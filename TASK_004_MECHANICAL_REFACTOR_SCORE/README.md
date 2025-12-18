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

```bash
docker build -t calc-score-refactor .
docker run --rm calc-score-refactor
```

Or:

```bash
docker compose run --rm tests
```

## Code quality evaluation

### Run pylint on before and after

```bash
# Evaluate BEFORE version
pylint repository_before/app/score.py --score=y

# Evaluate AFTER version
pylint repository_after/app/score.py --score=y

# Save reports to evaluation folder
pylint repository_before/app/score.py --output-format=text --score=y > evaluation/pylint_before.txt
pylint repository_after/app/score.py --output-format=text --score=y > evaluation/pylint_after.txt
```

### Expected improvement
- Before score: **6.30/10**
- After score: **7.45/10** (+18% improvement)

## Regenerate patch

From repo root:

```bash
git diff --no-index repository_before repository_after > patches/task_001.patch
```
