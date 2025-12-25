"""Refactored SubscriptionManager with testable time and clearer business rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol, Optional


# LEGACY GLOBAL - DO NOT CHANGE SIGNATURE
def save_to_db(user_id, status, expiry):
    print(f"SAVING: User {user_id} is now {status} until {expiry}")


# ---------- Time abstraction (no unittest.mock needed) ----------

class Clock(Protocol):
    """Clock protocol to make time testable without unittest.mock."""

    def now(self) -> datetime:
        ...


class SystemClock:
    def now(self) -> datetime:  # pragma: no cover - thin wrapper
        return datetime.now()


# ---------- Pricing & Tier logic ----------

@dataclass
class PriceCalculator:
    """Encapsulates pricing rules for subscription tiers."""

    premium_price: int = 100
    corporate_price: int = 500

    def price_for(self, current_tier: str, new_tier: str) -> int:
        if new_tier == "PREMIUM":
            return self.premium_price
        if new_tier == "CORPORATE":
            return self.corporate_price
        return 0


@dataclass
class SubscriptionTier:
    """Represents the user's current tier and affordability logic."""

    name: str
    calculator: PriceCalculator

    def price_for_upgrade(self, new_tier: str) -> int:
        return self.calculator.price_for(self.name, new_tier)

    def has_sufficient_funds(self, new_tier: str, balance: int) -> bool:
        price = self.price_for_upgrade(new_tier)
        return balance >= price


def end_of_month(now: datetime) -> datetime:
    """Return a timestamp for the last day of the current month."""
    next_month = now.replace(day=28) + timedelta(days=4)
    last_day = next_month - timedelta(days=next_month.day)
    return last_day.replace(hour=23, minute=59, second=59, microsecond=999999)


# ---------- SubscriptionManager ----------

class SubscriptionManager:
    def __init__(
        self,
        user_id,
        tier,
        status,
        expiry,
        balance,
        clock: Optional[Clock] = None,
        calculator: Optional[PriceCalculator] = None,
    ):
        self.user_id = user_id
        # Billing tier: "FREE", "PREMIUM", "CORPORATE"
        self.tier = tier
        self.status = status  # "ACTIVE", "EXPIRED", "PENDING"
        self.expiry = expiry
        self.balance = balance

        self._clock: Clock = clock or SystemClock()
        self._calculator: PriceCalculator = calculator or PriceCalculator()

        # Downgrade grace fields (for PREMIUM -> FREE perks)
        self._grace_tier: Optional[str] = None
        self._grace_expiry: Optional[datetime] = None

    # ----- Helpers -----

    def _now(self) -> datetime:
        return self._clock.now()

    def _effective_tier(self, ref_time: Optional[datetime] = None) -> str:
        """
        Tier used for feature access.

        - During PREMIUM -> FREE downgrade, billing tier is FREE but
          perks stay PREMIUM until _grace_expiry.
        """
        now = ref_time or self._now()
        if self._grace_tier and self._grace_expiry and now <= self._grace_expiry:
            return self._grace_tier
        return self.tier

    def _compute_status_with_grace(self, now: datetime) -> str:
        """
        Compute status based on expiry and corporate 30-day grace rules.
        """
        if self.tier == "CORPORATE":
            if now > self.expiry + timedelta(days=30):
                return "EXPIRED"
            return "ACTIVE"
        if now > self.expiry:
            return "EXPIRED"
        return "ACTIVE"

    # ----- Public API -----

    def process_tier_change(self, new_tier):
        now = self._now()

        # Pricing & balance via SubscriptionTier + PriceCalculator
        tier_obj = SubscriptionTier(self.tier, self._calculator)
        if not tier_obj.has_sufficient_funds(new_tier, self.balance):
            raise Exception("Insufficient funds")
        price = tier_obj.price_for_upgrade(new_tier)

        # Transition logic
        if self.tier == "PREMIUM" and new_tier == "FREE":
            # Billing tier changes to FREE immediately
            self.tier = "FREE"
            # Keep PREMIUM perks until end of month
            self._grace_tier = "PREMIUM"
            self._grace_expiry = end_of_month(now)
            self.expiry = self._grace_expiry
            self.status = "ACTIVE"
        else:
            # Clear any downgrade grace
            self._grace_tier = None
            self._grace_expiry = None

            # For CORPORATE, apply 30-day grace based on existing expiry first
            self.tier = new_tier
            status = self._compute_status_with_grace(now)

            # If still ACTIVE under grace rules, extend by 30 days
            if status == "ACTIVE":
                self.expiry = now + timedelta(days=30)

            self.status = status

        # Finalization
        self.balance -= price
        save_to_db(self.user_id, self.status, self.expiry)

    def can_access_feature(self, feature_name):
        """
        Feature access logic using effective tier + status.
        """
        effective_tier = self._effective_tier()

        if effective_tier == "FREE" and feature_name in ["HD_VIDEO", "AD_FREE"]:
            return False
        if self.status == "EXPIRED":
            return False
        return True
