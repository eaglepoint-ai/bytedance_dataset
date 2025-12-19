from __future__ import annotations

import os
import timeit
import threading
from pathlib import Path

import psycopg

from app.db import get_conn, reset_schema
from app.transfer import transfer_funds


def run_workload_once() -> int:
    """Run the concurrency workload once. Return number of thread errors."""
    reset_schema()

    barrier = threading.Barrier(5)
    errors: list[BaseException] = []

    def _run(from_id: int, to_id: int, amount: int) -> None:
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SET deadlock_timeout = '50ms';")
                    cur.execute("SET lock_timeout = '2s';")
                barrier.wait()
                transfer_funds(conn, from_id, to_id, amount)
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


def run_once_for_timing() -> None:
    # Keep timing separate from printing/summary.
    _ = run_workload_once()


if __name__ == "__main__":
    target = os.environ.get("PYTHONPATH", "")
    print(f"Benchmark target PYTHONPATH={target}")

    # 1) Stability proof (repeat a few times and count failures)
    trials = 20
    failures = 0
    for _ in range(trials):
        failures += (1 if run_workload_once() > 0 else 0)

    print(f"Workload trials: {trials}")
    print(f"Trials with errors: {failures}")

    # 2) Timing (multiple runs)
    runs = 10
    t = timeit.timeit("run_once_for_timing()", number=runs, globals=globals())
    print(f"Total time ({runs} runs): {t:.4f}s")
    print(f"Avg time/run: {t/runs:.6f}s")
