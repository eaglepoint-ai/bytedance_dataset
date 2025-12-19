# Transaction Processor Meta-Testing Sandbox

This repo hosts a SWE-Bench–style scenario focused on keeping unit-test suites effective. Our current emphasis is the transaction rules engine in `repository_after/transaction_processor.py`, plus optional division-guard tests in `repository_after/mathoperation`.

Meta tests in `tests/` feed both correct and intentionally broken implementations into the *real* suites to verify they detect regressions.

## Project Layout

```
repository_after/
  transaction_processor.py
  tests/test_transaction_processor_rules.py
tests/
  test_transaction_processor_rules_meta.py
  resources/transaction_processor/*.py
Dockerfile, docker-compose.yml
```

## Running Tests Locally

```bash
# Meta suite (detects broken implementations)
pytest tests/test_transaction_processor_rules_meta.py

# Real unit tests
pytest repository_after/tests/test_transaction_processor_rules.py
```

If `tests/test_division_meta.py` exists in your copy, you can run it the same way.

## Running via Docker

```bash
docker compose run --rm tests
```