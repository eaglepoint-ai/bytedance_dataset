# Google Drive Access Logic - Performance Optimization

This project demonstrates optimizing a Google Drive-like permission system for querying accessible resources.

## Overview

- **`repository_before/`** - Naive implementation (loads all data, filters in Python)
- **`repository_after/`** - Optimized implementation (uses recursive CTEs, filters in database)

## Quick Start

### 1. Start the Database

```bash
docker compose up -d db
```

### 2. Run All Tests

```bash
docker compose run --rm app pytest -v tests/ -s
```

---

## Test Commands

### Run Tests Independently

#### Correctness Tests (repository_before)
Tests the access logic for correctness (ownership, permissions, inheritance):
```bash
docker compose run --rm app pytest -v tests/test_access_logic.py -s
```

#### Performance Tests (repository_before - Naive)
Tests performance of the naive implementation:
```bash
docker compose run --rm app pytest -v tests/test_performance_before.py -s
```

#### Performance Tests (repository_after - Optimized)
Tests performance of the optimized implementation:
```bash
docker compose run --rm app pytest -v tests/test_performance_after.py -s
```

### Run Comparison Tests

#### Compare Both Implementations
Runs correctness verification and performance comparison between before/after:
```bash
docker compose run --rm app pytest -v tests/test_comparison.py -s
```

---

## Individual Test Files

| File | Description | Command |
|------|-------------|---------|
| `test_access_logic.py` | Correctness tests for access rules | `pytest -v tests/test_access_logic.py -s` |
| `_test_performance_before.py` | Performance tests for repository_before | `pytest -v tests/test_performance_before.py -s` |
| `test_performance_after.py` | Performance tests for repository_after | `pytest -v tests/test_performance_after.py -s` |
| `test_comparison.py` | Side-by-side comparison of both | `pytest -v tests/test_comparison.py -s` |

---

## Seed the Database

To seed a large dataset for manual testing:

```bash
docker compose run --rm app python seed_db.py --users 50 --folders 200 --files-per-folder 100
```

---

## Architecture

### Schema (unchanged between versions)

```
User { id, email, createdAt }
Folder { id, name, ownerId, parentId, createdAt }
File { id, name, folderId, ownerId, createdAt }
Permission { id, userId, resourceType, resourceId, level, createdAt }
```

### Access Rules

1. **Ownership**: Users always see resources they own
2. **Direct Permission**: Explicit permission grants access
3. **Inheritance**: Folder permissions cascade to descendants and contained files
4. **Permission Levels**: owner > edit > comment > view

### Optimization Strategy

| Aspect | Before (Naive) | After (Optimized) |
|--------|---------------|-------------------|
| Data Loading | Loads ALL folders/files | Loads only accessible resources |
| Hierarchy Traversal | Python recursion | SQL Recursive CTE |
| Queries | Multiple queries + Python filtering | 2 queries with UNION |
| Complexity | O(n) where n = total resources | O(k) where k = accessible resources |

---

## Performance Results

Typical results on test dataset (100 folders, 5000 files):

| User | Before | After | Speedup |
|------|--------|-------|---------|
| heavy_user | ~30 ms | ~4 ms | **7x** |
| other_user_0 | ~25 ms | ~2 ms | **13x** |
| other_user_5 | ~25 ms | ~2 ms | **13x** |

---

## Development

### Run the App Locally

```bash
# Start PostgreSQL
docker compose up -d db

# Run before implementation
docker compose run --rm app python repository_before/app.py

# Run after implementation  
docker compose run --rm app python repository_after/app.py
```

### Access the Dashboard

```bash
curl http://localhost:8080/dashboard/heavy_user
```

---

## File Structure

```
├── repository_before/          # Naive implementation
│   ├── access_logic.py         # Python-based filtering
│   ├── app.py
│   ├── db.py
│   └── models.py
├── repository_after/           # Optimized implementation
│   ├── access_logic.py         # SQL CTE-based filtering
│   ├── app.py
│   ├── db.py
│   └── models.py
├── tests/
│   ├── utils.py                # Shared test utilities
│   ├── conftest.py             # Pytest fixtures
│   ├── test_access_logic.py    # Correctness tests
│   ├── test_performance_before.py     # Before performance tests
│   ├── test_performance_after.py # After performance tests
│   └── test_comparison.py      # Comparison tests
├── seed_db.py                  # Database seeding script
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

