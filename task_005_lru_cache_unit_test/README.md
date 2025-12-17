# LRU Cache Testing Project

This project contains an LRU Cache implementation with comprehensive tests and meta-tests to verify test suite quality.

## Project Structure

```
├── repository_before/      # Code before adding tests (no test suite)
│   └── lru_cache.py
├── repository_after/       # Code after adding comprehensive tests
│   ├── lru_cache.py
│   └── tests/
│       └── test_lru_cache.py
├── tests/
│   ├── conftest.py
│   └── meta_test_lru_cache.py   # Meta-tests to verify test quality
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Quick Start with Docker Compose

### Available Commands

#### 1. Test repository_before (Expected to FAIL - no tests)
```bash
docker-compose run --rm test-before
```
This runs tests against `repository_before`. It will fail because there's no test suite.

#### 2. Test repository_after (Expected to PASS)
```bash
docker-compose run --rm test-after
```
This runs the full test suite against `repository_after`. All tests should pass.

#### 3. Run Meta-Tests (Verify Test Suite Quality)
```bash
docker-compose run --rm meta-test
```
Meta-tests verify that the test suite is strong enough to catch:
- Missing eviction logic
- Missing recency updates on `get()`
- Wrong eviction policy (MRU instead of LRU)

#### 4. Run Full Comparison Report
```bash
docker-compose run --rm compare
```
This runs all three test phases and provides a comprehensive comparison report:
1. Tests `repository_before` (should fail)
2. Tests `repository_after` (should pass)
3. Runs meta-tests (should pass)
4. Prints a summary comparison

## Building the Docker Image

```bash
docker-compose build
```

## Understanding the Output

### Successful Comparison
```
╔══════════════════════════════════════════════════════════════╗
║                    COMPARISON SUMMARY                        ║
╠══════════════════════════════════════════════════════════════╣
║ repository_before:  ❌ FAILED (or no tests)                 ║
║ repository_after:   ✅ PASSED                               ║
║ meta-tests:         ✅ PASSED (test suite is robust)        ║
╚══════════════════════════════════════════════════════════════╝

🎉 SUCCESS: The test suite correctly distinguishes between
   broken (before) and fixed (after) implementations!
```

## Meta-Tests Explained

The meta-tests in `tests/meta_test_lru_cache.py` use pytest's `pytester` plugin to verify that the test suite can catch intentionally broken LRU implementations:

| Broken Implementation | Expected Test Failures |
|-----------------------|------------------------|
| No eviction logic | 2 tests fail |
| No recency update on get | 1 test fails |
| Wrong eviction (MRU instead of LRU) | 1 test fails |
| Correct implementation | All tests pass |

## Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests on repository_after
PYTHONPATH=repository_after pytest repository_after/tests/ -v

# Run meta-tests
pytest tests/meta_test_lru_cache.py -v
```

## Requirements

- Docker & Docker Compose
- Python 3.11+ (for local development)
- pytest 8.3.3
- pytest-cov 5.0.0
