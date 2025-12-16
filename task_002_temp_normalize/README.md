# TEMP ID Normalization Refactoring Benchmark

## Overview
This benchmark demonstrates **behavior-preserving refactoring** with the addition of new feature requirements. The task adds special handling for "TEMP" prefixed IDs while maintaining **exact backward compatibility** for all existing non-TEMP IDs.

## The Challenge

### Original Behavior
The `normalize_id` function converts any input string to a normalized ID format:
- Strip whitespace
- Convert to uppercase
- Collapse runs of non-alphanumeric characters to a single hyphen

Example: `"ABC_123"` → `"ABC-123"`

### New Requirement
Add special handling for IDs starting with "TEMP":
- **Preserve underscores** in TEMP IDs
- Convert other non-alphanumeric characters to hyphens (one-to-one mapping)
- **Must not break** any existing non-TEMP ID normalization

Example: `"temp_user_1"` → `"TEMP_USER_1"` (underscores preserved)

## Files Structure

### Core Implementation
- `repository_before/ids.py` - Original implementation (single regex approach)
- `repository_after/ids.py` - Refactored implementation (with helper function)

### Test Suite
- `tests/test_ids.py` - Original basic tests
- `tests/test_behavior_preservation.py` - Comprehensive behavioral tests
- `tests/test_code_quality_metrics.py` - Code quality assertions
- `tests/test_performance_improvement.py` - Performance benchmarks

### Evaluation & Metrics
- `evaluation/compare_metrics.py` - Metric comparison script
- `evaluation/pylint_score_before.txt` - Pylint score (before)
- `evaluation/pylint_score_after.txt` - Pylint score (after)
- `evaluation/radon_report_before.json` - Complexity metrics (before)
- `evaluation/radon_report_after.json` - Complexity metrics (after)

### Documentation
- `instances/todo_refactor_001.json` - Task specification
- `patches/todo_refactor_001.patch` - Git diff
- `trajectory/todo_refactor_001.md` - Implementation steps

### Infrastructure
- `Dockerfile` - Test environment
- `docker-compose.yml` - Orchestrates tests and metrics
- `requirements.txt` - Python dependencies

## Quick Start

### Run Tests Locally
```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_behavior_preservation.py -v
pytest tests/test_code_quality_metrics.py -v
pytest tests/test_performance_improvement.py -v
```

### Run with Docker Compose (Recommended)
```bash
# Run all tests and compare metrics
docker-compose up test-before test-after generate-metrics compare-metrics

# Just run tests
docker-compose up test-before test-after

# Just generate and compare metrics
docker-compose up generate-metrics compare-metrics
```

### Run Individual Containers
```bash
# Build image
docker build -t temp-normalize .

# Test before version
docker run --rm -e PYTHONPATH=/app/repository_before temp-normalize

# Test after version
docker run --rm -e PYTHONPATH=/app/repository_after temp-normalize
```

## Understanding the Results

### Expected Behavior

**Before Version (Original):**
- All behavioral tests pass (for non-TEMP IDs only)
- TEMP-specific tests FAIL (feature not implemented)
- Code quality varies

**After Version (Refactored):**
- All behavioral tests pass (both TEMP and non-TEMP)
- Code quality improved
- Helper function extracted for clarity

### 📊 Quality Improvements

The refactoring demonstrates:

1. **New Feature Addition** - TEMP ID handling without breaking existing behavior
2. **Code Organization** - Extracted helper function `_normalize_temp`
3. **Maintainability** - Clearer separation of concerns
4. **Test Coverage** - Comprehensive test suite covering edge cases

### Example Test Results
```
test-before:
  test_old_behavior_unchanged_abc_underscore_123 PASSED
  test_old_behavior_unchanged_spaces_collapse PASSED
  test_temp_preserves_underscores FAILED
  test_temp_mixed_symbols_example FAILED

test-after:
  test_old_behavior_unchanged_abc_underscore_123 PASSED
  test_old_behavior_unchanged_spaces_collapse PASSED
  test_temp_preserves_underscores PASSED
  test_temp_mixed_symbols_example PASSED
```

## Test Categories

### 1. Original Behavior Tests
Validates backward compatibility:
- Underscores convert to hyphens (non-TEMP)
- Multiple special characters collapse to one hyphen
- Case insensitive uppercasing
- Leading/trailing hyphen preservation

### 2. TEMP Behavior Tests
Validates new feature:
- Underscores preserved in TEMP IDs
- Other special chars become hyphens (one-to-one)
- TEMP prefix detection after strip/uppercase
- Mixed special character handling

### 3. Edge Cases
Tests boundary conditions:
- None/empty input
- Whitespace-only input
- Special characters only
- TEMP prefix detection edge cases

### 4. Code Quality Tests
Asserts quality standards:
- **Cyclomatic complexity** ≤ 8
- **Function length** ≤ 30 lines
- **Nesting depth** ≤ 4 levels
- Helper function extraction

### 5. Performance Tests
Ensures efficiency:
- Basic normalization < 100μs per call
- TEMP vs non-TEMP performance comparable
- Long string handling efficient

## Key Insights

### Backward Compatibility
Critical requirement: **Non-TEMP IDs must produce byte-for-byte identical output**.

Example requirements:
- `"ABC_123"` must still produce `"ABC-123"` (not `"ABC_123"`)
- `"abc   def"` must still produce `"ABC-DEF"` (collapse multiple spaces)
- Edge cases like `"___"` → `"-"` must be preserved

### TEMP Detection Logic
```python
# After strip and uppercase, check prefix
s = (raw or "").strip().upper()
if s.startswith("TEMP"):
    # Special handling
else:
    # Original behavior
```

This means:
- `"temp_id"` → uses TEMP behavior
- `"  TEMP_id"` → uses TEMP behavior (leading spaces stripped)
- `"!!!temp_id"` → uses original behavior (doesn't start with TEMP after strip)

## Metrics Generation

```bash
# Generate all metrics
docker-compose up generate-metrics

# This runs:
pylint repository_before/ids.py > evaluation/pylint_score_before.txt
pylint repository_after/ids.py > evaluation/pylint_score_after.txt
radon cc -j repository_before/ids.py > evaluation/radon_report_before.json
radon cc -j repository_after/ids.py > evaluation/radon_report_after.json
```

## Use Cases

This benchmark is useful for:
- **Feature addition with backward compatibility** - Adding new behavior without breaking existing
- **Refactoring with requirements** - Improving code while meeting new specs
- **Testing AI agents** - Validating ability to preserve behavior while adding features
- **Code quality assessment** - Measuring improvements in organization and complexity

## Requirements

- Python 3.11+
- pytest 8.3+
- pylint (for code quality analysis)
- radon (for complexity metrics)
- pytest-benchmark (for performance tests)
- Docker & Docker Compose (optional, recommended)

## Success Criteria

A successful refactoring must:
1. Pass all backward compatibility tests for non-TEMP IDs
2. Pass all new feature tests for TEMP IDs
3. Meet code quality thresholds
4. Maintain or improve performance
5. Have clear code organization with helper functions

## Contributing

When adding new test cases:
1. Test backward compatibility first - ensure non-TEMP behavior unchanged
2. Test new TEMP behavior separately
3. Document any edge cases discovered
4. Update metrics if code structure changes

## License

[Specify your license here]