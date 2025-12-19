#!/usr/bin/env python3
"""
Performance benchmark runner for the TransactionProcessor before/after implementations.

Run with:
    python evaluation/performance_benchmark.py [options]

Options:
    --transactions N   Number of synthetic transactions to replay (default: 500)
    --customers N      Number of synthetic customers (default: 60)
    --iterations N     Number of times to replay the workload per implementation (default: 5)
    --seed N           Random seed for reproducibility (default: 42)
    --output-dir DIR   Output directory for reports (default: evaluation/)
"""
import argparse
import importlib.util
import io
import json
import os
import platform
import random
import subprocess
import sys
import traceback
import uuid
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    # Ensure dataclass machinery sees a proper module entry
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _get_git_rev(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def get_git_commit() -> str:
    return _get_git_rev(["git", "rev-parse", "--short", "HEAD"])


def get_git_branch() -> str:
    return _get_git_rev(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def get_environment_info() -> dict:
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "os": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "git_commit": get_git_commit(),
        "git_branch": get_git_branch(),
    }


def _as_float(value: Decimal) -> float:
    return float(Decimal(value))


def build_dataset(params: dict) -> dict:
    rng = random.Random(params["seed"])

    account_types = ["STANDARD", "PREMIUM", "BUSINESS"]
    transaction_types = ["DOMESTIC", "INTERNATIONAL", "INSTANT"]
    channels = ["BRANCH", "MOBILE_APP", "WEB", "ATM"]
    currencies = ["USD", "EUR", "GBP", "JPY"]
    locations = ["US", "CA", "GB", "JP", "AU", "DE", "FR", "BR"]

    customers = []
    for i in range(params["customers"]):
        acct = rng.choice(account_types)
        daily_limit = Decimal(str(rng.choice([7500, 10000, 15000, 20000])))
        overdraft_limit = Decimal(str(rng.choice([500, 750, 1000])))
        frequent = rng.sample(locations, k=rng.randint(0, 3))
        customers.append(
            {
                "id": i + 1,
                "account_type": acct,
                "daily_limit": str(daily_limit),
                "has_overdraft_protection": rng.choice([True, False]),
                "overdraft_limit": str(overdraft_limit),
                "average_transaction": str(Decimal(rng.randint(150, 750))),
                "home_location": rng.choice(locations),
                "last_login_location": rng.choice(locations),
                "monthly_transaction_count": rng.randint(50, 180),
                "loyalty_score": str(Decimal(rng.randint(0, 100))),
                "frequent_travel_locations": frequent,
            }
        )

    requests = []
    base_ts = datetime(2024, 1, 1, 9, 0, 0)
    for _ in range(params["transactions"]):
        tx_type = rng.choice(transaction_types)
        channel = rng.choice(channels)
        amount = Decimal(str(round(rng.uniform(50, 4500), 2)))
        currency = rng.choice(currencies if tx_type != "INTERNATIONAL" else currencies[1:])
        ts = base_ts + timedelta(minutes=rng.randint(0, 60 * 5), days=rng.randint(0, 3))
        requests.append(
            {
                "amount": str(amount),
                "transaction_type": tx_type,
                "channel": channel,
                "location": rng.choice(locations),
                "currency": currency,
                "timestamp": ts.isoformat(),
            }
        )

    assignment = [rng.randrange(len(customers)) for _ in range(len(requests))]

    total_amount = sum(Decimal(r["amount"]) for r in requests)
    summary = {
        "customers": len(customers),
        "requests": len(requests),
        "account_types": dict(Counter(c["account_type"] for c in customers)),
        "transaction_types": dict(Counter(r["transaction_type"] for r in requests)),
        "channels": dict(Counter(r["channel"] for r in requests)),
        "currencies": dict(Counter(r["currency"] for r in requests)),
        "average_amount": round(_as_float(total_amount) / max(len(requests), 1), 2),
        "total_amount": round(_as_float(total_amount), 2),
    }

    return {
        "customers": customers,
        "requests": requests,
        "assignment": assignment,
        "summary": summary,
    }


def _materialize_objects(module, dataset: dict):
    customers = []
    for c in dataset["customers"]:
        customers.append(
            module.CustomerProfile(
                id=c["id"],
                account_type=module.AccountType[c["account_type"]],
                daily_limit=Decimal(c["daily_limit"]),
                has_overdraft_protection=c["has_overdraft_protection"],
                overdraft_limit=Decimal(c["overdraft_limit"]),
                average_transaction=Decimal(c["average_transaction"]),
                home_location=c["home_location"],
                last_login_location=c["last_login_location"],
                monthly_transaction_count=c["monthly_transaction_count"],
                loyalty_score=Decimal(c["loyalty_score"]),
                frequent_travel_locations=list(c["frequent_travel_locations"]),
            )
        )

    requests = []
    for r in dataset["requests"]:
        requests.append(
            module.TransactionRequest(
                amount=Decimal(r["amount"]),
                transaction_type=module.TransactionType[r["transaction_type"]],
                channel=module.Channel[r["channel"]],
                location=r["location"],
                currency=r["currency"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
            )
        )

    return customers, requests


def measure_variant(label: str, module, dataset: dict, iterations: int) -> dict:
    customers, requests = _materialize_objects(module, dataset)

    iteration_stats = []
    total_errors = 0
    total_reviews = 0
    total_messages = 0
    samples = []

    for _ in range(iterations):
        processor = module.TransactionProcessor()
        errors = 0
        reviews = 0
        messages = 0

        start = perf_counter()
        for idx, cust_idx in enumerate(dataset["assignment"]):
            try:
                res = processor.process_transaction(requests[idx], customers[cust_idx])
                messages += len(res.messages)
                if res.requires_review:
                    reviews += 1
                if len(samples) < 6:
                    samples.append(
                        {
                            "request_index": idx,
                            "processed_amount": str(res.processed_amount),
                            "requires_review": res.requires_review,
                            "messages": list(res.messages),
                        }
                    )
            except Exception as exc:
                errors += 1
                if len(samples) < 6:
                    samples.append(
                        {
                            "request_index": idx,
                            "error": exc.__class__.__name__,
                            "message": str(exc),
                        }
                    )

        duration_ms = (perf_counter() - start) * 1000
        iteration_stats.append(
            {
                "duration_ms": round(duration_ms, 3),
                "errors": errors,
                "reviews": reviews,
                "messages": messages,
            }
        )
        total_errors += errors
        total_reviews += reviews
        total_messages += messages

    total_time_ms = sum(item["duration_ms"] for item in iteration_stats)
    total_transactions = len(dataset["requests"]) * iterations
    avg_tx_ms = total_time_ms / max(total_transactions, 1)
    throughput = (total_transactions / (total_time_ms / 1000)) if total_time_ms > 0 else 0

    return {
        "label": label,
        "summary": {
            "total_transactions": total_transactions,
            "total_time_ms": round(total_time_ms, 3),
            "avg_tx_ms": round(avg_tx_ms, 4),
            "throughput_tps": round(throughput, 2),
            "errors": total_errors,
            "reviews": total_reviews,
            "messages": total_messages,
        },
        "iterations": iteration_stats,
        "samples": samples,
    }


def run_benchmarks(params: dict) -> dict:
    dataset = build_dataset(params)
    before_mod = _load_module("transaction_processor_before", ROOT / "repository_before" / "transaction_processor.py")
    after_mod = _load_module("transaction_processor_after", ROOT / "repository_after" / "transaction_processor.py")

    before_metrics = measure_variant("before", before_mod, dataset, params["iterations"])
    after_metrics = measure_variant("after", after_mod, dataset, params["iterations"])

    b = before_metrics["summary"]
    a = after_metrics["summary"]
    speedup = (b["avg_tx_ms"] / a["avg_tx_ms"]) if a["avg_tx_ms"] > 0 else 0
    throughput_gain = a["throughput_tps"] - b["throughput_tps"]

    comparison = {
        "speedup": round(speedup, 3),
        "throughput_delta_tps": round(throughput_gain, 2),
        "error_delta": a["errors"] - b["errors"],
        "review_delta": a["reviews"] - b["reviews"],
    }

    return {
        "dataset_summary": dataset["summary"],
        "before": before_metrics,
        "after": after_metrics,
        "comparison": comparison,
    }


def generate_markdown_report(report_data: dict) -> str:
    env = report_data["environment"]
    params = report_data["parameters"]
    metrics = report_data["metrics"]
    ds = metrics["dataset_summary"]

    md = f"""# Transaction Processor Benchmark

**Run ID:** `{report_data['run_id']}`  
**Started:** {report_data['started_at']}  
**Finished:** {report_data['finished_at']}  
**Duration:** {report_data['duration_seconds']:.2f} seconds

---

## Environment

| Property | Value |
|---|---|
| Python Version | {env['python_version']} |
| Platform | {env['platform']} |
| OS | {env['os']} {env['os_release']} |
| Architecture | {env['architecture']} |
| Git Commit | `{env['git_commit']}` |
| Git Branch | `{env['git_branch']}` |

---

## Parameters

| Parameter | Value |
|---|---|
| Transactions | {params['transactions']} |
| Customers | {params['customers']} |
| Iterations | {params['iterations']} |
| Seed | {params['seed']} |
| Output Dir | {params['output_dir']} |

---

## Dataset Summary

| Metric | Value |
|---|---|
| Customers | {ds['customers']} |
| Requests | {ds['requests']} |
| Avg Amount | {ds['average_amount']} |
| Total Amount | {ds['total_amount']} |
| Account Types | {', '.join(f"{k}:{v}" for k, v in ds['account_types'].items())} |
| Transaction Types | {', '.join(f"{k}:{v}" for k, v in ds['transaction_types'].items())} |
| Channels | {', '.join(f"{k}:{v}" for k, v in ds['channels'].items())} |
| Currencies | {', '.join(f"{k}:{v}" for k, v in ds['currencies'].items())} |

---

## Results Summary

| Variant | Avg per Tx (ms) | Throughput (tx/s) | Errors | Reviews | Messages |
|---|---|---|---|---|---|
| Before | {metrics['before']['summary']['avg_tx_ms']:.4f} | {metrics['before']['summary']['throughput_tps']:.2f} | {metrics['before']['summary']['errors']} | {metrics['before']['summary']['reviews']} | {metrics['before']['summary']['messages']} |
| After | {metrics['after']['summary']['avg_tx_ms']:.4f} | {metrics['after']['summary']['throughput_tps']:.2f} | {metrics['after']['summary']['errors']} | {metrics['after']['summary']['reviews']} | {metrics['after']['summary']['messages']} |

**Speedup:** {metrics['comparison']['speedup']:.3f}x  \
**Throughput Delta:** {metrics['comparison']['throughput_delta_tps']:+.2f} tx/s  \
**Error Delta:** {metrics['comparison']['error_delta']}  \
**Review Delta:** {metrics['comparison']['review_delta']}

---

## Per-Iteration Details

| Variant | Iteration | Duration (ms) | Errors | Reviews | Messages |
|---|---|---|---|---|---|
"""

    for idx, it in enumerate(metrics["before"]["iterations"], start=1):
        md += f"| Before | {idx} | {it['duration_ms']:.3f} | {it['errors']} | {it['reviews']} | {it['messages']} |\\n"
    for idx, it in enumerate(metrics["after"]["iterations"], start=1):
        md += f"| After | {idx} | {it['duration_ms']:.3f} | {it['errors']} | {it['reviews']} | {it['messages']} |\\n"

    md += "\n---\n\n## Sample Results\n\n"
    for sample in metrics["after"].get("samples", [])[:5]:
        if "error" in sample:
            md += f"- Request {sample['request_index']}: ERROR {sample['error']} ({sample.get('message','')})\\n"
        else:
            md += (
                f"- Request {sample['request_index']}: amount={sample['processed_amount']}, "
                f"review={sample['requires_review']}, messages={sample['messages']}\\n"
            )

    return md


def main() -> int:
    parser = argparse.ArgumentParser(description="Run TransactionProcessor performance benchmark")
    parser.add_argument("--transactions", type=int, default=500, help="Number of synthetic transactions (default: 500)")
    parser.add_argument("--customers", type=int, default=60, help="Number of synthetic customers (default: 60)")
    parser.add_argument("--iterations", type=int, default=5, help="Iterations per implementation (default: 5)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default="evaluation", help="Output directory (default: evaluation)")
    args = parser.parse_args()

    parameters = {
        "transactions": args.transactions,
        "customers": args.customers,
        "iterations": args.iterations,
        "seed": args.seed,
        "output_dir": args.output_dir,
    }

    run_id = str(uuid.uuid4())[:8]
    started_at = datetime.now()
    date_folder = started_at.strftime("%Y-%m-%d")
    timestamp = started_at.strftime("%H-%M-%S")
    output_path = Path(args.output_dir) / date_folder / timestamp
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("TRANSACTION PROCESSOR BENCHMARK")
    print("=" * 60)
    print(f"Run ID: {run_id}")
    print(f"Started: {started_at.isoformat()}")
    print(f"Output: {output_path}")
    print("=" * 60)
    print(f"Parameters: {json.dumps(parameters, indent=2)}")

    stdout_capture = io.StringIO()
    success = False
    error_message = None
    metrics = None

    with redirect_stdout(stdout_capture):
        try:
            metrics = run_benchmarks(parameters)
            success = True
            print("\nDataset summary:")
            print(json.dumps(metrics["dataset_summary"], indent=2))
            print("\nBefore summary:")
            print(json.dumps(metrics["before"]["summary"], indent=2))
            print("\nAfter summary:")
            print(json.dumps(metrics["after"]["summary"], indent=2))
            print("\nComparison:")
            print(json.dumps(metrics["comparison"], indent=2))
        except Exception as exc:
            error_message = str(exc)
            traceback.print_exc()

    finished_at = datetime.now()
    duration = (finished_at - started_at).total_seconds()

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

    json_path = output_path / "report.json"
    with open(json_path, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"Saved JSON report to {json_path}")

    if success:
        md_path = output_path / "report.md"
        with open(md_path, "w") as f:
            f.write(generate_markdown_report(report_data))
        print(f"Saved markdown report to {md_path}")

    log_path = output_path / "stdout.log"
    with open(log_path, "w") as f:
        f.write(stdout_capture.getvalue())
    print(f"Saved stdout log to {log_path}")

    print("\n" + "=" * 60)
    print("BENCHMARK COMPLETE")
    print("=" * 60)
    print(f"Duration: {duration:.2f}s")
    print(f"Reports saved to: {output_path}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
