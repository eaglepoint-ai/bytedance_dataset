#!/bin/bash
# Run all tests (backend locally + frontend in Docker)

set -e  # Exit on error

echo "======================================"
echo "Running ALL Tests"
echo "======================================"
echo ""
echo "Note: Backend tests run locally (cookie auth)"
echo "      Frontend tests run in Docker (MSW mocks)"
echo ""

# Navigate to docker-compose directory
cd "$(dirname "$0")/repository_after/meeting-scheduler"

# Start services
echo "📦 Starting Docker services..."
docker compose up -d
echo "✅ Services started"
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10
echo "✅ Services ready"
echo ""

# Run backend tests LOCALLY
echo "======================================"
echo "🐍 Running Backend Tests (LOCAL)"
echo "======================================"
cd ../..
export API_BASE_URL=http://localhost:8000
export AUTH_BASE_URL=http://localhost:3001
pytest tests/test_backend_api.py tests/test_database.py -v
BACKEND_EXIT=$?
echo ""

# Run frontend tests in Docker
echo "======================================"
echo "⚛️  Running Frontend Tests (DOCKER)"
echo "======================================"
cd repository_after/meeting-scheduler
docker compose run --rm test-frontend
FRONTEND_EXIT=$?
echo ""

# Summary
echo "======================================"
echo "📊 Test Summary"
echo "======================================"

if [ $BACKEND_EXIT -eq 0 ]; then
    echo "✅ Backend Tests: PASSED"
else
    echo "❌ Backend Tests: FAILED (exit code: $BACKEND_EXIT)"
fi

if [ $FRONTEND_EXIT -eq 0 ]; then
    echo "✅ Frontend Tests: PASSED"
else
    echo "❌ Frontend Tests: FAILED (exit code: $FRONTEND_EXIT)"
fi

echo ""

# Stop services
echo "🛑 Stopping services..."
docker compose down
echo "✅ Services stopped"
echo ""

# Exit with error if any tests failed
if [ $BACKEND_EXIT -ne 0 ] || [ $FRONTEND_EXIT -ne 0 ]; then
    echo "❌ Some tests failed!"
    exit 1
else
    echo "✅ All tests passed!"
    exit 0
fi

