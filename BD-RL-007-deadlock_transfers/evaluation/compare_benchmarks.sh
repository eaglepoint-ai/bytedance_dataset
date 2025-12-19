#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash evaluation/compare_benchmarks.sh [docker_image_tag]
# Example:
#   bash evaluation/compare_benchmarks.sh deadlock-transfers
#
# If no image tag provided, defaults to "deadlock-transfers".

IMAGE="${1:-deadlock-transfers}"

# Compose network for this task (based on your container name task_003_deadlock_transfers-db-1)
NETWORK="task_003_deadlock_transfers_default"

# Connect to the compose DB service name "db" on the compose network
DB_URL="postgresql://app:app@db:5432/appdb"

BEFORE_OUT="evaluation/bench_before.txt"
AFTER_OUT="evaluation/bench_after.txt"

echo "== BEFORE (repository_before) =="
docker run --rm \
  --network "$NETWORK" \
  -e PYTHONPATH=/app/repository_before \
  -e DATABASE_URL="$DB_URL" \
  "$IMAGE" python evaluation/performance_benchmark.py | tee "$BEFORE_OUT"

echo ""
echo "== AFTER (repository_after) =="
docker run --rm \
  --network "$NETWORK" \
  -e PYTHONPATH=/app/repository_after \
  -e DATABASE_URL="$DB_URL" \
  "$IMAGE" python evaluation/performance_benchmark.py | tee "$AFTER_OUT"

echo ""
echo "== SUMMARY =="
python - <<'PY'
import re
from pathlib import Path

def parse(path: str):
    txt = Path(path).read_text(encoding="utf-8")

    m_avg = re.search(r"Avg time/run:\s*([0-9.]+)", txt)
    if not m_avg:
        raise SystemExit(f"ERROR: Could not find 'Avg time/run' in {path}")
    avg = float(m_avg.group(1))

    m_q = re.search(r"SQL statements(?: \(single run\))?:\s*(\d+)", txt)
    q = int(m_q.group(1)) if m_q else None

    return avg, q

b_avg, b_q = parse("evaluation/bench_before.txt")
a_avg, a_q = parse("evaluation/bench_after.txt")

speedup = (b_avg / a_avg) if a_avg else float("inf")
improvement_pct = (1 - (a_avg / b_avg)) * 100 if b_avg else 0.0

print(f"Before avg: {b_avg:.6f}s" + (f" | queries: {b_q}" if b_q is not None else ""))
print(f"After  avg: {a_avg:.6f}s" + (f" | queries: {a_q}" if a_q is not None else ""))

print(f"Speedup: {speedup:.2f}x")
print(f"Improvement: {improvement_pct:.2f}% faster")


PY

echo ""
echo "Saved outputs:"
echo "  - $BEFORE_OUT"
echo "  - $AFTER_OUT"
