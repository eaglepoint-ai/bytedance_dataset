import pytest
from datetime import datetime

from calc_total import calc_total


def _dt(y, m, d):
    return datetime(y, m, d)


def test_basic_case_no_discounts():
    items = [{"price": 10, "qty": 2, "tax": 0.1}]
    user = {"vip": False, "country": "US", "created_at": "bad"}
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 22.00


def test_missing_qty_defaults_to_one():
    items = [{"price": 10, "tax": 0.0}]
    user = {"vip": False, "country": "US", "created_at": "bad"}
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 10.00


def test_invalid_qty_defaults_to_one():
    items = [{"price": 10, "qty": "abc", "tax": 0.0}]
    user = {"vip": False, "country": "US", "created_at": "bad"}
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 10.00


def test_negative_qty_becomes_zero():
    items = [{"price": 10, "qty": -3, "tax": 0.5}]
    user = {"vip": False, "country": "US", "created_at": "bad"}
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 0.00


def test_tax_none_treated_as_zero():
    items = [{"price": 10, "qty": 1, "tax": None}]
    user = {"vip": False, "country": "US", "created_at": "bad"}
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 10.00


def test_tax_invalid_treated_as_zero():
    items = [{"price": 10, "qty": 1, "tax": "nope"}]
    user = {"vip": False, "country": "US", "created_at": "bad"}
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 10.00


def test_price_invalid_treated_as_zero():
    items = [{"price": "nope", "qty": 5, "tax": 0.5}]
    user = {"vip": False, "country": "US", "created_at": "bad"}
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 0.00


def test_et_fee_applies_before_tax_is_added_tax_unchanged():
    items = [{"price": 100, "qty": 1, "tax": 0.1}]
    user = {"vip": False, "country": "ET", "created_at": "bad"}
    # subtotal=100, loyalty=0, fee => 102, tax_total uses base line (100*0.1=10), total=112
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 112.00


def test_vip_discount_applies_after_tax():
    items = [{"price": 100, "qty": 1, "tax": 0.1}]
    user = {"vip": True, "country": "US", "created_at": "bad"}
    # total before VIP = 110, after VIP 0.93 => 102.3
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 102.30


def test_loyalty_discount_applies_before_et_fee_and_tax_addition():
    items = [{"price": 100, "qty": 1, "tax": 0.1}]
    user = {"vip": False, "country": "ET", "created_at": "2022-12-15"}
    now = _dt(2025, 12, 15)  # 3 full years by day/365 logic
    # subtotal=100*(1-0.03)=97, then ET fee => 98.94, tax_total=10, total=108.94
    assert calc_total(items, user, now=now) == 108.94


def test_loyalty_discount_capped_at_five_percent():
    items = [{"price": 200, "qty": 1, "tax": 0.0}]
    user = {"vip": False, "country": "US", "created_at": "2010-01-01"}
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 190.00


def test_future_created_at_clamps_loyalty_to_zero():
    items = [{"price": 50, "qty": 2, "tax": 0.0}]
    user = {"vip": False, "country": "US", "created_at": "2026-01-01"}
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 100.00


def test_rounding_uses_python_round():
    items = [{"price": 2.675, "qty": 1, "tax": 0.0}]
    user = {"vip": False, "country": "US", "created_at": "bad"}
    now = _dt(2025, 12, 15)
    assert calc_total(items, user, now=now) == round(2.675, 2)


def test_catches_nonstandard_exceptions_in_price_float():
    class BadFloat:
        def __float__(self):
            raise RuntimeError("boom")

    items = [{"price": BadFloat(), "qty": 2, "tax": 0.1}]
    user = {"vip": False, "country": "US", "created_at": "bad"}
    # original code catches all exceptions and treats price as 0.0, so total is 0.0
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 0.00


def test_catches_nonstandard_exceptions_in_qty_int():
    class BadInt:
        def __int__(self):
            raise RuntimeError("boom")

    items = [{"price": 10, "qty": BadInt(), "tax": 0.1}]
    user = {"vip": False, "country": "US", "created_at": "bad"}
    # qty becomes 1, subtotal=10, tax=1, total=11
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 11.00


def test_catches_nonstandard_exceptions_in_tax_float():
    class BadTax:
        def __float__(self):
            raise RuntimeError("boom")

    items = [{"price": 10, "qty": 1, "tax": BadTax()}]
    user = {"vip": False, "country": "US", "created_at": "bad"}
    # tax becomes 0.0, total=10
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 10.00


def test_empty_items_returns_zero():
    items = []
    user = {"vip": True, "country": "ET", "created_at": "2010-01-01"}
    assert calc_total(items, user, now=_dt(2025, 12, 15)) == 0.00
