from __future__ import annotations

import psycopg


class InsufficientFunds(Exception):
    pass


def _lock_account(cur: psycopg.Cursor, account_id: int) -> None:
    """Lock one account row and validate it exists."""
    cur.execute("SELECT 1 FROM accounts WHERE id = %s FOR UPDATE;", (account_id,))
    if cur.fetchone() is None:
        raise ValueError(f"account not found: {account_id}")


def transfer_funds(conn: psycopg.Connection, from_id: int, to_id: int, amount: int) -> None:
    if amount <= 0:
        raise ValueError("amount must be positive")
    if from_id == to_id:
        raise ValueError("from_id and to_id must differ")

    first_id, second_id = sorted((from_id, to_id))

    # Own the transaction so atomicity doesn't depend on the caller.
    with conn.transaction():
        with conn.cursor() as cur:
            # Acquire locks in a consistent global order to avoid deadlocks.
            _lock_account(cur, first_id)
            _lock_account(cur, second_id)

            # Now both rows are locked; read the source balance safely.
            cur.execute("SELECT balance FROM accounts WHERE id = %s;", (from_id,))
            row = cur.fetchone()
            if row is None:
                raise ValueError("from_id not found")
            from_balance = int(row[0])

            if from_balance < amount:
                raise InsufficientFunds()

            # Apply updates; locks prevent concurrent modification until commit.
            cur.execute(
                "UPDATE accounts SET balance = balance - %s WHERE id = %s;",
                (amount, from_id),
            )
            cur.execute(
                "UPDATE accounts SET balance = balance + %s WHERE id = %s;",
                (amount, to_id),
            )
