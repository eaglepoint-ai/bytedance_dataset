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
- Backend API tests (pytest)
- Database tests (pytest)
- Frontend unit tests (vitest)
- Frontend component tests (vitest + React Testing Library)
- Frontend integration tests (vitest)

## Project Structure

```
repository_after/meeting-scheduler/
├── api/          # FastAPI backend + PostgreSQL
├── auth/         # Node.js/TypeScript auth service
├── web/          # React/Vite frontend
tests/            # All test files
```

## Manual Testing

```bash
# Backend tests only
cd repository_after/meeting-scheduler
docker compose exec api pytest -v

# Frontend tests only
cd tests
npm install
npm test
```

