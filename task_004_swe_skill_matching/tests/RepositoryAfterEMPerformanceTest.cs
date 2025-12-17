extern alias repository_after;

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Xunit;
using EmployeeMatcher = repository_after::repository_after.EmployeeMatcher;
using ProjectRequirements = repository_after::repository_after.ProjectRequirements;
using TimeSlot = repository_after::repository_after.TimeSlot;
using Employee = repository_after::repository_after.Employee;

namespace tests;

[CollectionDefinition("EmployeeMatcherAfterEMPerformance", DisableParallelization = true)]
public sealed class EmployeeMatcherAfterEMPerformanceCollectionDefinition
{
}

[Collection("EmployeeMatcherAfterEMPerformance")]
public sealed class RepositoryAfterEMPerformanceTest : IAsyncLifetime
{
    private string _dbPath = string.Empty;

    public async Task InitializeAsync()
    {
        _dbPath = Path.Combine(Path.GetTempPath(), $"employee_matcher_after_{Guid.NewGuid():N}.sqlite");
        if (File.Exists(_dbPath))
        {
            File.Delete(_dbPath);
        }

        await using var context = new EmployeeMatcher.EmployeeDbContext(_dbPath, deleteDatabaseOnDispose: false);
        await context.EnsureCreatedAndSeededAsync();
    }

    public Task DisposeAsync()
    {
        try
        {
            if (File.Exists(_dbPath))
            {
                File.Delete(_dbPath);
            }
        }
        catch
        {
            // Ignore cleanup failures to keep tests resilient.
        }

        return Task.CompletedTask;
    }

    [Fact]
    public async Task RepositoryAfterEMPerformanceTest_FindBestEmployees_WarmRun_CompletesWithinBudget()
    {
        var requirements = BuildRequirements(requiredSkillsCount: 320, requiredTimeSlotsCount: 80);

        var median = await MeasureMedianAsync(
            iterations: 5,
            action: async () =>
            {
                await using var context = new EmployeeMatcher.EmployeeDbContext(_dbPath, deleteDatabaseOnDispose: false);
                var matcher = new EmployeeMatcher(context, threshold: 15);
                await matcher.FindBestEmployeesForProject(requirements);
            });

        var budget = TimeSpan.FromSeconds(5);
        Assert.True(
            median < budget,
            $"Warm run median {median.TotalMilliseconds:F0} ms exceeded budget {budget.TotalMilliseconds:F0} ms.");
    }

    [Fact]
    public async Task RepositoryAfterEMPerformanceTest_FindBestEmployees_Scaling_WithinBudget()
    {
        var small = BuildRequirements(requiredSkillsCount: 32, requiredTimeSlotsCount: 10);
        var large = BuildRequirements(requiredSkillsCount: 3200, requiredTimeSlotsCount: 80);

        var smallMedian = await MeasureMedianAsync(
            iterations: 3,
            action: async () =>
            {
                await using var context = new EmployeeMatcher.EmployeeDbContext(_dbPath, deleteDatabaseOnDispose: false);
                var matcher = new EmployeeMatcher(context, threshold: 15);
                await matcher.FindBestEmployeesForProject(small);
            });

        var largeMedian = await MeasureMedianAsync(
            iterations: 5,
            action: async () =>
            {
                await using var context = new EmployeeMatcher.EmployeeDbContext(_dbPath, deleteDatabaseOnDispose: false);
                var matcher = new EmployeeMatcher(context, threshold: 15);
                await matcher.FindBestEmployeesForProject(large);
            });

        var smallMs = Math.Max(1.0, smallMedian.TotalMilliseconds);
        var largeMs = largeMedian.TotalMilliseconds;
        var ratio = largeMs / smallMs;

        Assert.True(
            ratio <= 2,
            $"Scaling too steep. Small median {smallMedian.TotalMilliseconds:F0} ms, " +
            $"large median {largeMedian.TotalMilliseconds:F0} ms, ratio {ratio:F1}x.");
    }

    [Fact]
    public async Task RepositoryAfterEMPerformanceTest_FindBestEmployees_Allocations_StayWithinBudget_WhenManyMatches()
    {
        var requirements = BuildRequirements(requiredSkillsCount: 320, requiredTimeSlotsCount: 10);

        await using (var warmContext = new EmployeeMatcher.EmployeeDbContext(_dbPath, deleteDatabaseOnDispose: false))
        {
            var warmMatcher = new EmployeeMatcher(warmContext, threshold: 0);
            await warmMatcher.FindBestEmployeesForProject(requirements);
        }

        GC.Collect();
        GC.WaitForPendingFinalizers();
        GC.Collect();

        var gen0Before = GC.CollectionCount(0);
        var allocatedBefore = GC.GetTotalAllocatedBytes(precise: true);

        TimeSpan elapsed;
        await using (var context = new EmployeeMatcher.EmployeeDbContext(_dbPath, deleteDatabaseOnDispose: false))
        {
            var matcher = new EmployeeMatcher(context, threshold: 0);
            var sw = Stopwatch.StartNew();
            await matcher.FindBestEmployeesForProject(requirements);
            sw.Stop();
            elapsed = sw.Elapsed;
        }

        var allocatedAfter = GC.GetTotalAllocatedBytes(precise: true);
        var gen0After = GC.CollectionCount(0);

        var allocatedBytes = allocatedAfter - allocatedBefore;
        var allocatedMb = allocatedBytes / (1024.0 * 1024.0);

        const long allocationBudgetBytes = 30L * 1024L * 1024L;
        Assert.True(
            allocatedBytes < allocationBudgetBytes,
            $"Allocated {allocatedMb:F1} MB in {elapsed.TotalMilliseconds:F0} ms, exceeds 30.0 MB budget.");

    }

    private static ProjectRequirements BuildBroadRequirements()
    {
        var requirements = new ProjectRequirements();
        requirements.RequiredSkills.AddRange(new[]
        {
            "C#", "Java", "Python", "SQL", "JavaScript", "React", "Azure", "AWS"
        });

        var baseStart = DateTime.Today.AddHours(9);
        requirements.TimeSlots.AddRange(Enumerable.Range(0, 5).Select(i =>
        {
            var start = baseStart.AddDays(i).AddHours(i);
            return new TimeSlot { Start = start, End = start.AddHours(2) };
        }));

        return requirements;
    }

    private static ProjectRequirements BuildRequirements(int requiredSkillsCount, int requiredTimeSlotsCount)
    {
        var skillPool = new[]
        {
            "C#", "Java", "Python", "SQL", "JavaScript", "React", "Angular", "Azure",
            "AWS", "GCP", "Kubernetes", "Docker", "Go", "Rust", "Project Management", "QA Automation"
        };

        var requirements = new ProjectRequirements();
        for (int i = 0; i < requiredSkillsCount; i++)
        {
            requirements.RequiredSkills.Add(skillPool[i % skillPool.Length]);
        }

        var baseStart = DateTime.Today.AddHours(9);
        for (int i = 0; i < requiredTimeSlotsCount; i++)
        {
            var start = baseStart
                .AddDays(i % 14)
                .AddHours((i % 4) * 2);

            requirements.TimeSlots.Add(new TimeSlot
            {
                Start = start,
                End = start.AddHours(2)
            });
        }

        return requirements;
    }

    private static async Task<TimeSpan> MeasureMedianAsync(int iterations, Func<Task> action)
    {
        await action(); // warmup

        var samples = new List<long>(iterations);
        for (int i = 0; i < iterations; i++)
        {
            var sw = Stopwatch.StartNew();
            await action();
            sw.Stop();
            samples.Add(sw.ElapsedTicks);
        }

        samples.Sort();
        var medianTicks = samples[samples.Count / 2];
        return TimeSpan.FromTicks(medianTicks);
    }

    private async Task<Employee> GetDeterministicEmployeeAsync()
    {
        await using var context = new EmployeeMatcher.EmployeeDbContext(_dbPath, deleteDatabaseOnDispose: false);
        var employees = await context.GetAllEmployeesAsync();
        return employees.First();
    }
}
