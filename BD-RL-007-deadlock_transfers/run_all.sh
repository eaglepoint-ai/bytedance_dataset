#!/bin/bash
set -e

echo "=========================================="
echo "Deadlock Transfers - Full Evaluation"
echo "=========================================="
echo ""

# Step 1: Build Docker image
echo "Step 1: Building Docker image..."
docker build -t deadlock-transfers . > /dev/null 2>&1
echo "✅ Docker image built successfully"
echo ""

# Step 2: Start PostgreSQL database
echo "Step 2: Starting PostgreSQL database..."
docker compose up -d db > /dev/null 2>&1

# Wait for database to be ready
echo "Waiting for database to be ready..."
timeout=30
counter=0
while ! docker compose exec -T db pg_isready -U app -d appdb > /dev/null 2>&1; do
    sleep 1
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        echo "❌ Database failed to start within $timeout seconds"
        exit 1
    fi
done
echo "✅ Database is ready"
echo ""

# Step 3: Run tests for before implementation
echo "Step 3: Running tests for BEFORE implementation..."
echo "Note: Tests are expected to FAIL due to deadlocks"
set +e  # Allow failures for this step - deadlocks are expected
docker compose run --rm test-before > /dev/null 2>&1
BEFORE_EXIT_CODE=$?
set -e  # Re-enable exit on error

if [ $BEFORE_EXIT_CODE -eq 0 ]; then
    echo "⚠️  BEFORE tests passed (unexpected - should fail due to deadlocks)"
elif [ $BEFORE_EXIT_CODE -eq 1 ]; then
    echo "✅ BEFORE tests completed (deadlocks occurred as expected)"
else
    echo "❌ BEFORE tests had unexpected error"
    exit 1
fi
echo ""

# Step 4: Run tests for after implementation
echo "Step 4: Running tests for AFTER implementation..."
if docker compose run --rm test-after; then
    echo "✅ AFTER tests passed (deadlocks eliminated)"
else
    echo "❌ AFTER tests failed"
    exit 1
fi
echo ""

# Step 5: Run evaluation and generate report
echo "Step 5: Running evaluation and generating report..."
REPORT_FILE="evaluation/report.json"

# Build docker-compose app service first
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

