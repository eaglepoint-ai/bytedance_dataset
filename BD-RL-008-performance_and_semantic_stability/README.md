# Performance and Semantic Stability Refactoring: format_ids

## Overview
This benchmark demonstrates **performance-oriented refactoring** while maintaining **exact semantic stability**. The refactoring optimizes the `format_ids` function by eliminating repeated regex compilation overhead while ensuring byte-for-byte identical output.

## The Challenge

### Original Implementation Issues
The `format_ids` function has a critical performance bottleneck:
- **Repeated regex compilation**: Calling `re.sub(r'[^A-Z0-9]+', '-', s)` inside a loop compiles the regex pattern on every iteration
- **O(n) compilation overhead**: With n IDs, the regex is compiled n times unnecessarily
- **Suboptimal variable naming**: Code clarity could be improved

### Refactoring Goals
1. **Eliminate regex recompilation** - Pre-compile pattern at module level
2. **Maintain semantic stability** - Output must be byte-for-byte identical
3. **Improve code quality** - Better variable names and documentation
4. **No breaking changes** - Function signature unchanged

## Files Structure

### Core Implementation
- `repository_before/format_ids.py` - Original implementation (regex compiled per iteration)
- `repository_after/format_ids.py` - Refactored implementation (pre-compiled regex)

### Test Suite
- `tests/test_behavior_preservation.py` - 34 tests ensuring semantic stability
- `tests/test_code_quality_metrics.py` - 6 code quality assertions (1 FAIL_TO_PASS)
- `tests/test_performance_improvement.py` - 8 performance benchmarks (1 FAIL_TO_PASS)
- `tests/test_optimization_quality.py` - 3 optimization validation tests (all FAIL_TO_PASS)

### Evaluation & Metrics
- `evaluation/evaluate.py` - Comprehensive evaluation script
- `evaluation/YYYY-MM-DD/HH-MM-SS/report.json` - Generated evaluation reports

### Documentation
- `instances/task_003.json` - Task specification and requirements
- `patches/task_003.patch` - Git diff showing exact changes
- `trajectory/task_003.md` - Implementation steps and rationale

### Infrastructure
- `Dockerfile` - Test environment with pylint, radon, pytest-benchmark
- `docker-compose.yml` - Single service orchestration
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
pytest tests/test_performance_improvement.py -v
```

### Run with Docker Compose (Recommended)
```bash
# Run evaluation (tests + metrics + comparison)
docker compose run --rm app python evaluation/evaluate.py

# Run tests for 'before' version only
docker compose run --rm -e PYTHONPATH=/app/repository_before app pytest -q

# Run tests for 'after' version only
docker compose run --rm -e PYTHONPATH=/app/repository_after app pytest -q

# Run specific test category
docker compose run --rm -e PYTHONPATH=/app/repository_after app python evaluation/evaluate.py --test-type performance_improvement

# Generate evaluation report with parameters
docker compose run --rm app python evaluation/evaluate.py --param version=1.0 --param environment=production
```

### Run Individual Containers
```bash
# Build image
docker build -t format-ids .

# Test before version
docker run --rm -e PYTHONPATH=/app/repository_before format-ids

# Test after version
docker run --rm -e PYTHONPATH=/app/repository_after format-ids
```

## Evaluation Reports

The `evaluation/evaluate.py` script generates comprehensive reports in JSON format at `evaluation/YYYY-MM-DD/HH-MM-SS/report.json`. Each report contains:

- **`run_id`**: Unique identifier for the evaluation run
- **`started_at`** / **`finished_at`**: Timestamps with duration
- **`parameters`**: Custom parameters passed to the evaluation
- **`environment`**: System information (Python version, platform, etc.)
- **`metrics`**: Code quality metrics (pylint scores, complexity, LOC)
- **`before`** / **`after`**: Test results and metrics for each version
- **`comparison`**: Detailed comparison between before/after versions

### Example Report Structure
```json
{
  "run_id": "95d1a51c-4129-48f7-aef7-2240c0a71d9c",
  "started_at": "2025-12-19T16:13:10.628048",
  "finished_at": "2025-12-19T16:13:10.678757",
  "duration_seconds": 0.050709,
  "parameters": {"version": "1.0"},
  "environment": {...},
  "metrics": {
    "before": {"lines_of_code": 14, "has_precompiled_regex": false},
    "after": {"lines_of_code": 27, "has_precompiled_regex": true}
  },
  "before": {"tests": {...}, "metrics": {...}},
  "after": {"tests": {...}, "metrics": {...}},
  "comparison": {
    "test_improvements": {...},
    "metric_improvements": {...},
    "summary": {...}
  }
}
```

## Expected Results

### Before Version (Original):
- **42 tests PASS** (semantic correctness maintained)
- **5 tests FAIL** (demonstrates optimization gaps):
  - `test_regex_precompilation` - No pre-compiled pattern detected
  - `test_repeated_calls_performance` - Exceeds 120μs per call threshold
  - `test_no_inline_regex_compilation` - Has inline `re.sub()` in loop
  - `test_has_module_level_compiled_pattern` - Missing module-level pattern
  - `test_documentation_mentions_optimization` - No optimization docs

### After Version (Optimized):
- **All 47 tests PASS** (100% success rate)
- **5 FAIL_TO_PASS tests now pass** (proves optimization worked)
- **Faster performance** (30-50% improvement with pre-compiled regex)
- **Improved code quality** (better names, documentation, maintainability)

### Performance Improvements
Expected improvements with the refactored version:
- **Small batches (100 IDs)**: 20-30% faster
- **Large batches (1000+ IDs)**: 40-50% faster
- **Repeated calls**: Consistent performance, no degradation
- **Memory usage**: Similar or slightly better

## Test Categories

### 1. Behavior Preservation Tests (34 tests)
Validates exact semantic stability across:

**Basic Behavior**
- Simple ID formatting
- Empty lists and single IDs
- Uppercase conversion

**None Handling**
- None values skipped
- All None values
- None at various positions

**Whitespace Handling**
- Leading/trailing whitespace removal
- Internal whitespace becomes hyphen
- Whitespace-only strings

**Special Character Handling**
- Single special characters → hyphen
- Multiple consecutive → single hyphen
- Mixed special characters
- Leading/trailing special chars

**Order and Duplicates**
- Order preserved
- Duplicates preserved
- Duplicates after formatting

**Edge Cases**
- Empty strings
- Single characters
- Numbers only
- Alphanumeric mix
- Unicode characters
- Very long IDs (1000+ chars)
- Large batches (1000+ IDs)

**Complex Scenarios**
- Mixed edge cases
- Realistic ID strings
- Database-style keys

### 2. Performance Tests (8 tests)
Measures and validates improvements:
- **Basic performance**: 300 ID benchmark
- **Large batch**: 1000 ID throughput test
- **Repeated calls**: 1000 iterations timing **FAIL_TO_PASS** (strict <120μs threshold)
- **Special chars**: Heavy regex workload
- **Mixed workload**: Realistic usage patterns
- **Memory efficiency**: No excessive allocations
- **Scalability**: Linear performance scaling
- **Regex compilation overhead**: Compilation cost measurement

### 3. Code Quality Tests (6 tests)
Asserts quality improvements:
- **Complexity**: Cyclomatic complexity ≤ 5
- **Length**: Function ≤ 30 lines
- **Nesting**: Max depth ≤ 3
- **Regex optimization**: Pre-compiled pattern detected **FAIL_TO_PASS**
- **Signature stability**: No API changes
- **Module imports**: Proper re module usage

### 4. Optimization Quality Tests (3 tests) **All FAIL_TO_PASS**
Validates the optimization was applied correctly:
- **No inline compilation**: Source code doesn't have `re.sub()` in loop
- **Module-level pattern**: Pre-compiled `_NON_ALNUM_PATTERN` exists
- **Documentation quality**: Docstring mentions performance optimization

## Key Technical Details

### Behavior Specification

**Input Behaviors:**
- None values → skipped (not in output)
- `"  abc  "` → `"ABC"` (whitespace stripped, uppercased)
- `"a_b_c"` → `"A-B-C"` (special chars → hyphens)
- `"a___b"` → `"A-B"` (multiple special chars collapse)
- Order and duplicates always preserved

### Performance Optimization

**Before (Inefficient)**
```python
def format_ids(ids):
    out = []
    for x in ids:
        if x is None:
            continue
        s = x.strip().upper()
        s = re.sub(r"[^A-Z0-9]+", "-", s)
        out.append(s)
    return out
```

**After (Optimized)**
```python
_NON_ALNUM_PATTERN = re.compile(r'[^A-Z0-9]+')

def format_ids(ids):
    result = []
    for id_val in ids:
        if id_val is None:
            continue
        cleaned = id_val.strip().upper()
        cleaned = _NON_ALNUM_PATTERN.sub('-', cleaned)
        result.append(cleaned)
    return result
```

### Why This Matters

**Regex Compilation Cost**
- Compiling a regex pattern has overhead
- In a loop with 1000 iterations, the pattern is compiled 1000 times
- Pre-compiling eliminates 999 unnecessary compilations
- Performance gain increases with batch size

## Success Criteria

A successful refactoring achieves:
1. **Semantic stability preserved** - All 42 PASS_TO_PASS tests pass in both versions
2. **Optimization validated** - All 5 FAIL_TO_PASS tests fail before, pass after
3. **Measurable performance gain** - 30-50% faster execution at scale
4. **Code quality improvement** - Better complexity, clarity, documentation
5. **No breaking changes** - Same function signature and behavior
6. **Maintainability** - Clearer code with better variable names

### Test Summary
- **Total tests**: 47
- **PASS_TO_PASS**: 42 tests (semantic stability)
- **FAIL_TO_PASS**: 5 tests (optimization proof)

## Metrics

### Performance Metrics
- Execution time (ms, μs)
- Throughput (IDs/second)
- Per-call overhead
- Scalability factor

### Quality Metrics
- Pylint score
- Cyclomatic complexity
- Function length (LOC)
- Documentation quality

## Requirements

- Python 3.11+
- pytest 8.3+ (testing framework)
- pylint (code quality analysis)
- radon (complexity metrics)
- pytest-benchmark (performance tests)
- Docker & Docker Compose (optional, recommended)

## Use Cases

This benchmark demonstrates:
- **Performance optimization** without changing behavior
- **Regex optimization** techniques
- **Test-driven refactoring** methodology
- **Semantic stability** validation
- **Performance benchmarking** best practices

Useful for:
- Teaching refactoring principles
- Evaluating AI coding agents
- Training on performance optimization
- Understanding regex compilation costs
- Demonstrating test-driven development

## Contributing

When making changes:
1. Ensure all behavioral tests pass in both versions
2. Add performance benchmarks for new scenarios
3. Document optimization techniques used
4. Update metrics if code changes
5. Maintain backward compatibility

## License

[Specify your license here]
