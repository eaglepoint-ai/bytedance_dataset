# Trajectory – SubscriptionManager Refactor (Teaching View)

- **Understand the legacy behavior**
  - Pricing rules are hard-coded inside `process_tier_change`.
  - Time is read directly using `datetime.now()`.
  - Single `tier` field is used for both billing status and feature access.
  - Downgrading `PREMIUM -> FREE` updates `tier` immediately, so perks are lost
    even though expiry is moved to the end of the month.
  - CORPORATE users are never expired once the tier is CORPORATE.

- **Introduce a testable clock**
  - Add a `Clock` protocol with a `now()` method.
  - Add a `SystemClock` implementation that wraps `datetime.now()`.
  - Make `SubscriptionManager` accept an optional `clock` argument and use
    `self._clock.now()` via a `_now()` helper.
  - Tests can inject a `FixedClock` instead of using `unittest.mock`.

- **Extract pricing rules into PriceCalculator + SubscriptionTier**
  - Create `PriceCalculator` with explicit `premium_price` and `corporate_price`.
  - Implement `price_for(current_tier, new_tier)` to compute upgrade cost.
  - Create `SubscriptionTier` that holds the current tier name and a reference
    to `PriceCalculator`.
  - Provide methods:
    - `price_for_upgrade(new_tier)`
    - `has_sufficient_funds(new_tier, balance)`
  - Update `process_tier_change` to use `SubscriptionTier` instead of hard-coded
    if/elif blocks for prices.

- **Implement downgrade grace (PREMIUM -> FREE)**
  - When downgrading from `PREMIUM` to `FREE`:
    - Set billing `self.tier` to `"FREE"`.
    - Set `self._grace_tier` to `"PREMIUM"`.
    - Compute `self._grace_expiry = end_of_month(now)` and align `self.expiry`.
    - Keep `self.status = "ACTIVE"`.
  - Add `_effective_tier(now)`:
    - Returns `self._grace_tier` while `now <= self._grace_expiry`.
    - Falls back to billing `self.tier` once grace ends.
  - Update `can_access_feature` to use `_effective_tier()` instead of raw `tier`.

- **Implement corporate 30-day grace window**
  - Add `_compute_status_with_grace(now)`:
    - For CORPORATE:
      - If `now > expiry + 30 days` → `"EXPIRED"`.
      - Else → `"ACTIVE"`.
    - For non-corporate tiers:
      - If `now > expiry` → `"EXPIRED"`.
      - Else → `"ACTIVE"`.
  - Call `_compute_status_with_grace` whenever expiry is updated for
    non-downgrade scenarios.

- **Preserve legacy API guarantees**
  - Keep `save_to_db(user_id, status, expiry)` exactly as-is.
  - Ensure `process_tier_change(new_tier)` still drives the transition.
  - Always call `save_to_db` at the end of a successful transition with the
    final `status` and `expiry` values.

- **Test strategy**
  - `test_behavior_basics.py`:
    - FREE users cannot access premium features (HD_VIDEO, AD_FREE).
    - EXPIRED users cannot access any features.
    - These tests pass on both before and after versions.
  - `test_refactor_constraints.py`:
    - Downgrade from PREMIUM to FREE keeps perks until month end.
    - CORPORATE users with expiry beyond 30 days become EXPIRED.
    - `SubscriptionManager` accepts a `clock` parameter and works with an
      injected `FixedClock`.
    - These tests fail on the legacy version and pass on the refactored version.
