from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from models import Base, User, Order
from service import latest_orders_per_active_user


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True)
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


def seed_data(session):
    """
    Create:
      - 3 active users
      - 1 inactive user
      - 1 active user with 0 orders (edge case)
      - Orders include a created_at tie for tie-breaking by id DESC.
    """
    u1 = User(email="a@example.com", is_active=True)
    u2 = User(email="b@example.com", is_active=True)
    u3 = User(email="c@example.com", is_active=True)
    u4 = User(email="inactive@example.com", is_active=False)
    u5 = User(email="noorders@example.com", is_active=True)  # active with 0 orders

    session.add_all([u1, u2, u3, u4, u5])
    session.flush()

    def add_order(u, oid, dt, amt):
        session.add(Order(id=oid, user_id=u.id, created_at=dt, amount=Decimal(amt)))

    t1 = datetime(2024, 1, 1, 10, 0, 0)
    t2 = datetime(2024, 1, 2, 10, 0, 0)
    t3 = datetime(2024, 1, 3, 10, 0s, 0)
    t4 = datetime(2024, 1, 4, 10, 0, 0)

    # u1: 3 orders
    add_order(u1, 101, t1, "10.00")
    add_order(u1, 102, t2, "20.00")
    add_order(u1, 103, t3, "30.00")

    # u2: 1 order
    add_order(u2, 201, t2, "5.00")

    # u3: 4 orders, tie at t4 -> id DESC => 303 then 302
    add_order(u3, 301, t1, "1.00")
    add_order(u3, 302, t4, "2.00")
    add_order(u3, 303, t4, "3.00")
    add_order(u3, 304, t3, "4.00")

    # u4 inactive (must not appear)
    add_order(u4, 401, t4, "9.99")
    add_order(u4, 402, t3, "8.88")

    session.commit()
    return u1, u2, u3, u4, u5


class QueryCounter:
    def __init__(self, engine):
        self.engine = engine
        self.count = 0
        self._enabled = False

    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        if self._enabled:
            self.count += 1

    def __enter__(self):
        event.listen(self.engine, "before_cursor_execute", self._before_cursor_execute)
        self._enabled = True
        return self

    def __exit__(self, exc_type, exc, tb):
        self._enabled = False
        event.remove(self.engine, "before_cursor_execute", self._before_cursor_execute)


def test_correctness_latest_2_orders_per_active_user(session):
    u1, u2, u3, u4, u5 = seed_data(session)

    res = latest_orders_per_active_user(session, n=2)

    assert set(res.keys()) == {u1.id, u2.id, u3.id, u5.id}  # inactive excluded, no-orders included
    assert [o.id for o in res[u1.id]] == [103, 102]
    assert [o.id for o in res[u2.id]] == [201]
    assert [o.id for o in res[u3.id]] == [303, 302]
    assert res[u5.id] == []


def test_tie_breaking_created_at_then_id_desc(session):
    _, _, u3, _, _ = seed_data(session)

    res = latest_orders_per_active_user(session, n=3)
    assert [o.id for o in res[u3.id]] == [303, 302, 304]


def test_n_zero_returns_empty_lists_for_active_users(session):
    u1, u2, u3, u4, u5 = seed_data(session)

    res = latest_orders_per_active_user(session, n=0)

    assert set(res.keys()) == {u1.id, u2.id, u3.id, u5.id}
    assert all(v == [] for v in res.values())


def test_regression_query_count_must_be_small(session):
    """
    Must FAIL for repository_before (N+1: 1 users query + per-user orders queries).
    Must PASS for repository_after (<= 3 queries total for function call).
    """
    seed_data(session)
    engine = session.get_bind()

    with QueryCounter(engine) as qc:
        _ = latest_orders_per_active_user(session, n=2)

    assert qc.count <= 3, f"Too many SQL statements: {qc.count} (N+1 likely present)"
