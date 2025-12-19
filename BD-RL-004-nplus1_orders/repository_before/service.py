"""Service layer functions for order retrieval and aggregation."""

from __future__ import annotations

from typing import Dict, List

from sqlalchemy.orm import Session

from models import Order, User


def latest_orders_per_active_user(session: Session, top_n: int = 2) -> Dict[int, List[Order]]:
    """Return up to top_n latest orders per active user.

    Note: This implementation intentionally triggers an N+1 query pattern by
    accessing the lazy-loaded relationship `user.orders` inside a loop.
    """
    users = session.query(User).filter(User.is_active.is_(True)).order_by(User.id).all()

    if top_n <= 0:
        return {user.id: [] for user in users}

    result: Dict[int, List[Order]] = {}
    for user in users:
        # N+1 happens here: user.orders triggers a SELECT per user (lazy load)
        orders = sorted(user.orders, key=lambda order: (order.created_at, order.id), reverse=True)
        result[user.id] = orders[:top_n]

    return result
