from __future__ import annotations

import os
import timeit
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from models import Base, User, Order
from service import latest_orders_per_active_user


def seed(session, users=2000, orders_per_user=300, active_ratio=0.8):
    session.query(Order).delete()
    session.query(User).delete()
    session.commit()

    now = datetime(2024, 1, 1, 0, 0, 0)
    for i in range(users):
        u = User(email=f"user{i}@example.com", is_active=(i < int(users * active_ratio)))
        session.add(u)
        session.flush()

        for j in range(orders_per_user):
            session.add(
                Order(
                    id=(i * 10000000 + j + 1),
                    user_id=u.id,
                    created_at=now + timedelta(minutes=j),
                    amount=Decimal("1.00"),
                )
            )

    session.commit()


def count_sql_statements(engine, fn):
    counter = {"n": 0}

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        counter["n"] += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    try:
        fn()
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)

    return counter["n"]


def run_once_and_count_queries():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    s = SessionLocal()

    seed(s, users=2000, orders_per_user=300)

    q = count_sql_statements(engine, lambda: latest_orders_per_active_user(s, n=2))

    s.close()
    return q


def run_once_for_timing():
    # Keep timing separate so printing/query counting doesn't distort it too much.
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    s = SessionLocal()

    seed(s, users=2000, orders_per_user=300)
    latest_orders_per_active_user(s, n=2)

    s.close()


if __name__ == "__main__":
    target = os.environ.get("PYTHONPATH", "")
    print(f"Benchmark target PYTHONPATH={target}")

    # 1) Query count proof (single run)
    q = run_once_and_count_queries()
    print(f"SQL statements (single run): {q}")

    # 2) Timing (multiple runs)
    runs = 10
    t = timeit.timeit("run_once_for_timing()", number=runs, globals=globals())
    print(f"Total time ({runs} runs): {t:.4f}s")
    print(f"Avg time/run: {t/runs:.6f}s")
