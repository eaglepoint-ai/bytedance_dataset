from __future__ import annotations

import threading
import pytest

from app.db import get_conn, reset_schema
from app.transfer import transfer_funds, InsufficientFunds


@pytest.fixture(autouse=True)
def _reset():
    reset_schema()


def _run_transfer(
    barrier: threading.Barrier,
    from_id: int,
    to_id: int,
    amount: int,
    errors: list[BaseException],
):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SET deadlock_timeout = '50ms';")
                cur.execute("SET lock_timeout = '2s';")

            barrier.wait()
            transfer_funds(conn, from_id, to_id, amount)
    except BaseException as e:
        errors.append(e)


def _balances():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, balance FROM accounts ORDER BY id;")
            return dict(cur.fetchall())


def test_multiway_concurrent_transfers():
    """Concurrency regression: multiple opposing transfers must complete without errors."""
    barrier = threading.Barrier(5)
    errors: list[BaseException] = []

    threads = [
        threading.Thread(target=_run_transfer, args=(barrier, 1, 2, 300, errors)),
        threading.Thread(target=_run_transfer, args=(barrier, 2, 1, 200, errors)),
        threading.Thread(target=_run_transfer, args=(barrier, 2, 3, 400, errors)),
        threading.Thread(target=_run_transfer, args=(barrier, 3, 2, 150, errors)),
        threading.Thread(target=_run_transfer, args=(barrier, 1, 3, 100, errors)),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if errors:
        raise AssertionError(f"Transfer threads raised errors: {errors!r}")

    assert _balances() == {1: 800, 2: 850, 3: 1350}


def test_final_balances_are_correct():
    """PASS-to-PASS: sanity check balances are deterministic in a single-thread sequence."""
    with get_conn() as conn:
        transfer_funds(conn, 1, 2, 300)
        transfer_funds(conn, 2, 1, 200)
        transfer_funds(conn, 2, 3, 400)
        transfer_funds(conn, 3, 2, 150)
        transfer_funds(conn, 1, 3, 100)
    assert _balances() == {1: 800, 2: 850, 3: 1350}


def test_insufficient_funds_rolls_back_atomically():
    """PASS-to-PASS: insufficient funds must not partially update balances."""
    before = _balances()
    with pytest.raises(InsufficientFunds):
        with get_conn() as conn:
            transfer_funds(conn, 1, 2, 10_000)  # impossible (would go negative)

    after = _balances()
    assert after == before, "Balances changed despite InsufficientFunds (non-atomic behavior)"
