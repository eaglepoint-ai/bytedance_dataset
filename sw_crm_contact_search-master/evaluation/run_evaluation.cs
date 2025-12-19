extern alias repository_after;

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using RepoBefore = repository_before;
using RepoAfter = repository_after::repository_before;

internal static class Program
{
    public static async Task<int> Main(string[] args)
    {
        var options = EvalOptions.Parse(args);
        var runId = Guid.NewGuid().ToString("N")[..8];
        var startedAt = DateTime.Now;

        var outputPath = Path.Combine(options.OutputDir, startedAt.ToString("yyyy-MM-dd"), startedAt.ToString("HH-mm-ss"));
        Directory.CreateDirectory(outputPath);

        var originalOut = Console.Out;
        using var teeWriter = new TeeTextWriter(originalOut);
        Console.SetOut(teeWriter);

        Console.WriteLine(new string('=', 60));
        Console.WriteLine("PERFORMANCE EVALUATION (.NET)");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine($"Run ID: {runId}");
        Console.WriteLine($"Started: {startedAt:O}");
        Console.WriteLine($"Output: {outputPath}");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine("\nParameters:");
        Console.WriteLine(options.ToJson());
        Console.WriteLine("\nRunning evaluation...");

        EvaluationMetrics? metrics = null;
        string? error = null;
        bool success;

        try
        {
            metrics = await RunPerformanceEvaluation(options, outputPath);
            success = true;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"\nERROR: {ex.Message}");
            Console.Error.WriteLine(ex);
            error = ex.ToString();
            success = false;
        }
        finally
        {
            Console.Out.Flush();
            Console.SetOut(originalOut);
        }

        var finishedAt = DateTime.Now;
        var durationSeconds = (finishedAt - startedAt).TotalSeconds;

        var reportData = new ReportData
        {
            RunId = runId,
            StartedAt = startedAt,
            FinishedAt = finishedAt,
            DurationSeconds = durationSeconds,
            Success = success,
            Error = error,
            Parameters = options.ToParameters(),
            Environment = EnvironmentInfo.Create(),
            Metrics = metrics
        };

        var jsonOptions = new JsonSerializerOptions
        {
            WriteIndented = true,
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase
        };

        var jsonPath = Path.Combine(outputPath, "report.json");
        File.WriteAllText(jsonPath, JsonSerializer.Serialize(reportData, jsonOptions));
        Console.WriteLine($"\n✅ Saved: {jsonPath}");

        if (success && metrics is not null)
        {
            var mdPath = Path.Combine(outputPath, "report.md");
            File.WriteAllText(mdPath, GenerateMarkdownReport(reportData));
            Console.WriteLine($"✅ Saved: {mdPath}");
        }

        var logPath = Path.Combine(outputPath, "stdout.log");
        var logContent = teeWriter.CapturedText + (error is not null ? $"\nERROR:\n{error}" : string.Empty);
        File.WriteAllText(logPath, logContent);
        Console.WriteLine($"✅ Saved: {logPath}");

        Console.WriteLine("\n" + new string('=', 60));
        Console.WriteLine("EVALUATION COMPLETE");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine($"Duration: {durationSeconds:F2}s");
        Console.WriteLine($"Reports saved to: {outputPath}");

        return success ? 0 : 1;
    }

    private static async Task<EvaluationMetrics> RunPerformanceEvaluation(EvalOptions options, string outputPath)
    {
        var beforeDbPath = Path.Combine(outputPath, "crm_contacts_before.sqlite");
        var afterDbPath = Path.Combine(outputPath, "crm_contacts_after.sqlite");

        EvaluationMetrics metrics;

        await using (var beforeContext = new RepoBefore.CrmContactSearch.CrmDbContext(beforeDbPath, deleteDatabaseOnDispose: false))
        await using (var afterContext = new RepoAfter.CrmContactSearch.CrmDbContext(afterDbPath))
        {
            await beforeContext.EnsureCreatedAndSeededAsync();
            await afterContext.EnsureCreatedAndSeededAsync();

            var seedStats = await BuildSeedStats(beforeContext, afterContext);
            var scenarios = BuildScenarios(options);

            var beforeSearcher = new RepoBefore.CrmContactSearch.ContactSearcher(beforeContext);
            var afterSearcher = new RepoAfter.CrmContactSearch.ContactSearcher(afterContext);

            metrics = new EvaluationMetrics
            {
                SeedStats = seedStats
            };

            foreach (var scenario in scenarios)
            {
                var scenarioMetrics = await MeasureScenarioAsync(scenario, beforeSearcher, afterSearcher, options.Iterations);
                metrics.Before[scenario.Name] = scenarioMetrics.Before;
                metrics.After[scenario.Name] = scenarioMetrics.After;
                metrics.Comparison[scenario.Name] = scenarioMetrics.Comparison;

                Console.WriteLine($"\nScenario: {scenario.Name} ({scenario.Description})");
                Console.WriteLine($"  Before: {scenarioMetrics.Before.AvgMs:F2} ms avg " +
                                  $"(min {scenarioMetrics.Before.MinMs:F2}, max {scenarioMetrics.Before.MaxMs:F2})");
                Console.WriteLine($"  After : {scenarioMetrics.After.AvgMs:F2} ms avg " +
                                  $"(min {scenarioMetrics.After.MinMs:F2}, max {scenarioMetrics.After.MaxMs:F2})");
                Console.WriteLine($"  Speedup: {scenarioMetrics.Comparison.Speedup:F2}x");
            }

            metrics.Summary = BuildSummary(metrics);
        }

        CleanupDatabaseArtifacts(beforeDbPath);
        CleanupDatabaseArtifacts(afterDbPath);

        return metrics;
    }

    private static List<QueryScenario> BuildScenarios(EvalOptions options)
    {
        var pageSize = Math.Clamp(options.FilesPerFolder, 1, 200);

        return new List<QueryScenario>
        {
            new(
                "baseline",
                "Unfiltered search with minimum deal value",
                new RequestSpec(null, null, null, Stage.Qualified, 10_000m, 1, pageSize)
            ),
            new(
                "city_and_stage",
                "City + deal stage filter",
                new RequestSpec("London", null, null, Stage.Negotiation, 20_000m, 1, pageSize)
            ),
            new(
                "tags_and_value",
                "Tag filter plus higher deal value",
                new RequestSpec(null, "VIP,Premium", null, null, 50_000m, 1, pageSize)
            ),
            new(
                "stale_contacts_page_2",
                "Older contacts on page 2 with light floor",
                new RequestSpec(null, null, DateTime.UtcNow.AddDays(-120), Stage.Prospect, 5_000m, 2, pageSize)
            )
        };
    }

    private static async Task<ScenarioMetrics> MeasureScenarioAsync(
        QueryScenario scenario,
        RepoBefore.CrmContactSearch.ContactSearcher beforeSearcher,
        RepoAfter.CrmContactSearch.ContactSearcher afterSearcher,
        int iterations)
    {
        var beforeTimings = new List<double>(iterations);
        var afterTimings = new List<double>(iterations);
        SearchSnapshot? beforeSnapshot = null;
        SearchSnapshot? afterSnapshot = null;

        for (var i = 0; i < iterations; i++)
        {
            var result = await beforeSearcher.SearchContacts(ToBeforeRequest(scenario.Request));
            beforeTimings.Add(result.ElapsedMilliseconds);
            beforeSnapshot = new SearchSnapshot(result.TotalCount, result.Data.Count, result.Page, result.PageSize);
        }

        for (var i = 0; i < iterations; i++)
        {
            var result = await afterSearcher.SearchContacts(ToAfterRequest(scenario.Request));
            afterTimings.Add(result.ElapsedMilliseconds);
            afterSnapshot = new SearchSnapshot(result.TotalCount, result.Data.Count, result.Page, result.PageSize);
        }

        var beforeStats = TimingStats.From(beforeTimings, beforeSnapshot);
        var afterStats = TimingStats.From(afterTimings, afterSnapshot);
        var comparison = ComparisonStats.From(beforeStats.AvgMs, afterStats.AvgMs);

        return new ScenarioMetrics(scenario.Name, scenario.Description, beforeStats, afterStats, comparison);
    }

    private static RepoBefore.CrmContactSearch.ContactSearchRequest ToBeforeRequest(RequestSpec request)
    {
        return new RepoBefore.CrmContactSearch.ContactSearchRequest
        {
            City = request.City,
            Tags = request.Tags,
            LastContactBefore = request.LastContactBefore,
            DealStage = request.DealStage is null ? null : (RepoBefore.CrmContactSearch.DealStage?)request.DealStage,
            MinDealValue = request.MinDealValue,
            Page = request.Page,
            PageSize = request.PageSize
        };
    }

    private static RepoAfter.CrmContactSearch.ContactSearchRequest ToAfterRequest(RequestSpec request)
    {
        return new RepoAfter.CrmContactSearch.ContactSearchRequest
        {
            City = request.City,
            Tags = request.Tags,
            LastContactBefore = request.LastContactBefore,
            DealStage = request.DealStage is null ? null : (RepoAfter.CrmContactSearch.DealStage?)request.DealStage,
            MinDealValue = request.MinDealValue,
            Page = request.Page,
            PageSize = request.PageSize
        };
    }

    private static SummaryMetrics BuildSummary(EvaluationMetrics metrics)
    {
        double beforeAvg = metrics.Before.Count == 0 ? 0 : metrics.Before.Values.Average(m => m.AvgMs);
        double afterAvg = metrics.After.Count == 0 ? 0 : metrics.After.Values.Average(m => m.AvgMs);
        double overallSpeedup = afterAvg > 0 ? beforeAvg / afterAvg : 0;

        return new SummaryMetrics
        {
            BeforeAvgMs = Math.Round(beforeAvg, 2),
            AfterAvgMs = Math.Round(afterAvg, 2),
            OverallSpeedup = Math.Round(overallSpeedup, 2),
            OverallImprovementPct = beforeAvg > 0
                ? Math.Round(((beforeAvg - afterAvg) / beforeAvg) * 100, 1)
                : 0
        };
    }

    private static async Task<SeedStats> BuildSeedStats(
        RepoBefore.CrmContactSearch.CrmDbContext beforeContext,
        RepoAfter.CrmContactSearch.CrmDbContext afterContext)
    {
        return new SeedStats
        {
            Contacts = await beforeContext.Contacts.CountAsync(),
            Tags = await beforeContext.Tags.CountAsync(),
            Interactions = await beforeContext.Interactions.CountAsync(),
            Deals = await beforeContext.Deals.CountAsync(),
            CachedMetrics = await afterContext.ContactMetrics.CountAsync()
        };
    }

    private static void CleanupDatabaseArtifacts(string databasePath)
    {
        DeleteIfExists(databasePath);
        DeleteIfExists(databasePath + "-wal");
        DeleteIfExists(databasePath + "-shm");
    }

    private static void DeleteIfExists(string path)
    {
        if (!File.Exists(path))
        {
            return;
        }

        try
        {
            File.Delete(path);
        }
        catch (IOException)
        {
            // Best-effort cleanup only
        }
        catch (UnauthorizedAccessException)
        {
            // Best-effort cleanup only
        }
    }

    private static string GenerateMarkdownReport(ReportData report)
    {
        if (report.Metrics is null)
        {
            return "# Performance Evaluation Report\n\nRun did not complete.";
        }

        var env = report.Environment;
        var metrics = report.Metrics;
        var parameters = report.Parameters;

        var sb = new StringBuilder();
        sb.AppendLine("# Performance Evaluation Report");
        sb.AppendLine();
        sb.AppendLine($"**Run ID:** `{report.RunId}`  ");
        sb.AppendLine($"**Started:** {report.StartedAt:O}  ");
        sb.AppendLine($"**Finished:** {report.FinishedAt:O}  ");
        sb.AppendLine($"**Duration:** {report.DurationSeconds:F2} seconds");
        sb.AppendLine("\n---\n");

        sb.AppendLine("## Environment\n");
        sb.AppendLine("| Property | Value |");
        sb.AppendLine("|----------|-------|");
        sb.AppendLine($"| .NET | {env.DotNetVersion} |");
        sb.AppendLine($"| Runtime | {env.FrameworkDescription} |");
        sb.AppendLine($"| OS | {env.OsDescription} |");
        sb.AppendLine($"| Architecture | {env.Architecture} |");
        sb.AppendLine($"| Processors | {env.ProcessorCount} |");
        sb.AppendLine($"| Git Commit | `{env.GitCommit}` |");
        sb.AppendLine($"| Git Branch | `{env.GitBranch}` |");
        sb.AppendLine("\n---\n");

        sb.AppendLine("## Parameters\n");
        sb.AppendLine("| Parameter | Value |");
        sb.AppendLine("|-----------|-------|");
        sb.AppendLine($"| Users | {parameters.Users} |");
        sb.AppendLine($"| Folders | {parameters.Folders} |");
        sb.AppendLine($"| Files per Folder | {parameters.FilesPerFolder} |");
        sb.AppendLine($"| Iterations | {parameters.Iterations} |");
        sb.AppendLine("\n---\n");

        sb.AppendLine("## Seed Statistics\n");
        sb.AppendLine("| Contacts | Tags | Interactions | Deals | Cached Metrics |");
        sb.AppendLine("|----------|------|--------------|-------|----------------|");
        sb.AppendLine($"| {metrics.SeedStats.Contacts} | {metrics.SeedStats.Tags} | {metrics.SeedStats.Interactions} | {metrics.SeedStats.Deals} | {metrics.SeedStats.CachedMetrics} |");
        sb.AppendLine("\n---\n");

        sb.AppendLine("## Summary Results\n");
        sb.AppendLine("| Metric | Before (Naive) | After (Optimized) | Improvement |");
        sb.AppendLine("|--------|----------------|-------------------|-------------|");
        sb.AppendLine($"| Average Response | {metrics.Summary.BeforeAvgMs:F2} ms | {metrics.Summary.AfterAvgMs:F2} ms | **{metrics.Summary.OverallSpeedup:F2}x faster** |");
        sb.AppendLine($"| Improvement | - | - | {metrics.Summary.OverallImprovementPct:F1}% |");
        sb.AppendLine("\n---\n");

        sb.AppendLine("## Detailed Results by Scenario\n");
        sb.AppendLine("| Scenario | Before (ms) | After (ms) | Speedup | Returned | Total |");
        sb.AppendLine("|----------|-------------|------------|---------|----------|-------|");

        foreach (var scenario in metrics.Before.Keys)
        {
            var b = metrics.Before[scenario];
            var a = metrics.After[scenario];
            var c = metrics.Comparison[scenario];
            sb.AppendLine($"| {scenario} | {b.AvgMs:F2} | {a.AvgMs:F2} | {c.Speedup:F2}x | {a.Returned} | {a.Total} |");
        }

        sb.AppendLine("\n---\n");
        sb.AppendLine("## Conclusion\n");

        if (metrics.Summary.OverallSpeedup >= 2.0)
        {
            sb.AppendLine($"✅ **Excellent optimization.** The optimized implementation is **{metrics.Summary.OverallSpeedup:F2}x faster** than the naive version.");
        }
        else if (metrics.Summary.OverallSpeedup >= 1.0)
        {
            sb.AppendLine($"✅ **Good optimization.** The optimized implementation is **{metrics.Summary.OverallSpeedup:F2}x faster** than the naive version.");
        }
        else
        {
            sb.AppendLine("⚠️ **Needs investigation.** The optimized implementation is slower than the naive version.");
        }

        return sb.ToString();
    }
}

internal sealed record EvalOptions
{
    public int Users { get; init; } = 21;
    public int Folders { get; init; } = 100;
    public int FilesPerFolder { get; init; } = 50;
    public int Iterations { get; init; } = 5;
    public string OutputDir { get; init; } = "evaluation";

    public static EvalOptions Parse(string[] args)
    {
        var options = new EvalOptions();

        for (var i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "--users" when i + 1 < args.Length && int.TryParse(args[i + 1], out var users):
                    options = options with { Users = users };
                    i++;
                    break;
                case "--folders" when i + 1 < args.Length && int.TryParse(args[i + 1], out var folders):
                    options = options with { Folders = folders };
                    i++;
                    break;
                case "--files-per-folder" when i + 1 < args.Length && int.TryParse(args[i + 1], out var fpf):
                    options = options with { FilesPerFolder = fpf };
                    i++;
                    break;
                case "--iterations" when i + 1 < args.Length && int.TryParse(args[i + 1], out var iterations):
                    options = options with { Iterations = iterations };
                    i++;
                    break;
                case "--output-dir" when i + 1 < args.Length:
                    options = options with { OutputDir = args[i + 1] };
                    i++;
                    break;
            }
        }

        return options;
    }

    public string ToJson()
    {
        var opts = new JsonSerializerOptions { WriteIndented = true };
        return JsonSerializer.Serialize(ToParameters(), opts);
    }

    public EvalParameters ToParameters() =>
        new()
        {
            Users = Users,
            Folders = Folders,
            FilesPerFolder = FilesPerFolder,
            Iterations = Iterations
        };
}

internal sealed class EvalParameters
{
    public int Users { get; init; }
    public int Folders { get; init; }
    public int FilesPerFolder { get; init; }
    public int Iterations { get; init; }
}

internal sealed class EnvironmentInfo
{
    public string DotNetVersion { get; init; } = string.Empty;
    public string FrameworkDescription { get; init; } = string.Empty;
    public string OsDescription { get; init; } = string.Empty;
    public string Architecture { get; init; } = string.Empty;
    public int ProcessorCount { get; init; }
    public string GitCommit { get; init; } = "unknown";
    public string GitBranch { get; init; } = "unknown";

    public static EnvironmentInfo Create()
    {
        return new EnvironmentInfo
        {
            DotNetVersion = Environment.Version.ToString(),
            FrameworkDescription = RuntimeInformation.FrameworkDescription,
            OsDescription = RuntimeInformation.OSDescription,
            Architecture = RuntimeInformation.OSArchitecture.ToString(),
            ProcessorCount = Environment.ProcessorCount,
            GitCommit = TryGit("rev-parse --short HEAD"),
            GitBranch = TryGit("rev-parse --abbrev-ref HEAD")
        };
    }

    private static string TryGit(string arguments)
    {
        try
        {
            var psi = new ProcessStartInfo("git", arguments)
            {
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            using var process = Process.Start(psi);
            if (process is null)
            {
                return "unknown";
            }

            var output = process.StandardOutput.ReadToEnd().Trim();
            process.WaitForExit(3000);
            return process.ExitCode == 0 ? output : "unknown";
        }
        catch
        {
            return "unknown";
        }
    }
}

internal sealed class ReportData
{
    public string RunId { get; init; } = string.Empty;
    public DateTime StartedAt { get; init; }
    public DateTime FinishedAt { get; init; }
    public double DurationSeconds { get; init; }
    public bool Success { get; init; }
    public string? Error { get; init; }
    public EvalParameters Parameters { get; init; } = new();
    public EnvironmentInfo Environment { get; init; } = new();
    public EvaluationMetrics? Metrics { get; init; }
}

internal sealed class SeedStats
{
    public int Contacts { get; init; }
    public int Tags { get; init; }
    public int Interactions { get; init; }
    public int Deals { get; init; }
    public int CachedMetrics { get; init; }
}

internal sealed class TimingStats
{
    public double AvgMs { get; init; }
    public double MinMs { get; init; }
    public double MaxMs { get; init; }
    public int Total { get; init; }
    public int Returned { get; init; }
    public int Page { get; init; }
    public int PageSize { get; init; }

    public static TimingStats From(IReadOnlyCollection<double> timings, SearchSnapshot? snapshot)
    {
        if (timings.Count == 0)
        {
            return new TimingStats();
        }

        return new TimingStats
        {
            AvgMs = Math.Round(timings.Average(), 2),
            MinMs = Math.Round(timings.Min(), 2),
            MaxMs = Math.Round(timings.Max(), 2),
            Total = snapshot?.Total ?? 0,
            Returned = snapshot?.Returned ?? 0,
            Page = snapshot?.Page ?? 0,
            PageSize = snapshot?.PageSize ?? 0
        };
    }
}

internal sealed class ComparisonStats
{
    public double Speedup { get; init; }
    public double ImprovementPct { get; init; }

    public static ComparisonStats From(double beforeAvg, double afterAvg)
    {
        var speedup = afterAvg > 0 ? beforeAvg / afterAvg : 0;
        var improvement = beforeAvg > 0
            ? ((beforeAvg - afterAvg) / beforeAvg) * 100
            : 0;

        return new ComparisonStats
        {
            Speedup = Math.Round(speedup, 2),
            ImprovementPct = Math.Round(improvement, 1)
        };
    }
}

internal sealed class SummaryMetrics
{
    public double BeforeAvgMs { get; init; }
    public double AfterAvgMs { get; init; }
    public double OverallSpeedup { get; init; }
    public double OverallImprovementPct { get; init; }
}

internal sealed class EvaluationMetrics
{
    public SeedStats SeedStats { get; init; } = new();
    public Dictionary<string, TimingStats> Before { get; } = new(StringComparer.OrdinalIgnoreCase);
    public Dictionary<string, TimingStats> After { get; } = new(StringComparer.OrdinalIgnoreCase);
    public Dictionary<string, ComparisonStats> Comparison { get; } = new(StringComparer.OrdinalIgnoreCase);
    public SummaryMetrics Summary { get; set; } = new();
}

internal sealed record QueryScenario(string Name, string Description, RequestSpec Request);

internal sealed record RequestSpec(
    string? City,
    string? Tags,
    DateTime? LastContactBefore,
    Stage? DealStage,
    decimal? MinDealValue,
    int Page,
    int PageSize
);

internal sealed record ScenarioMetrics(
    string Name,
    string Description,
    TimingStats Before,
    TimingStats After,
    ComparisonStats Comparison
);

internal sealed record SearchSnapshot(int Total, int Returned, int Page, int PageSize);

internal enum Stage
{
    Prospect = 0,
    Qualified = 1,
    Proposal = 2,
    Negotiation = 3,
    ClosedWon = 4,
    ClosedLost = 5
}

internal sealed class TeeTextWriter : TextWriter
{
    private readonly TextWriter _inner;
    private readonly StringBuilder _buffer = new();

    public TeeTextWriter(TextWriter inner)
    {
        _inner = inner;
    }

    public string CapturedText => _buffer.ToString();

    public override Encoding Encoding => _inner.Encoding;

    public override void Write(char value)
    {
        _inner.Write(value);
        _buffer.Append(value);
    }

    public override void Write(string? value)
    {
        _inner.Write(value);
        _buffer.Append(value);
    }

    public override void WriteLine(string? value)
    {
        _inner.WriteLine(value);
        _buffer.AppendLine(value);
    }
}
