import datetime

import subscription_manager


def test_free_cannot_access_premium_features():
    now = datetime.datetime.now()
    mgr = subscription_manager.SubscriptionManager(
        user_id=1,
        tier="FREE",
        status="ACTIVE",
        expiry=now + datetime.timedelta(days=10),
        balance=0,
    )

    assert mgr.can_access_feature("HD_VIDEO") is False
    assert mgr.can_access_feature("AD_FREE") is False
    assert mgr.can_access_feature("BASIC_ARTICLE") is True


def test_expired_cannot_access_any_feature():
    now = datetime.datetime.now()
    mgr = subscription_manager.SubscriptionManager(
        user_id=2,
        tier="PREMIUM",
        status="EXPIRED",
        expiry=now - datetime.timedelta(days=1),
        balance=0,
    )

    assert mgr.can_access_feature("HD_VIDEO") is False
    assert mgr.can_access_feature("AD_FREE") is False
    assert mgr.can_access_feature("BASIC_ARTICLE") is False
