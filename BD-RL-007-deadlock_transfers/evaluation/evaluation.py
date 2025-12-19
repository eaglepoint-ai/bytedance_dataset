#!/usr/bin/env python3
"""
Evaluation runner for Deadlock Transfers (Concurrency & Locking).

This evaluation script:
- Tests both before and after implementations
- Runs performance benchmarks under concurrency
- Measures deadlock frequency and performance improvements
- Generates structured reports

Run with:
    docker compose run --rm app python evaluation/evaluation.py
"""
import os
import sys
import json
import timeit
import threading
import subprocess
from datetime import datetime
from pathlib import Path

import psycopg

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "repository_before"))
sys.path.insert(0, str(Path(__file__).parent.parent / "repository_after"))


def run_tests(implementation_name, pythonpath):
    """Run pytest tests for a given implementation."""
    print(f"\nRunning tests for {implementation_name}...")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = pythonpath
    env["DATABASE_URL"] = os.getenv("DATABASE_URL", "postgresql://app:app@db:5432/appdb")
    
    try:
        result = subprocess.run(
            ["pytest", "-q", "/app/tests"],
            env=env,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        
        return {
            "passed": passed,
            "return_code": result.returncode,
            "output": output,
        }
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "return_code": -1,
            "output": "Test execution timed out",
        }
    except Exception as e:
        return {
            "passed": False,
            "return_code": -1,
            "output": f"Error running tests: {str(e)}",
        }


def run_workload_once(transfer_func, get_conn_func, reset_schema_func):
    """Run the concurrency workload once. Return number of thread errors."""
    reset_schema_func()

    barrier = threading.Barrier(5)
    errors: list[BaseException] = []

    def _run(from_id: int, to_id: int, amount: int) -> None:
        try:
            conn = get_conn_func()
            with conn.cursor() as cur:
                cur.execute("SET deadlock_timeout = '50ms';")
                cur.execute("SET lock_timeout = '2s';")
            barrier.wait()
            transfer_func(conn, from_id, to_id, amount)
            conn.close()
        except BaseException as e:
            errors.append(e)

    threads = [
        threading.Thread(target=_run, args=(1, 2, 300)),
        threading.Thread(target=_run, args=(2, 1, 200)),
        threading.Thread(target=_run, args=(2, 3, 400)),
        threading.Thread(target=_run, args=(3, 2, 150)),
        threading.Thread(target=_run, args=(1, 3, 100)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return len(errors)


def run_benchmark(implementation_name, pythonpath):
    """Run performance benchmark for a given implementation."""
    print(f"\nRunning benchmark for {implementation_name}...")
    
    # Save original sys.path and modify it
    original_path = sys.path[:]
    try:
        # Clear any existing app module from cache
        modules_to_remove = [m for m in sys.modules.keys() if m.startswith('app.')]
        for m in modules_to_remove:
            del sys.modules[m]
        
        # Add the implementation path
        if pythonpath not in sys.path:
            sys.path.insert(0, pythonpath)
        
        # Import the implementation
        from app.db import get_conn, reset_schema
        from app.transfer import transfer_funds
    except ImportError as e:
        sys.path[:] = original_path
        return {
            "error": f"Failed to import modules: {str(e)}",
            "trials": 0,
            "failures": 0,
            "avg_time_seconds": None,
        }
    finally:
        # Restore original path after imports
        sys.path[:] = original_path
    
    # Set database URL
    db_url = os.getenv("DATABASE_URL", "postgresql://app:app@db:5432/appdb")
    os.environ["DATABASE_URL"] = db_url
    
    # 1) Stability proof (repeat a few times and count failures)
    trials = 20
    failures = 0
    for _ in range(trials):
        errors = run_workload_once(transfer_funds, get_conn, reset_schema)
        if errors > 0:
            failures += 1
    
    # 2) Timing (multiple runs)
    def run_once_for_timing():
        _ = run_workload_once(transfer_funds, get_conn, reset_schema)
    
    runs = 10
    total_time = timeit.timeit(run_once_for_timing, number=runs, globals=globals())
    avg_time = total_time / runs
    
    return {
        "trials": trials,
        "failures": failures,
        "failure_rate": failures / trials if trials > 0 else 0.0,
        "runs": runs,
        "total_time_seconds": total_time,
        "avg_time_seconds": avg_time,
    }


def evaluate_implementation(implementation_name, pythonpath):
    """Evaluate a single implementation (before or after)."""
    print(f"\n{'=' * 60}")
    print(f"EVALUATING: {implementation_name.upper()}")
    print(f"{'=' * 60}")
    
    # Run tests
    test_results = run_tests(implementation_name, pythonpath)
    if test_results["passed"]:
        print(f"✅ Tests passed")
    else:
        print(f"❌ Tests failed (return code: {test_results['return_code']})")
    
    # Run benchmark
    benchmark_results = run_benchmark(implementation_name, pythonpath)
    if "error" in benchmark_results:
        print(f"❌ Benchmark error: {benchmark_results['error']}")
    else:
        print(f"Benchmark results:")
        print(f"  Trials: {benchmark_results['trials']}")
        print(f"  Failures: {benchmark_results['failures']} ({benchmark_results['failure_rate']*100:.1f}%)")
        print(f"  Avg time: {benchmark_results['avg_time_seconds']:.6f}s")
    
    return {
        "tests": test_results,
        "benchmark": benchmark_results,
    }


def run_evaluation():
    """
    Run complete evaluation for both implementations and collect metrics.
    
    Returns dict with metrics from both before and after implementations.
    """
    print(f"\n{'=' * 60}")
    print("DEADLOCK TRANSFERS EVALUATION")
    print(f"{'=' * 60}")
    
    # Evaluate before implementation
    before_path = "/app/repository_before"
    before_metrics = evaluate_implementation("before", before_path)
    
    # Evaluate after implementation
    after_path = "/app/repository_after"
    after_metrics = evaluate_implementation("after", after_path)
    
    # Calculate improvements
    before_failures = before_metrics["benchmark"].get("failures", 0)
    after_failures = after_metrics["benchmark"].get("failures", 0)
    
    before_avg_time = before_metrics["benchmark"].get("avg_time_seconds")
    after_avg_time = after_metrics["benchmark"].get("avg_time_seconds")
    
    speedup = None
    improvement_pct = None
    if before_avg_time and after_avg_time and after_avg_time > 0:
        speedup = before_avg_time / after_avg_time
        improvement_pct = ((before_avg_time - after_avg_time) / before_avg_time) * 100
    
    # Compile results
    metrics = {
        "before": {
            "tests_passed": before_metrics["tests"]["passed"],
            "benchmark": before_metrics["benchmark"],
        },
        "after": {
            "tests_passed": after_metrics["tests"]["passed"],
            "benchmark": after_metrics["benchmark"],
        },
        "comparison": {
            "deadlock_elimination": before_failures > 0 and after_failures == 0,
            "failure_reduction": before_failures - after_failures,
            "speedup": round(speedup, 2) if speedup else None,
            "improvement_pct": round(improvement_pct, 1) if improvement_pct else None,
        },
    }
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("EVALUATION SUMMARY")
    print(f"{'=' * 60}")
    print(f"\nTests:")
    print(f"  Before: {'✅ PASSED' if before_metrics['tests']['passed'] else '❌ FAILED'}")
    print(f"  After:  {'✅ PASSED' if after_metrics['tests']['passed'] else '❌ FAILED'}")
    
    print(f"\nBenchmark (Concurrency Stability):")
    print(f"  Before failures: {before_failures}/{before_metrics['benchmark'].get('trials', 0)} ({before_metrics['benchmark'].get('failure_rate', 0)*100:.1f}%)")
    print(f"  After failures:  {after_failures}/{after_metrics['benchmark'].get('trials', 0)} ({after_metrics['benchmark'].get('failure_rate', 0)*100:.1f}%)")
    
    if before_avg_time and after_avg_time:
        print(f"\nPerformance:")
        print(f"  Before avg: {before_avg_time:.6f}s")
        print(f"  After avg:  {after_avg_time:.6f}s")
        if speedup:
            print(f"  Speedup: {metrics['comparison']['speedup']:.2f}x faster")
            print(f"  Improvement: {metrics['comparison']['improvement_pct']:.1f}%")
    
    if metrics["comparison"]["deadlock_elimination"]:
        print(f"\n✅ Deadlocks Successfully Eliminated!")
    elif after_failures == 0:
        print(f"\n✅ No deadlocks in after implementation")
    else:
        print(f"\n⚠️  Warning: After implementation still has deadlocks")
    
    return metrics


def main():
    """Main entry point for evaluation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run deadlock transfers evaluation")
    parser.add_argument("--output", type=str, default="evaluation/report.json", help="Output JSON file path (default: evaluation/report.json)")
    
    args = parser.parse_args()
    
    started_at = datetime.now()
    
    try:
        metrics = run_evaluation()
        success = True
        error_message = None
    except Exception as e:
        import traceback
        print(f"\nERROR: {str(e)}")
        traceback.print_exc()
        metrics = None
        success = False
        error_message = str(e)
    
    finished_at = datetime.now()
    duration = (finished_at - started_at).total_seconds()
    
    # Build report
    report = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": duration,
        "success": success,
        "error": error_message,
        "metrics": metrics,
    }
    
    # Output JSON to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n✅ Report saved to: {output_path}")
    
    print(f"\n{'=' * 60}")
    print(f"EVALUATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Duration: {duration:.2f}s")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

