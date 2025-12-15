"""Service layer functions for order retrieval and aggregation."""

from __future__ import annotations

from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from repository_after.models import Order, User


def latest_orders_per_active_user(session: Session, top_n: int = 2) -> Dict[int, List[Order]]:
    """Return up to top_n latest orders per active user.

    Implementation notes:
    - 1 query to list active users
    - 1 query using a window function to fetch top-n orders per active user
    - deterministic ordering: created_at DESC, id DESC
    """
    active_user_ids = (
        session.execute(select(User.id).where(User.is_active.is_(True)).order_by(User.id))
        .scalars()
        .all()
    )

    if not active_user_ids:
        return {}

    if top_n <= 0:
        return {user_id: [] for user_id in active_user_ids}

    row_number = func.row_number().over(
        partition_by=Order.user_id,
        order_by=(Order.created_at.desc(), Order.id.desc()),
    ).label("row_number")

    ranked_sq = (
        select(
            Order.id.label("id"),
            Order.user_id.label("user_id"),
            Order.created_at.label("created_at"),
            Order.amount.label("amount"),
            row_number,
        )
        .join(User, User.id == Order.user_id)
        .where(User.is_active.is_(True))
        .subquery()
    )

    order_ranked = aliased(Order, ranked_sq)

    top_orders = (
        session.execute(
            select(order_ranked)
            .where(ranked_sq.c.row_number <= top_n)
            .order_by(
                order_ranked.user_id.asc(),
                order_ranked.created_at.desc(),
                order_ranked.id.desc(),
            )
        )
        .scalars()
        .all()
    )

    result: Dict[int, List[Order]] = {user_id: [] for user_id in active_user_ids}
    for order in top_orders:
        result[order.user_id].append(order)

    return result
