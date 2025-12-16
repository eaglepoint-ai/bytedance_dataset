# Behavior-Preserving Refactoring Benchmark: calc_total

## Overview
This benchmark demonstrates and validates **behavior-preserving refactoring** of a Python function. The test suite ensures that while code quality improves through refactoring, the exact behavior (including edge cases and quirks) remains unchanged.

## Files Structure

### Core Implementation
- `repository_before/calc_total.py` - Original implementation (baseline)
- `repository_after/calc_total.py` - Refactored implementation (improved)

### Test Suite
- `tests/test_behavior_preservation.py` - Comprehensive behavioral tests that lock in exact behavior
- `tests/test_code_quality_metrics.py` - Quality assertions (complexity, length, nesting)
- `tests/test_performance_improvement.py` - Performance benchmarks

### Evaluation & Metrics
- `evaluation/compare_metrics.py` - Script to compare quality improvements
- `evaluation/pylint_score_before.txt` - Pylint analysis of original code
- `evaluation/pylint_score_after.txt` - Pylint analysis of refactored code
- `evaluation/radon_report_before.json` - Complexity metrics (before)
- `evaluation/radon_report_after.json` - Complexity metrics (after)

### Task Documentation
- `instances/todo_refactor_001.json` - Task specification
- `patches/todo_refactor_001.patch` - Git diff of changes
- `trajectory/todo_refactor_001.md` - Refactoring decision log

### Infrastructure
- `Dockerfile` - Test environment setup
- `docker-compose.yml` - Orchestrates tests and metrics
- `requirements.txt` - Python dependencies

## Quick Start

### Run Tests Locally
```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run behavioral tests only
pytest tests/test_behavior_preservation.py -v

# Run all tests including quality checks
pytest tests/ -v
```

### Run with Docker Compose (Recommended)
```bash
# Run all tests and see quality comparison
docker-compose up test-before test-after

# Generate metrics and compare
docker-compose up generate-metrics compare-metrics

# Full workflow: tests + metrics + comparison
docker-compose up
```

### Run Individual Containers
```bash
# Build image
docker build -t calc-total .

# Test before version
docker run --rm -e PYTHONPATH=/app/repository_before calc-total

# Test after version
docker run --rm -e PYTHONPATH=/app/repository_after calc-total
```

## Understanding the Results

### Expected Behavior

**Before Version (Original):**
- All behavioral tests pass
- **Complexity test FAILS** (complexity = 16, threshold = 15)
- Total: 22/23 tests pass

**After Version (Refactored):**
- All behavioral tests pass
- **Complexity test PASSES** (complexity ≤ 15)
- Total: 23/23 tests pass

### Quality Improvements Demonstrated

The refactoring improves code quality while preserving behavior:

1. **Behavioral Equivalence** - All 18 behavioral tests pass in both versions
2. **Reduced Complexity** - Cyclomatic complexity reduced from 16 to ≤15
3. **Better Maintainability** - Improved pylint scores
4. **Preserved Performance** - Performance tests pass in both versions

### Example Output
```
test-before: FAILED test_function_complexity (16 > 15)
test-after:  PASSED test_function_complexity (complexity ≤ 15)

Metrics Comparison:
  Pylint:     Before: 7.5/10 | After: 8.8/10 (+17% improvement)
  Complexity: Before: 16     | After: 12     (-25% reduction)
```

## Test Categories

### 1. Behavior Preservation Tests
Validates exact behavior including:
- Default value handling (missing quantity → 1)
- Invalid input handling (negative quantity → 0)
- Tax and discount application order
- Loyalty discount calculations with date logic
- Exception handling for non-standard exceptions
- Edge cases (empty lists, future dates, etc.)

### 2. Code Quality Tests
Asserts quality thresholds:
- **Cyclomatic complexity** ≤ 15 (decision points)
- **Function length** ≤ 100 non-empty lines
- **Try-except nesting** ≤ 3 levels deep
- **Module structure** has callable public functions

### 3. Performance Tests
Ensures reasonable execution times:
- Simple calculations complete in < 100ms
- Module imports and function discovery work correctly
- No performance regression from refactoring

## Key Testing Principle

> **Tests that fail on `before` but pass on `after` prove the refactoring improved quality while preserving behavior.**

The complexity test is **intentionally designed** to:
- Fail on the original (complex) code
- Pass on the refactored (simplified) code

This validates that the refactoring achieved its goal.

## Metrics Generation

The `generate-metrics` service automatically runs:

```bash
# Pylint analysis
pylint repository_before/calc_total.py > evaluation/pylint_score_before.txt
pylint repository_after/calc_total.py > evaluation/pylint_score_after.txt

# Radon complexity analysis
radon cc -j repository_before/calc_total.py > evaluation/radon_report_before.json
radon cc -j repository_after/calc_total.py > evaluation/radon_report_after.json
```

## Use Cases

This benchmark is useful for:
- **Evaluating AI agents** that perform code refactoring
- **Teaching refactoring principles** with concrete examples
- **Demonstrating test-driven refactoring** workflows
- **Benchmarking code quality tools** and metrics
- **Training models** on behavior-preserving transformations

## Requirements

- Python 3.11+
- pytest 8.3+
- pylint (for linting)
- radon (for complexity metrics)
- pytest-benchmark (for performance tests)
- Docker & Docker Compose (optional, recommended)

## Contributing

When adding new test cases:
1. Ensure they pass in **both** `before` and `after` for behavior preservation
2. Add quality assertions that show improvement (fail before, pass after)
3. Document any quirky behavior being preserved
4. Update metrics if code structure changes

## License

[Specify your license here]

## References

- [Cyclomatic Complexity](https://en.wikipedia.org/wiki/Cyclomatic_complexity)
- [Behavior-Preserving Refactoring](https://refactoring.com/)
- [Test-Driven Development](https://martinfowler.com/bliki/TestDrivenDevelopment.html)