# Mechanical Refactor: calc_score

This dataset task contains a production-style Python function with intentional quirks.
The objective is **pure structural de-duplication** while preserving **bit-for-bit** runtime behavior.

## Folder layout

- `repository_before/` original implementation
- `repository_after/` mechanically refactored implementation
- `tests/` equivalence + invariants tests
- `patches/` diff between before/after
- `Dockerfile`, `docker-compose.yml`, `requirements.txt` for reproducible runs

## Run locally

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run all tests
```bash
# Run all tests (quiet mode)
pytest -q

# Run all tests (verbose mode)
pytest -v

# Run all tests (very verbose with detailed output)
pytest -vv
```

### Test individual versions

```bash
# Test only the BEFORE version
pytest tests/test_before.py -v

# Test only the AFTER version
pytest tests/test_after.py -v

# Test equivalence between before and after
pytest tests/test_calc_score_equivalence.py -v

# Test structural requirements (helper functions, line count, duplication)
pytest tests/test_structure.py -v
```

### Run specific test functions

```bash
# Test specific function
pytest tests/test_calc_score_equivalence.py::test_equivalence_on_handpicked_adversarial_inputs -v

# Run tests matching a pattern
pytest -k "equivalence" -v

# Show test collection without running
pytest --collect-only
```

## Run with Docker

### Quick Start - Run Everything (Recommended)
```bash
./run_all.sh
```
This single command will:
1. Build the Docker image
2. Run tests for both before and after implementations
3. Run equivalence tests
4. Run structural tests
5. Generate a comprehensive evaluation report

### Build image
```bash
docker build -t calc-score-refactor .
```

### Run tests (before – expected some failures)
```bash
docker run --rm -e PYTHONPATH=/app/repository_before calc-score-refactor
```

**Expected behavior:**
- Functional tests: ✅ PASS
- Structural tests (helper functions, duplication reduction): ❌ FAIL (expected - no improvements yet)

### Run tests (after – expected all pass)
```bash
docker run --rm -e PYTHONPATH=/app/repository_after calc-score-refactor
```

**Expected behavior:**
- Functional tests: ✅ PASS
- Structural tests (helper functions, duplication reduction): ✅ PASS (improvements present)

### Alternative: Using docker-compose

#### Run tests (before)
```bash
docker compose run --rm test-before
```

#### Run tests (after)
```bash
docker compose run --rm test-after
```

#### Run equivalence tests
```bash
docker compose run --rm test-equivalence
```

#### Run all tests
```bash
docker compose run --rm test-all
```

#### Run evaluation (compares both implementations)
```bash
docker compose run --rm app python evaluation/evaluation.py
```

#### Run evaluation with output file
```bash
docker compose run --rm app python evaluation/evaluation.py --output evaluation/report.json
```

## Regenerate patch

From repo root:

```bash
git diff --no-index repository_before repository_after > patches/task_001.patch
```
