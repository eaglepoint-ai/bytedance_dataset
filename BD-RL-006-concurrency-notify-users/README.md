# Python Concurrency Dataset – Bounded Notifications Service

## Scenario

You are refactoring a mission-critical backend service in Python. The service
processes large lists of `user_ids` and calls a slow, blocking
`send_notification` function. The original implementation is purely
synchronous and becomes too slow for thousands of users.

The refactor must:

- Introduce real concurrency for `notify_users`.
- Enforce a **hard global limit** of at most **50 concurrent `send_notification` calls**
  across the entire process.
- Preserve the order of results so that `results[i]` corresponds to
  `user_ids[i]`.
- Avoid creating thousands of pending futures in memory.
- Use **only the Python Standard Library**.
- Handle failures carefully:
  - Normal errors become error strings at the correct index.
  - Fatal errors (e.g. `KeyboardInterrupt`) must propagate and not be swallowed.

## Files

- `repository_before/notify_service.py`
  - Original slow, synchronous implementation.
- `repository_after/notify_service.py`
  - Optimized concurrent implementation with a global bounded thread pool
    and ordered results.
- `tests/`
  - `test_behavior_basics.py`
    - API / behavior tests that should pass for both before & after
      (PASS_TO_PASS).
  - `test_concurrency_constraints.py`
    - Concurrency constraint tests that **must fail** on the original
      implementation and **pass** on the optimized one (FAIL_TO_PASS).
- `evaluation/evaluation.py`
  - Small helper that compares structural stats between the before/after
    implementations and writes `evaluation/results.json`.
- `trajectory/001_notify_users_concurrency_trajectory.md`
  - Notes describing the reasoning and steps of the refactor.

## Running Tests with Docker

Build image:

```bash
docker compose build
```

### Run tests against BEFORE implementation

```bash
docker compose run --rm -e PYTHONPATH=/app/repository_before app pytest -q
```

Expected behavior in a training/eval context:

- `test_behavior_basics.py` → ✅ PASS
- `test_concurrency_constraints.py` → ❌ FAIL
  (because the original code is synchronous and does not use bounded concurrency)

### Run tests against AFTER implementation

```bash
docker compose run --rm -e PYTHONPATH=/app/repository_after app pytest -q
```

Expected behavior:

- All tests in both files should ✅ PASS once the refactor is correct.

## Run Evaluation

```bash
docker compose run --rm app python evaluation/evaluation.py
```

This writes a short JSON summary to `evaluation/results.json` with line counts
and simple structural features.
