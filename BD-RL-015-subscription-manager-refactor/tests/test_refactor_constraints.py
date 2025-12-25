import datetime

import pytest

import subscription_manager


class FixedClock:
    """Simple test clock for deterministic now()."""

    def __init__(self, fixed: datetime.datetime):
        self._fixed = fixed

    def now(self) -> datetime.datetime:
        return self._fixed


def test_premium_to_free_keeps_perks_until_month_end():
    """Downgrading PREMIUM -> FREE should keep perks until month end.

    - Billing tier must become FREE.
    - Feature access should still behave like PREMIUM during the grace window.
    """
    now = datetime.datetime(2025, 1, 10, 12, 0, 0)
    mgr = subscription_manager.SubscriptionManager(
        user_id=1,
        tier="PREMIUM",
        status="ACTIVE",
        expiry=now + datetime.timedelta(days=10),
        balance=1000,
    )

    mgr.process_tier_change("FREE")

    assert mgr.tier == "FREE"
    assert mgr.can_access_feature("HD_VIDEO") is True
    assert mgr.can_access_feature("AD_FREE") is True


def test_corporate_gets_30_day_grace_window():
    """CORPORATE users should get a 30-day grace window after expiry."""
    now = datetime.datetime(2025, 1, 31, 12, 0, 0)
    past_expiry = now - datetime.timedelta(days=40)

    mgr = subscription_manager.SubscriptionManager(
        user_id=2,
        tier="CORPORATE",
        status="ACTIVE",
        expiry=past_expiry,
        balance=1000,
    )

    mgr.process_tier_change("CORPORATE")

    assert mgr.status == "EXPIRED"


def test_supports_injected_clock_without_unittest_mock():
    """Refactored version must accept an injected clock object.

    - Before refactor: __init__ does not support a clock parameter -> TypeError.
    - After refactor: __init__ accepts 'clock' and uses it safely.
    """
    fixed_now = datetime.datetime(2030, 5, 1, 8, 0, 0)
    clock = FixedClock(fixed_now)

    try:
        mgr = subscription_manager.SubscriptionManager(
            user_id=3,
            tier="FREE",
            status="ACTIVE",
            expiry=fixed_now,
            balance=0,
            clock=clock,
        )
    except TypeError:
        pytest.fail("SubscriptionManager.__init__ must support 'clock' injection")

    mgr.process_tier_change("FREE")
