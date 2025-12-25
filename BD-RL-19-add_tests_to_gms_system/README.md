# Global Message Sequence (GMS) – Test Suite

This repository contains a small scenario to design and run a pytest-based test suite for a Global Message Sequence (GMS) generator. The GMS assigns every message in a distributed chat system a unique, incrementing `sequence_id`. To reduce database traffic, it leases IDs in blocks of 100 and serves them from local memory.

Primary target implementation: `repository_before/gms_sequence_generator.py`.
Reference test suite (after): `repository_after/tests/test_sequence_generator.py`.
Meta tests (root): `tests/test_sequence_generator_meta.py`.

## Problem Statement

> You are testing a Global Message Sequence (GMS). This system is designed to give every message sent in a distributed chat app a unique, incrementing sequence_id. It uses a Lease system to reduce database hits: it grabs a block of 100 IDs from the DB at once and hands them out from local memory. Generate a pytest test suite to check that the system is implemented correctly to handle a huge amount of load concurrently.

## What To Verify

- **Uniqueness:** No duplicate IDs across all threads.
- **Monotonicity:** IDs strictly increase globally as they are handed out.
- **Lease behavior:** A new lease is acquired only when the current lease is exhausted; each lease covers 100 IDs.
- **Concurrency safety:** Under heavy concurrent access, the generator remains correct and stable.
- **Efficiency:** Database calls are minimized (i.e., proportional to leases, not individual IDs).

## Project Layout

```
repository_before/
  gms_sequence_generator.py
repository_after/
  gms_sequence_generator.py
  tests/test_sequence_generator.py
instances/
  tests_to_gms_system.json
tests/
  test_sequence_generator_meta.py
pytest.ini
Dockerfile
docker-compose.yml
requirements.txt
```

The reference generator:

```
class SequenceGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.current_id = 0
        self.max_id_in_lease = 0

    def get_next_id(self):
        if self.current_id >= self.max_id_in_lease:
            new_start = self.db.get_next_block_start(block_size=100)
            self.current_id = new_start
            self.max_id_in_lease = new_start + 100
        self.current_id += 1
        return self.current_id
```

## Running Tests Locally

```bash
# 'After' reference suite
pytest -q repository_after/tests/test_sequence_generator.py

# Meta tests (copy the 'after' suite to a temp workspace and validate coverage)
pytest -q tests/test_sequence_generator_meta.py

# Only stress-marked tests
pytest -q -k stress
```

## Running via Docker

```bash
# Run meta tests inside container
docker compose run --rm tests

# Generate a single JSON report via benchmark runner
docker compose run --rm benchmark
```

The benchmark writes `evaluation/report-<YYYYMMDD-HHMMSS>-<RUNID>.json` with:
- Environment info
- Pytest command and summary
- Detailed per-test outcomes and failure messages
- Aggregated totals (`totalTests`, `totalPasses`, `totalFailures`)

### Requirements
- Python 3.12+
- `pytest`, `pytest-json-report` (installed via `requirements.txt`).

### Generate a report locally (no Docker)
```bash
.venv/bin/python \
  evaluation/performance_benchmark.py --tests tests/test_sequence_generator_meta.py
# Output: evaluation/report-<YYYYMMDD-HHMMSS>-<RUNID>.json
```
