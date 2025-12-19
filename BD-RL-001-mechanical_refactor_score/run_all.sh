#!/bin/bash
set -e

echo "=========================================="
echo "Mechanical Refactor - Full Evaluation"
echo "=========================================="
echo ""

# Step 1: Build Docker image
echo "Step 1: Building Docker image..."
docker build -t calc-score-refactor . > /dev/null 2>&1
echo "✅ Docker image built successfully"
echo ""

# Step 2: Run tests for before implementation
echo "Step 2: Running tests for BEFORE implementation..."
echo "Note: Structural tests (helper functions, duplication reduction) are expected to FAIL for before"
set +e  # Allow failures for this step - structural tests should fail
docker run --rm -e PYTHONPATH=/app/repository_before calc-score-refactor
BEFORE_EXIT_CODE=$?
set -e  # Re-enable exit on error

if [ $BEFORE_EXIT_CODE -eq 0 ]; then
    echo "✅ BEFORE tests passed (unexpected - structural tests should fail)"
elif [ $BEFORE_EXIT_CODE -eq 1 ]; then
    echo "✅ BEFORE tests completed (structural tests failed as expected)"
else
    echo "❌ BEFORE tests had unexpected error"
    exit 1
fi
echo ""

# Step 3: Run tests for after implementation
echo "Step 3: Running tests for AFTER implementation..."
if docker run --rm -e PYTHONPATH=/app/repository_after calc-score-refactor; then
    echo "✅ AFTER tests passed (including structural improvements)"
else
    echo "❌ AFTER tests failed"
    exit 1
fi
echo ""



# Step 6: Run evaluation and generate report
echo "Step 6: Running evaluation and generating report..."
REPORT_FILE="evaluation/report.json"

# Build docker-compose services first
docker compose build app > /dev/null 2>&1

docker compose run --rm app python evaluation/evaluation.py

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

