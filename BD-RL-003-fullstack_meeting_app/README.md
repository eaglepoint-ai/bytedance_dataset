# Meeting Scheduler App - Fullstack Test Suite

Full-stack meeting scheduler application with authentication, booking system, and comprehensive test coverage (backend, frontend, integration).

## Quick Start with Docker

```bash
# Run the meeting scheduler app
cd repository_after/meeting-scheduler
docker compose up --build
```

**Services:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Auth Service: http://localhost:3001

## Run All Tests

```bash
# Run all tests (backend + frontend + integration)
./run-all-tests-docker.sh
```

**Test suites included:**
- Backend API tests (pytest) - HTTP integration tests against running services
- Database tests (pytest) - Model and data integrity tests
- Frontend unit tests (vitest) - Component rendering and logic
- Frontend component tests (vitest + React Testing Library) - User interactions
- Frontend integration tests (vitest) - Multi-component workflows

## Project Structure

```
repository_after/meeting-scheduler/
├── api/          # FastAPI backend + PostgreSQL
├── auth/         # Node.js/TypeScript auth service
├── web/          # React/Vite frontend
tests/            # All test files (root level)
├── frontend_*.test.*  # Frontend component/integration tests
├── test_backend_api.py     # Backend API tests
├── test_database.py        # Database model tests
└── vitest.config.ts   # Frontend test configuration
```

## Manual Testing

```bash
# Backend tests only (run locally against running services)
cd repository_after/meeting-scheduler
docker compose up -d  # Start services first
cd ../..
export API_BASE_URL=http://localhost:8000
export AUTH_BASE_URL=http://localhost:3001
pytest tests/test_backend_api.py tests/test_database.py -v

# Frontend tests only (in Docker)
cd repository_after/meeting-scheduler
docker compose run --rm test-frontend

# Frontend tests only (local development)
cd tests
npm install
npm test
```

