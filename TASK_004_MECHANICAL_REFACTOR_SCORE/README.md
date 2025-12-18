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

```bash
pip install -r requirements.txt
pytest -q
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

## Regenerate patch

From repo root:

```bash
git diff --no-index repository_before repository_after > patches/task_001.patch
```
