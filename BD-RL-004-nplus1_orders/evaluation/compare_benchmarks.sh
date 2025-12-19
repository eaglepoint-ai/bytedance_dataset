#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash evaluation/compare_benchmarks.sh [docker_image_tag]
# Example:
#   bash evaluation/compare_benchmarks.sh nplus1-orders
#
# If no image tag provided, defaults to "nplus1-orders".

IMAGE="${1:-nplus1-orders}"

BEFORE_OUT="evaluation/bench_before.txt"
AFTER_OUT="evaluation/bench_after.txt"

echo "== BEFORE (repository_before) =="
docker run --rm -e PYTHONPATH=/app/repository_before "$IMAGE" \
  python evaluation/performance_benchmark.py | tee "$BEFORE_OUT"

echo ""
echo "== AFTER (repository_after) =="
docker run --rm -e PYTHONPATH=/app/repository_after "$IMAGE" \
  python evaluation/performance_benchmark.py | tee "$AFTER_OUT"

echo ""
echo "== SUMMARY =="
python - <<'PY'
import re
from pathlib import Path

def parse(path: str):
    txt = Path(path).read_text(encoding="utf-8")

    # Required: Avg time/run
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

if b_q is not None and a_q is not None and a_q != 0:
    q_reduction = b_q / a_q
    q_improvement_pct = (1 - (a_q / b_q)) * 100 if b_q else 0.0
    print(f"Query reduction: {q_reduction:.2f}x")
    print(f"Query improvement: {q_improvement_pct:.2f}% fewer SQL statements")
else:
    print("Query reduction: N/A (benchmark did not print SQL statement counts)")
PY

echo ""
echo "Saved outputs:"
echo "  - $BEFORE_OUT"
echo "  - $AFTER_OUT"
