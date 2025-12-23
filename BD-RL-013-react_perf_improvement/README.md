
## How Tests Select BEFORE vs AFTER 

### Run tests for BEFORE 

```
docker compose run --rm -e PYTHONPATH=/app/repository_before app npm test
```

### Run tests for AFTER

```bash
docker compose run --rm -e PYTHONPATH=/app/repository_after app npm test
```

## Run Evaluation

```bash
docker compose run --rm app node evaluation/evaluation.js
```

This produces `evaluation/results.json` summarizing key structural differences
between the two implementations.
