#!/usr/bin/env python3
"""
Comprehensive evaluation runner for the normalize_id refactoring project.

Runs all tests and metrics, then generates a structured report.json file
in a date/time directory structure: evaluation/reports/YYYY-MM-DD/HH-MM-SS/report.json
"""
import json
import os
import platform
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


def get_git_info() -> dict:
    """Get git commit and branch information."""
    git_info = {"git_commit": "unknown", "git_branch": "unknown"}
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            git_info["git_commit"] = result.stdout.strip()
        
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            git_info["git_branch"] = result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return git_info


def get_environment_info() -> dict:
    """Collect environment information."""
    env_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "docker_image": os.environ.get("DOCKER_IMAGE", "python:3.11-slim"),
    }
    env_info.update(get_git_info())
    return env_info


def run_pytest(pythonpath: str, test_dir: str = "tests/") -> dict:
    """Run pytest and capture results."""
    env = os.environ.copy()
    env["PYTHONPATH"] = pythonpath
    
    result = subprocess.run(
        ["pytest", "-v", "--tb=short", "-q", test_dir],
        capture_output=True, text=True, env=env
    )
    
    # Parse pytest output for stats
    output = result.stdout + result.stderr
    passed = failed = errors = warnings = 0
    
    # Look for the summary line like "10 failed, 35 passed in 0.05s" or "45 passed in 0.03s"
    # Patterns: "X passed", "X failed", "X error", "X errors", "X warning", "X warnings"
    for line in output.split("\n"):
        # Match patterns like "10 failed" or "35 passed" with optional comma/space
        passed_match = re.search(r'(\d+)\s+passed', line)
        failed_match = re.search(r'(\d+)\s+failed', line)
        error_match = re.search(r'(\d+)\s+errors?', line)
        warning_match = re.search(r'(\d+)\s+warnings?', line)
        
        if passed_match:
            passed = int(passed_match.group(1))
        if failed_match:
            failed = int(failed_match.group(1))
        if error_match:
            errors = int(error_match.group(1))
        if warning_match:
            warnings = int(warning_match.group(1))
    
    return {
        "success": result.returncode == 0,
        "return_code": result.returncode,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "warnings": warnings,
        "output": output[-2000:] if len(output) > 2000 else output  # Truncate long outputs
    }


def run_pylint(file_path: str) -> dict:
    """Run pylint on a file and extract score."""
    result = subprocess.run(
        ["pylint", file_path, "--output-format=text"],
        capture_output=True, text=True
    )
    
    output = result.stdout + result.stderr
    score = None
    
    # Extract score from "Your code has been rated at X.XX/10"
    for line in output.split("\n"):
        if "rated at" in line:
            try:
                score_str = line.split("rated at")[1].split("/")[0].strip()
                score = float(score_str)
            except (ValueError, IndexError):
                pass
    
    return {
        "score": score,
        "return_code": result.returncode,
        "raw_output": output[-1000:] if len(output) > 1000 else output
    }


def run_performance_benchmark() -> dict:
    """Run performance benchmarks on both versions."""
    benchmarks = {}
    
    for version in ["before", "after"]:
        pythonpath = f"/app/repository_{version}"
        
        # Create a simple benchmark script
        benchmark_code = '''
import sys
import time
sys.path.insert(0, "{pythonpath}")
from ids import normalize_id

test_cases = [
    "ABC_123",
    " Abc 123 ",
    "temp_user_1",
    " TEMP__a b!!c ",
    "!!!abc!!!",
    "temp_" + "_".join([f"segment{{i}}" for i in range(20)]),
]

iterations = 1000
times = []

for _ in range(10):  # 10 runs for averaging
    start = time.perf_counter()
    for _ in range(iterations):
        for tc in test_cases:
            normalize_id(tc)
    duration = time.perf_counter() - start
    times.append(duration)

avg_ms = (sum(times) / len(times)) * 1000
min_ms = min(times) * 1000
max_ms = max(times) * 1000
per_call_us = (sum(times) / len(times) / (iterations * len(test_cases))) * 1_000_000

print(f"{{avg_ms:.4f}},{{min_ms:.4f}},{{max_ms:.4f}},{{per_call_us:.4f}}")
'''.format(pythonpath=pythonpath)
        
        result = subprocess.run(
            ["python", "-c", benchmark_code],
            capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": pythonpath}
        )
        
        try:
            parts = result.stdout.strip().split(",")
            benchmarks[version] = {
                "avg_ms": float(parts[0]),
                "min_ms": float(parts[1]),
                "max_ms": float(parts[2]),
                "per_call_us": float(parts[3]),
                "iterations": 1000,
                "test_cases": 6,
                "runs": 10
            }
        except (ValueError, IndexError):
            benchmarks[version] = {
                "error": result.stderr or "Failed to parse benchmark output",
                "stdout": result.stdout
            }
    
    # Calculate comparison
    if "avg_ms" in benchmarks.get("before", {}) and "avg_ms" in benchmarks.get("after", {}):
        before_avg = benchmarks["before"]["avg_ms"]
        after_avg = benchmarks["after"]["avg_ms"]
        
        if after_avg > 0:
            speedup = before_avg / after_avg
            improvement_pct = ((before_avg - after_avg) / before_avg) * 100
        else:
            speedup = float('inf')
            improvement_pct = 100.0
        
        benchmarks["comparison"] = {
            "speedup": round(speedup, 2),
            "improvement_pct": round(improvement_pct, 1)
        }
    
    return benchmarks


def create_report_directory() -> Path:
    """Create directory structure for report: evaluation/reports/YYYY-MM-DD/HH-MM-SS/"""
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")
    
    report_dir = Path("evaluation/reports") / date_str / time_str
    report_dir.mkdir(parents=True, exist_ok=True)
    
    return report_dir


def main() -> int:
    """Run all evaluations and generate report."""
    print("=" * 70)
    print("NORMALIZE_ID REFACTORING EVALUATION")
    print("=" * 70)
    
    run_id = uuid.uuid4().hex[:8]
    started_at = datetime.now()
    error = None
    success = True
    
    report: dict[str, Any] = {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": None,
        "duration_seconds": None,
        "success": None,
        "error": None,
        "environment": get_environment_info(),
        "metrics": {}
    }
    
    try:
        # Run tests for before version
        print("\n[1/6] Running tests on repository_before...")
        tests_before = run_pytest("/app/repository_before")
        report["metrics"]["tests_before"] = tests_before
        print(f"      Result: {'PASS' if tests_before['success'] else 'FAIL'} "
              f"(passed={tests_before['passed']}, failed={tests_before['failed']})")
        
        # Run tests for after version
        print("\n[2/6] Running tests on repository_after...")
        tests_after = run_pytest("/app/repository_after")
        report["metrics"]["tests_after"] = tests_after
        print(f"      Result: {'PASS' if tests_after['success'] else 'FAIL'} "
              f"(passed={tests_after['passed']}, failed={tests_after['failed']})")
        
        # Run pylint on before version
        print("\n[3/6] Running pylint on repository_before/ids.py...")
        pylint_before = run_pylint("repository_before/ids.py")
        report["metrics"]["pylint_before"] = pylint_before
        print(f"      Score: {pylint_before.get('score', 'N/A')}/10")
        
        # Run pylint on after version
        print("\n[4/6] Running pylint on repository_after/ids.py...")
        pylint_after = run_pylint("repository_after/ids.py")
        report["metrics"]["pylint_after"] = pylint_after
        print(f"      Score: {pylint_after.get('score', 'N/A')}/10")
        
        # Calculate pylint comparison
        if pylint_before.get("score") and pylint_after.get("score"):
            before_score = pylint_before["score"]
            after_score = pylint_after["score"]
            improvement = after_score - before_score
            report["metrics"]["pylint_comparison"] = {
                "before": before_score,
                "after": after_score,
                "improvement": round(improvement, 2),
                "improvement_pct": round((improvement / before_score) * 100, 1) if before_score else 0
            }
        
        # Run radon complexity analysis
        print("\n[5/6] Running radon complexity analysis...")
        radon_before = run_radon("repository_before/ids.py")
        radon_after = run_radon("repository_after/ids.py")
        report["metrics"]["radon_before"] = radon_before
        report["metrics"]["radon_after"] = radon_after
        print(f"      Before: total_complexity={radon_before.get('total_complexity', 'N/A')}, "
              f"functions={radon_before.get('function_count', 'N/A')}")
        print(f"      After:  total_complexity={radon_after.get('total_complexity', 'N/A')}, "
              f"functions={radon_after.get('function_count', 'N/A')}")
        
        # Run performance benchmarks
        print("\n[6/6] Running performance benchmarks...")
        benchmarks = run_performance_benchmark()
        report["metrics"]["performance"] = benchmarks
        
        if "comparison" in benchmarks:
            print(f"      Speedup: {benchmarks['comparison']['speedup']}x")
            print(f"      Improvement: {benchmarks['comparison']['improvement_pct']}%")
        
        # Determine overall success
        success = (
            tests_before.get("success", False) and
            tests_after.get("success", False)
        )
        
    except Exception as e:
        error = str(e)
        success = False
        print(f"\nERROR: {error}")
    
    # Finalize report
    finished_at = datetime.now()
    report["finished_at"] = finished_at.isoformat()
    report["duration_seconds"] = round((finished_at - started_at).total_seconds(), 6)
    report["success"] = success
    report["error"] = error
    
    # Create summary
    report["summary"] = {
        "tests_before_passed": report["metrics"].get("tests_before", {}).get("success", False),
        "tests_after_passed": report["metrics"].get("tests_after", {}).get("success", False),
        "pylint_before_score": report["metrics"].get("pylint_before", {}).get("score"),
        "pylint_after_score": report["metrics"].get("pylint_after", {}).get("score"),
        "complexity_before": report["metrics"].get("radon_before", {}).get("total_complexity"),
        "complexity_after": report["metrics"].get("radon_after", {}).get("total_complexity"),
        "performance_speedup": report["metrics"].get("performance", {}).get("comparison", {}).get("speedup")
    }
    
    # Save report
    report_dir = create_report_directory()
    report_path = report_dir / "report.json"
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    # Also save to evaluation root for easy access
    latest_path = Path("evaluation/latest_report.json")
    with open(latest_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    print(f"\nReport saved to: {report_path}")
    print(f"Latest report:   {latest_path}")
    print(f"\nRun ID:          {run_id}")
    print(f"Duration:        {report['duration_seconds']:.2f}s")
    print(f"Overall Status:  {'SUCCESS' if success else 'FAILED'}")
    
    if report.get("summary"):
        print("\n--- Summary ---")
        summary = report["summary"]
        print(f"Tests (before):    {'PASS' if summary['tests_before_passed'] else 'FAIL'}")
        print(f"Tests (after):     {'PASS' if summary['tests_after_passed'] else 'FAIL'}")
        if summary.get("pylint_before_score") and summary.get("pylint_after_score"):
            print(f"Pylint scores:     {summary['pylint_before_score']}/10 -> {summary['pylint_after_score']}/10")
        if summary.get("complexity_before") and summary.get("complexity_after"):
            print(f"Total complexity:  {summary['complexity_before']} -> {summary['complexity_after']}")
        if summary.get("performance_speedup"):
            print(f"Performance:       {summary['performance_speedup']}x speedup")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

