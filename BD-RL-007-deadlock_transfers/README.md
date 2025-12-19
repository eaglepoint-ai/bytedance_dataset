
## Task_003_deadlock_transfers
*(Concurrent Database Deadlock & Locking Resolution Task)*

## Overview

This task diagnose and fix a **real-world database concurrency bug**
in a PostgreSQL-backed money transfer system.

The original implementation works correctly in single-threaded execution but **fails intermittently under
concurrent access** due to improper row locking and transaction design. These failures manifest as deadlocks,
lock timeouts, or partial execution under load.

The goal is to refactor the implementation so that it is:

- Correct
- Deadlock-free
- Deterministic under concurrency
- Efficient at runtime

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

## How to Run

### Single Command (Recommended)

Run everything with a single command:

```bash
./run_all.sh
```

This will:
- Build the Docker image
- Start PostgreSQL database
- Run tests for before implementation (expected to fail due to deadlocks)
- Run tests for after implementation (expected to pass)
- Run evaluation and generate `evaluation/report.json`

### Manual Steps

#### Build the Docker Image

```bash
docker build -t deadlock-transfers .
```

#### Start PostgreSQL

```bash
docker compose up -d
```

Verify the database is running:

```bash
docker compose ps
```

#### Run Tests

**BEFORE (Expected to Fail due to Deadlocks):**

```bash
docker compose run --rm test-before
```

Or using docker run:

```bash
docker run --rm \
  --network bd-rl-007-deadlock_transfers_default \
  -e PYTHONPATH=/app/repository_before \
  -e DATABASE_URL=postgresql://app:app@db:5432/appdb \
  deadlock-transfers \
  pytest -q
```

**AFTER (Expected to Pass):**

```bash
docker compose run --rm test-after
```

Or using docker run:

```bash
docker run --rm \
  --network bd-rl-007-deadlock_transfers_default \
  -e PYTHONPATH=/app/repository_after \
  -e DATABASE_URL=postgresql://app:app@db:5432/appdb \
  deadlock-transfers \
  pytest -q
```

#### Run Evaluation

```bash
docker compose run --rm app python evaluation/evaluation.py
```

This will:
- Run tests for both before and after implementations
- Run performance benchmarks under concurrency
- Measure deadlock frequency and performance improvements
- Generate `evaluation/report.json`



### Evaluation Criteria

A solution is considered **correct** if:

* All tests pass reliably
* No deadlocks occur under concurrent execution
* Final account balances are deterministic and correct
* No partial updates occur on failure
* Runtime performance improves under concurrency

