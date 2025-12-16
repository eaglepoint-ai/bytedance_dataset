from __future__ import annotations

import psycopg


class InsufficientFunds(Exception):
    pass


def transfer_funds(conn: psycopg.Connection, from_id: int, to_id: int, amount: int) -> None:
    if amount <= 0:
        raise ValueError("amount must be positive")

    with conn.cursor() as cur:
        cur.execute("BEGIN;")

        cur.execute("SELECT balance FROM accounts WHERE id = %s;", (from_id,))
        row = cur.fetchone()
        if row is None:
            raise ValueError("from_id not found")

        from_balance = row[0]
        if from_balance < amount:
            cur.execute("ROLLBACK;")
            raise InsufficientFunds()

        cur.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s;", (amount, from_id))
        cur.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s;", (amount, to_id))

        cur.execute("COMMIT;")
