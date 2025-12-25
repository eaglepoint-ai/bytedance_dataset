# SubscriptionManager Refactor – Time Injection, Pricing, and Business Rules

This dataset describes a refactor of a legacy `SubscriptionManager` that manages
user access and billing tiers.

The refactor:

- Preserves the legacy `save_to_db(user_id, status, expiry)` function signature.
- Introduces a testable clock abstraction (no `unittest.mock` required).
- Encapsulates pricing logic with a `PriceCalculator` and `SubscriptionTier`.
- Correctly handles:
  - PREMIUM -> FREE downgrade grace (perks until end of month).
  - CORPORATE 30-day grace window after expiry.
- Keeps `process_tier_change` as the main entry point.

## Structure

- `repository_before/subscription_manager.py`
  - Original legacy implementation.
- `repository_after/subscription_manager.py`
  - Refactored implementation with injected clock and fixed business rules.
- `tests/`
  - `test_behavior_basics.py` – PASS_TO_PASS behavior tests.
  - `test_refactor_constraints.py` – FAIL_TO_PASS refactor tests.
- `evaluation/evaluation.py`
  - Structural comparison between before and after.
- `trajectory/001_subscription_manager_refactor_trajectory.md`
  - Textual trajectory of the refactor reasoning.

## Docker Usage

Build image:

```bash
docker compose build
```

Run tests against BEFORE:

```bash
docker compose run --rm -e PYTHONPATH=/app/repository_before app pytest -q
```

Run tests against AFTER:

```bash
docker compose run --rm -e PYTHONPATH=/app/repository_after app pytest -q
```

Run evaluation:

```bash
docker compose run --rm app python evaluation/evaluation.py
```
