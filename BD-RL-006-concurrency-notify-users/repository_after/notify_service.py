"""Optimized notification service with bounded concurrency."""

from __future__ import annotations

import concurrent.futures
import threading
import time
import random
from typing import List, Any

MAX_WORKERS = 50

_executor_lock = threading.Lock()
_executor: concurrent.futures.ThreadPoolExecutor | None = None


def _get_executor() -> concurrent.futures.ThreadPoolExecutor:
    global _executor
    with _executor_lock:
        if _executor is None or _executor._shutdown:  # type: ignore[attr-defined]
            _executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
        return _executor


# DO NOT MODIFY THIS FUNCTION (copied from before for clarity)
def send_notification(user_id, payload):
    """Simulates a slow I/O-bound notification send."""
    time.sleep(0.02)
    if random.random() < 0.05:
        raise RuntimeError("send failed")
    return f"sent:{user_id}"


def _notify_one(user_id, payload):
    """Worker function that performs lookup + send in a worker thread."""
    time.sleep(0.01)
    return send_notification(user_id, payload)


def notify_users(user_ids, payload):
    """Notify many users concurrently with a global 50-call cap."""
    user_ids = list(user_ids)
    n = len(user_ids)
    if n == 0:
        return []

    results: List[Any] = [None] * n
    executor = _get_executor()

    futures: dict[concurrent.futures.Future, int] = {}
    it = iter(range(n))

    def submit_next(index: int) -> None:
        fut = executor.submit(_notify_one, user_ids[index], payload)
        futures[fut] = index

    try:
        for _ in range(min(MAX_WORKERS, n)):
            idx = next(it)
            submit_next(idx)
    except StopIteration:
        pass

    try:
        while futures:
            done, _pending = concurrent.futures.wait(
                list(futures.keys()),
                return_when=concurrent.futures.FIRST_COMPLETED,
            )
            for fut in done:
                idx = futures.pop(fut)
                try:
                    results[idx] = fut.result()
                except Exception as e:  # noqa: BLE001
                    results[idx] = str(e)
                try:
                    next_idx = next(it)
                except StopIteration:
                    continue
                submit_next(next_idx)
    except BaseException:
        for fut in futures:
            fut.cancel()
        raise

    return results
