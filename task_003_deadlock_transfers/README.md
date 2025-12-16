
## Task_003_deadlock_transfers
*(Concurrent Database Deadlock & Locking Resolution Task)*

## Overview

This dataset instance evaluates a model’s ability to diagnose and fix a **real-world database concurrency bug**
in a PostgreSQL-backed money transfer system.

The original implementation works correctly in single-threaded execution but **fails intermittently under
concurrent access** due to improper row locking and transaction design. These failures manifest as deadlocks,
lock timeouts, or partial execution under load.

The goal is to refactor the implementation so that it is:

- Correct
- Deadlock-free
- Deterministic under concurrency
- Efficient at runtime

All fixes must preserve the original functional behavior and **must not modify the tests**.


### Problem Description

The system provides a function that transfers money between two accounts:

- Debit a source account
- Credit a destination account
- Ensure balances never go negative
- Apply both updates atomically

###  The Concurrency Bug

Under concurrent execution (multiple transfers running simultaneously):

- Each transfer touches **two rows** in the `accounts` table
- Different transactions acquire row locks in **different orders**
- This creates a **circular wait condition**
- PostgreSQL detects a deadlock or lock timeout
- Some transactions fail or roll back

These failures are:
- Non-deterministic
- Not reproducible in single-thread tests
- Common in production systems with transactional workloads


### What This Task Tests

This task specifically evaluates whether a model understands and correctly applies:

- Row-level locking using `SELECT … FOR UPDATE`
- Deadlock avoidance through **consistent global lock ordering**
- Correct transaction boundaries and atomicity
- Deterministic concurrency testing (thread barriers, no sleeps)
- Database-level concurrency reasoning (not Python locks or retries)

## Expected Fix (High-Level Requirements)

A correct solution must:

1. Execute the transfer inside **one explicit database transaction**
2. Lock **both account rows before reading balances**
3. Acquire locks in a **consistent global order** (e.g., smaller account ID first)
4. Perform debit and credit while locks are held
5. Commit atomically or roll back completely on error

The solution **must not**:
- Add sleeps or timing hacks
- Blindly retry failed transactions
- Rely on SERIALIZABLE isolation alone
- Modify existing tests

---

### Setup Instructions

#### Build the Docker Image

```bash
docker build -t deadlock-transfers .
````

#### Start PostgreSQL

```bash
docker compose up -d
```

Verify the database is running:

```bash
docker compose ps
```

---

### Running Tests

All tests are deterministic and rely on controlled concurrency.

### AFTER (Expected to Pass)

```bash
docker run --rm \
  --network task_003_deadlock_transfers_default \
  -e PYTHONPATH=/app/repository_after \
  -e DATABASE_URL=postgresql://app:app@db:5432/appdb \
  deadlock-transfers \
  pytest -q
```

### BEFORE (Expected to Fail or Be Flaky)

```bash
docker run --rm \
  --network task_003_deadlock_transfers_default \
  -e PYTHONPATH=/app/repository_before \
  -e DATABASE_URL=postgresql://app:app@db:5432/appdb \
  deadlock-transfers \
  pytest -q
```

## Performance & Stability Benchmark

The benchmark measures:
* Frequency of concurrency failures
* Runtime performance under contention
* SQL statement count per workload

### Run Benchmark Comparison

```bash
bash evaluation/compare_benchmarks.sh deadlock-transfers
```

### Output Files

* `evaluation/bench_before.txt`
* `evaluation/bench_after.txt`

Typical behavior:

* **BEFORE**: frequent deadlocks or failures, slower runtime
* **AFTER**: zero failures, significantly faster execution

## Unified Runner (Recommended)

A single entry-point script is provided:

```bash
bash evaluation/run.sh tests after
bash evaluation/run.sh tests before
bash evaluation/run.sh bench after
bash evaluation/run.sh bench before
```

This is the preferred way to run the task for automated evaluation.

---

### Static Analysis (Optional)

Run linting and complexity analysis:

```bash
bash evaluation/generate_reports.sh
```

Generated artifacts:

* `evaluation/pylint_score_before.txt`
* `evaluation/pylint_score_after.txt`
* `evaluation/radon_report_before.json`
* `evaluation/radon_report_after.json`



### Evaluation Criteria

A solution is considered **correct** if:

* All tests pass reliably
* No deadlocks occur under concurrent execution
* Final account balances are deterministic and correct
* No partial updates occur on failure
* Runtime performance improves under concurrency

