from __future__ import annotations

import os
from pathlib import Path
import psycopg


def dsn() -> str:
    return os.getenv("DATABASE_URL", "postgresql://app:app@localhost:5432/appdb")


def get_conn() -> psycopg.Connection:
    return psycopg.connect(dsn())


def reset_schema() -> None:
    sql_path = Path(__file__).with_name("schema.sql")
    sql = sql_path.read_text(encoding="utf-8")
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
