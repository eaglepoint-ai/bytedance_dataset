#!/usr/bin/env python3
"""
Meta-test runner for the GMS Sequence Generator task.

Executes the meta tests and emits a detailed JSON report describing the results.
"""

import argparse
import json
import platform
import re
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def get_environment_info() -> dict:
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
    }


def parse_pytest_summary(output: str) -> dict:
    """Extract simple counts from pytest terminal output."""

    counts: dict[str, int] = {}
    for count, label in re.findall(r"(\d+)\s+(passed|failed|skipped|xfailed|xpassed|warnings?)", output):
        counts[label] = counts.get(label, 0) + int(count)
    return counts


def load_json_report(path: Path) -> dict | None:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def run_meta_tests(test_path: str, extra_args: list[str]) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        report_path = Path(tmp.name)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        test_path,
        "--json-report",
        f"--json-report-file={report_path}",
        *extra_args,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    stdout = proc.stdout
    stderr = proc.stderr
    summary = parse_pytest_summary(stdout + "\n" + stderr)
    json_report = load_json_report(report_path)
    try:
        report_path.unlink(missing_ok=True)
    except Exception:
        pass
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "summary": summary,
        "json_report": json_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run meta tests and emit JSON report")
    parser.add_argument("--tests", default="tests/test_sequence_generator_meta.py", help="Path to meta tests")
    parser.add_argument("--output-dir", default="evaluation", help="Directory to store reports")
    parser.add_argument("--pytest-args", nargs="*", default=[], help="Additional args forwarded to pytest")
    args = parser.parse_args()

    run_id = str(uuid.uuid4())[:8]
    started_at = datetime.now()
    timestamp = started_at.strftime("%Y%m%d-%H%M%S")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_filename = f"report-{timestamp}-{run_id}.json"
    output_path = output_dir / report_filename

    test_results = run_meta_tests(args.tests, args.pytest_args)

    finished_at = datetime.now()
    duration = (finished_at - started_at).total_seconds()

    json_report = test_results["json_report"] or {}
    tests_section = json_report.get("tests", [])
    totals = json_report.get("summary", {})

    detailed_results = []
    for t in tests_section:
        outcome = t.get("outcome")
        duration = t.get("duration")
        nodeid = t.get("nodeid")
        longrepr = t.get("longrepr")
        failure_messages = []
        if outcome == "failed" and longrepr:
            if isinstance(longrepr, str):
                failure_messages.append(longrepr)
            elif isinstance(longrepr, dict):
                failure_messages.append(longrepr.get("reprcrash", ""))
        detailed_results.append(
            {
                "name": nodeid,
                "status": outcome,
                "duration": duration,
                "failureMessages": failure_messages,
                "keywords": t.get("keywords", []),
            }
        )

    meta_metrics = {
        "numTotalTests": totals.get("total", len(tests_section)),
        "numPassedTests": totals.get("passed", 0),
        "numFailedTests": totals.get("failed", 0) + totals.get("error", 0),
        "numSkippedTests": totals.get("skipped", 0),
        "numXfailedTests": totals.get("xfailed", 0),
        "numXpassedTests": totals.get("xpassed", 0),
        "testResults": detailed_results,
    }

    report = {
        "task": "GMS meta-test verification",
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": duration,
        "success": test_results["returncode"] == 0,
        "environment": get_environment_info(),
        "tests": {
            "path": args.tests,
            "command": test_results["command"],
            "returncode": test_results["returncode"],
            "summary": test_results["summary"],
        },
        "metrics": {
            "meta": meta_metrics,
            "summary": {
                "totalTests": meta_metrics["numTotalTests"],
                "totalPasses": meta_metrics["numPassedTests"],
                "totalFailures": meta_metrics["numFailedTests"],
            },
            "raw_pytest_json": json_report,
        },
        "stdout": test_results["stdout"],
        "stderr": test_results["stderr"],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Run ID: {run_id}")
    print(f"Report: {output_path}")
    print(f"Success: {report['success']}")

    return 0 if report["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
