#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash evaluation/run.sh tests before
#   bash evaluation/run.sh tests after
#   bash evaluation/run.sh bench before
#   bash evaluation/run.sh bench after
#
# Defaults:
#   MODE=tests
#   TARGET=after

MODE="${1:-tests}"     # tests | bench
TARGET="${2:-after}"   # before | after
IMAGE="deadlock-transfers"

# Compose project name is derived from folder; DB service is "db"
NETWORK="$(docker inspect task_003_deadlock_transfers-db-1 \
  --format '{{range $k,$v := .NetworkSettings.Networks}}{{println $k}}{{end}}' \
  | head -n1)"

DB_URL="postgresql://app:app@db:5432/appdb"

if [[ "$TARGET" == "before" ]]; then
  PY_PATH="/app/repository_before"
elif [[ "$TARGET" == "after" ]]; then
  PY_PATH="/app/repository_after"
else
  echo "ERROR: TARGET must be 'before' or 'after'"
  exit 1
fi

if [[ "$MODE" == "tests" ]]; then
  CMD="pytest -q"
elif [[ "$MODE" == "bench" ]]; then
  CMD="python evaluation/performance_benchmark.py"
else
  echo "ERROR: MODE must be 'tests' or 'bench'"
  exit 1
fi

echo "== RUN =="
echo "Mode:        $MODE"
echo "Target:      $TARGET"
echo "Image:       $IMAGE"
echo "Network:     $NETWORK"
echo "PYTHONPATH:  $PY_PATH"
echo ""

docker run --rm \
  --network "$NETWORK" \
  -e PYTHONPATH="$PY_PATH" \
  -e DATABASE_URL="$DB_URL" \
  "$IMAGE" $CMD
