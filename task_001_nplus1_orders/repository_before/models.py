"""SQLAlchemy ORM models used by the dataset task."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Pylint commonly flags ORM models as "too few public methods"; that's expected.
# pylint: disable=too-few-public-methods


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""


class User(Base):
    """User model with an active flag and a relationship to orders."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Lazy relationship (default) => can trigger N+1 in loops if accessed repeatedly.
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")


class Order(Base):
    """Order model used for latest-order aggregation queries."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="orders")
