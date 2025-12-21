# Task 001 – N+1 Query Optimization (Orders Aggregation)

This task demonstrates detection and elimination of an **N+1 SQL query pattern** when aggregating the latest orders per active user.  
It is structured to be **SWE-Bench compatible** and for **model training**.

---

## Problem Description

The original implementation retrieves active users and then accesses a lazy-loaded
`user.orders` relationship inside a loop, triggering **one SQL query per user** (N+1).

The optimized implementation:
- Uses a SQL window function
- Fetches top-N orders per user in one query
- Preserves deterministic ordering

---

## How to Run

### Build image
```bash
docker build -t nplus1-orders .
```

### Run tests (before – expected FAIL)
```bash
docker compose run --rm -e PYTHONPATH=/app/repository_before app pytest -q tests
```

### Run tests (after – expected PASS)
```bash
docker compose run --rm -e PYTHONPATH=/app/repository_before app pytest -q tests

```

### Run evaluation (compares both implementations)
```bash
docker compose run --rm app python evaluation/evaluation.py
```

This will:
- Evaluate both before and after implementations
- Count SQL queries to verify N+1 is eliminated
- Measure performance improvements
- Generate `evaluation/report.json`

---

## Patch
```bash
git diff --no-index repository_before repository_after > patches/task_001.patch
```

---

## Trajectory
See `trajectory/nplus_one_optimization.md`

---

## Outcome
- N+1 eliminated
- Performance improved
- Tests enforce regression safety
