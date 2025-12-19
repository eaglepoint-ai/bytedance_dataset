#!/bin/bash
set -e

echo "=========================================="
echo "N+1 Query Optimization - Full Evaluation"
echo "=========================================="
echo ""

# Step 1: Build Docker image
echo "Step 1: Building Docker image..."
docker build -t nplus1-orders . > /dev/null 2>&1
echo "✅ Docker image built successfully"
echo ""

# Step 2: Run tests for before implementation
echo "Step 2: Running tests for BEFORE implementation..."
if docker run --rm -e PYTHONPATH=/app/repository_before nplus1-orders; then
    echo "✅ BEFORE tests passed"
else
    echo "⚠️  BEFORE tests failed (expected for N+1 implementation)"
fi
echo ""

# Step 3: Run tests for after implementation
echo "Step 3: Running tests for AFTER implementation..."
if docker run --rm -e PYTHONPATH=/app/repository_after nplus1-orders; then
    echo "✅ AFTER tests passed"
else
    echo "❌ AFTER tests failed"
    exit 1
fi
echo ""

# Step 4: Run evaluation and generate report
echo "Step 4: Running evaluation and generating report..."
REPORT_DIR="evaluation/reports"
mkdir -p "$REPORT_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORT_DIR/evaluation_report_${TIMESTAMP}.json"

# Build docker-compose services first
docker compose build app > /dev/null 2>&1

docker compose run --rm app python evaluation/evaluation.py --output "$REPORT_FILE"

if [ -f "$REPORT_FILE" ]; then
    echo ""
    echo "✅ Evaluation report generated: $REPORT_FILE"
    echo ""
    echo "=========================================="
    echo "Full evaluation complete!"
    echo "=========================================="
    echo ""
    echo "Report location: $REPORT_FILE"
else
    echo "❌ Failed to generate evaluation report"
    exit 1
fi

