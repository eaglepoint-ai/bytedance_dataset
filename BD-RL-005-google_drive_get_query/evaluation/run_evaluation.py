#!/usr/bin/env python3
"""
Evaluation runner that generates structured reports.

Run with:
    docker compose run --rm app python evaluation/run_evaluation.py [options]

Options:
    --users N           Number of users to seed (default: 21)
    --folders N         Number of folders to seed (default: 100)
    --files-per-folder N  Files per folder (default: 50)
    --iterations N      Iterations per test (default: 5)
    --output-dir DIR    Output directory (default: evaluation/)
"""
import os
import sys
import json
import uuid
import subprocess
import platform
from datetime import datetime
from pathlib import Path
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_git_commit():
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def get_git_branch():
    """Get current git branch."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def get_environment_info():
    """Collect environment information."""
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "docker_image": os.environ.get("DOCKER_IMAGE", "python:3.11-slim"),
        "git_commit": get_git_commit(),
        "git_branch": get_git_branch(),
        "database_url": os.environ.get("DATABASE_URL", "sqlite (in-memory)"),
    }


def run_performance_evaluation(params):
    """
    Run performance evaluation and collect metrics.
    
    Returns dict with metrics from both before and after implementations.
    """
    from repository_before.app import create_app as create_app_before
    from repository_after.app import create_app as create_app_after
    from repository_before import db as db_before
    from tests.utils import (
        clear_database,
        seed_heavy_user_data,
        measure_performance,
    )
    
    db_url = os.environ.get("DATABASE_URL", "sqlite:///evaluation_test.db")
    
    # Initialize before app
    before_app = create_app_before(db_url)
    before_app.config["TESTING"] = True
    
    # Seed data
    session = db_before.SessionLocal()
    try:
        clear_database(session)
        seed_stats = seed_heavy_user_data(
            session, 
            num_folders=params["folders"], 
            num_files_per_folder=params["files_per_folder"]
        )
    finally:
        session.close()
    
    # Initialize after app
    after_app = create_app_after(db_url)
    after_app.config["TESTING"] = True
    
    users_to_test = ["heavy_user", "other_user_0", "other_user_5", "other_user_10"]
    
    before_results = {}
    after_results = {}
    
    # Run measurements
    for user_id in users_to_test:
        with before_app.test_client() as client:
            before_results[user_id] = measure_performance(
                client, user_id, 
                num_iterations=params["iterations"]
            )
        
        with after_app.test_client() as client:
            after_results[user_id] = measure_performance(
                client, user_id, 
                num_iterations=params["iterations"]
            )
    
    # Cleanup
    session = db_before.SessionLocal()
    try:
        clear_database(session)
    finally:
        session.close()
    
    # Calculate aggregate metrics
    metrics = {
        "seed_stats": seed_stats,
        "before": {},
        "after": {},
        "comparison": {}
    }
    
    for user_id in users_to_test:
        b = before_results[user_id]
        a = after_results[user_id]
        
        metrics["before"][user_id] = {
            "avg_ms": b["avg_ms"],
            "min_ms": b["min_ms"],
            "max_ms": b["max_ms"],
            "folders": b["folders"],
            "files": b["files"],
        }
        
        metrics["after"][user_id] = {
            "avg_ms": a["avg_ms"],
            "min_ms": a["min_ms"],
            "max_ms": a["max_ms"],
            "folders": a["folders"],
            "files": a["files"],
        }
        
        speedup = b["avg_ms"] / a["avg_ms"] if a["avg_ms"] > 0 else 0
        improvement_pct = ((b["avg_ms"] - a["avg_ms"]) / b["avg_ms"]) * 100 if b["avg_ms"] > 0 else 0
        
        metrics["comparison"][user_id] = {
            "speedup": round(speedup, 2),
            "improvement_pct": round(improvement_pct, 1),
        }
    
    # Overall averages
    before_avg = sum(m["avg_ms"] for m in metrics["before"].values()) / len(users_to_test)
    after_avg = sum(m["avg_ms"] for m in metrics["after"].values()) / len(users_to_test)
    overall_speedup = before_avg / after_avg if after_avg > 0 else 0
    
    metrics["summary"] = {
        "before_avg_ms": round(before_avg, 2),
        "after_avg_ms": round(after_avg, 2),
        "overall_speedup": round(overall_speedup, 2),
        "overall_improvement_pct": round(((before_avg - after_avg) / before_avg) * 100 if before_avg > 0 else 0, 1),
    }
    
    return metrics


def generate_markdown_report(report_data):
    """Generate a human-readable markdown report."""
    env = report_data["environment"]
    params = report_data["parameters"]
    metrics = report_data["metrics"]
    
    db_url_display = env['database_url']
    if len(db_url_display) > 50:
        db_url_display = db_url_display[:50] + "..."
    
    md = f"""# Performance Evaluation Report

**Run ID:** `{report_data['run_id']}`  
**Started:** {report_data['started_at']}  
**Finished:** {report_data['finished_at']}  
**Duration:** {report_data['duration_seconds']:.2f} seconds

---

## Environment

| Property | Value |
|----------|-------|
| Python Version | {env['python_version']} |
| Platform | {env['platform']} |
| OS | {env['os']} {env['os_release']} |
| Architecture | {env['architecture']} |
| Docker Image | {env['docker_image']} |
| Git Commit | `{env['git_commit']}` |
| Git Branch | `{env['git_branch']}` |
| Database | {db_url_display} |

---

## Parameters

| Parameter | Value |
|-----------|-------|
| Users | {params['users']} |
| Folders | {params['folders']} |
| Files per Folder | {params['files_per_folder']} |
| Total Files | {params['folders'] * params['files_per_folder']} |
| Iterations | {params['iterations']} |

---

## Seed Statistics

| Entity | Count |
|--------|-------|
| Users | {metrics['seed_stats']['users']} |
| Folders | {metrics['seed_stats']['folders']} |
| Files | {metrics['seed_stats']['files']} |
| Permissions | {metrics['seed_stats']['permissions']} |

---

## Summary Results

| Metric | Before (Naive) | After (Optimized) | Improvement |
|--------|----------------|-------------------|-------------|
| Average Response | {metrics['summary']['before_avg_ms']:.2f} ms | {metrics['summary']['after_avg_ms']:.2f} ms | **{metrics['summary']['overall_speedup']:.2f}x faster** |
| Improvement | - | - | {metrics['summary']['overall_improvement_pct']:.1f}% |

---

## Detailed Results by User

| User | Before (ms) | After (ms) | Speedup | Folders | Files |
|------|-------------|------------|---------|---------|-------|
"""
    
    for user_id in metrics["before"]:
        b = metrics["before"][user_id]
        a = metrics["after"][user_id]
        c = metrics["comparison"][user_id]
        md += f"| {user_id} | {b['avg_ms']:.2f} | {a['avg_ms']:.2f} | {c['speedup']:.2f}x | {a['folders']} | {a['files']} |\n"
    
    md += """
---

## Conclusion

"""
    
    if metrics['summary']['overall_speedup'] >= 2.0:
        md += f"✅ **Excellent optimization!** The optimized implementation is **{metrics['summary']['overall_speedup']:.2f}x faster** than the naive version.\n"
    elif metrics['summary']['overall_speedup'] >= 1.0:
        md += f"✅ **Good optimization.** The optimized implementation is **{metrics['summary']['overall_speedup']:.2f}x faster** than the naive version.\n"
    else:
        md += f"⚠️ **Needs investigation.** The optimized implementation is slower than the naive version.\n"
    
    return md


def main():
    parser = argparse.ArgumentParser(description="Run performance evaluation with structured reports")
    parser.add_argument("--users", type=int, default=21, help="Number of users (default: 21)")
    parser.add_argument("--folders", type=int, default=100, help="Number of folders (default: 100)")
    parser.add_argument("--files-per-folder", type=int, default=50, help="Files per folder (default: 50)")
    parser.add_argument("--iterations", type=int, default=5, help="Test iterations (default: 5)")
    parser.add_argument("--output-dir", type=str, default="evaluation", help="Output directory (default: evaluation)")
    args = parser.parse_args()
    
    # Generate run ID and timestamps
    run_id = str(uuid.uuid4())[:8]
    started_at = datetime.now()
    
    # Create output directory with date and timestamp
    date_folder = started_at.strftime("%Y-%m-%d")
    timestamp = started_at.strftime("%H-%M-%S")
    output_path = Path(args.output_dir) / date_folder / timestamp
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"{'=' * 60}")
    print(f"PERFORMANCE EVALUATION")
    print(f"{'=' * 60}")
    print(f"Run ID: {run_id}")
    print(f"Started: {started_at.isoformat()}")
    print(f"Output: {output_path}")
    print(f"{'=' * 60}")
    
    parameters = {
        "users": args.users,
        "folders": args.folders,
        "files_per_folder": args.files_per_folder,
        "iterations": args.iterations,
    }
    
    print(f"\nParameters: {json.dumps(parameters, indent=2)}")
    print(f"\nRunning evaluation...")
    
    # Capture stdout for the log
    import io
    from contextlib import redirect_stdout
    
    stdout_capture = io.StringIO()
    
    with redirect_stdout(stdout_capture):
        print(f"Run ID: {run_id}")
        print(f"Started: {started_at.isoformat()}")
        print(f"Parameters: {json.dumps(parameters, indent=2)}")
        print()
        
        try:
            metrics = run_performance_evaluation(parameters)
            
            # Print results to captured stdout
            print(f"\n{'=' * 60}")
            print("EVALUATION RESULTS")
            print(f"{'=' * 60}")
            print(f"\nSeed Statistics: {json.dumps(metrics['seed_stats'], indent=2)}")
            print(f"\nSummary:")
            print(f"  Before (naive) avg:     {metrics['summary']['before_avg_ms']:.2f} ms")
            print(f"  After (optimized) avg:  {metrics['summary']['after_avg_ms']:.2f} ms")
            print(f"  Overall speedup:        {metrics['summary']['overall_speedup']:.2f}x")
            print(f"  Improvement:            {metrics['summary']['overall_improvement_pct']:.1f}%")
            print(f"\nDetailed Results:")
            for user_id in metrics['before']:
                b = metrics['before'][user_id]
                a = metrics['after'][user_id]
                c = metrics['comparison'][user_id]
                print(f"  {user_id}: {b['avg_ms']:.2f}ms -> {a['avg_ms']:.2f}ms ({c['speedup']:.2f}x)")
            
            success = True
            error_message = None
            
        except Exception as e:
            print(f"\nERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            metrics = None
            success = False
            error_message = str(e)
    
    finished_at = datetime.now()
    duration = (finished_at - started_at).total_seconds()
    
    # Build full report
    report_data = {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": duration,
        "success": success,
        "error": error_message,
        "parameters": parameters,
        "environment": get_environment_info(),
        "metrics": metrics,
    }
    
    # Write report.json
    json_path = output_path / "report.json"
    with open(json_path, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"\n✅ Saved: {json_path}")
    
    # Write report.md
    if success:
        md_path = output_path / "report.md"
        with open(md_path, "w") as f:
            f.write(generate_markdown_report(report_data))
        print(f"✅ Saved: {md_path}")
    
    # Write stdout.log
    log_path = output_path / "stdout.log"
    with open(log_path, "w") as f:
        f.write(stdout_capture.getvalue())
    print(f"✅ Saved: {log_path}")
    
    print(f"\n{'=' * 60}")
    print(f"EVALUATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Duration: {duration:.2f}s")
    print(f"Reports saved to: {output_path}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

