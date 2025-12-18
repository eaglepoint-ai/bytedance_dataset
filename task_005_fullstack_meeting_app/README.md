# Task 005: Architecture Refactoring Project

This repository contains a refactoring task that transforms a flat Python module layout into a layered architecture, plus a complete meeting scheduler application.

## Project Structure

```
task_005/
├── repository_before/     # 
├── repository_after/      # Refactored layered structure
│   ├── app/              # Layered architecture
│   └── meeting-scheduler/ # Complete meeting scheduler application
├── tests/                # Test suite for refactoring validation
├── instances/            # Benchmark dataset configuration
├── trajectory/          # Build trajectory documentation
└── Dockerfile           # Docker configuration for tests
```

---

## Option 1: Running the Refactoring Tests

These tests validate that the refactoring from `repository_before` to `repository_after` maintains functionality.

### Prerequisites
- Python 3.11+
- PostgreSQL database running (for database connection tests)
- Docker (optional, for containerized testing)

### Method 1: Using Docker (Recommended)

```bash
# Build in Docker
docker build -t task_005_test .
```

### Method 2: Local Python Environment

```bash
# Install dependencies
pip install psycopg[binary] pytest

# Set PYTHONPATH to repository_before for before tests
export PYTHONPATH=$(pwd)/repository_before
pytest tests/ -v

# Set PYTHONPATH to repository_after for after tests
export PYTHONPATH=$(pwd)/repository_after
pytest tests/ -v
```

### Test Files
- `test_public_api.py` - Verifies public API (`transfer_funds`) is accessible
- `test_imports.py` - Validates layered architecture imports work
- `test_filesystem_structure.py` - Checks directory structure matches expected layout

---

## Option 2: Running the Meeting Scheduler Application

A complete full-stack meeting scheduler application is located in `repository_after/meeting-scheduler/`.

### Quick Start

```bash
# Navigate to the meeting scheduler directory
cd repository_after/meeting-scheduler

# Start all services with Docker Compose
docker compose up --build
```

### Services

Once running, the following services will be available:

- **Web Frontend**: http://localhost:5173
- **Auth Service**: http://localhost:3001
- **API Backend**: http://localhost:8000
- **API Health Check**: http://localhost:8000/health

### Architecture

- **Auth Service** (Node/TypeScript) - Authentication with email/password, roles (user/consultant)
- **API** (FastAPI) - Backend API with PostgreSQL, slot exclusivity constraints
- **Web** (Vite + React) - Frontend UI with React Router
- **E2E Tests** (Playwright) - Browser-based end-to-end tests

### Development Workflow

#### 1. Create a Consultant User (Dev Mode)

```bash
curl -X POST http://localhost:3001/api/auth/seed-consultant | jq
```

#### 2. Set Consultant Role

```bash
curl -X POST http://localhost:3001/api/auth/test/set-role \
  -H 'Content-Type: application/json' \
  -d '{"email":"consultant@example.com","role":"consultant"}' | jq
```

#### 3. Login as Consultant

- Email: `consultant@example.com`
- Password: `consultant123!`

#### 4. Create Time Slots

Navigate to `/consultant` in the web UI and click "Create Slots", or use the API:

```bash
# Login and store cookies
curl -c /tmp/cookies.txt -X POST http://localhost:3001/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"consultant@example.com","password":"consultant123!"}'

# Create slots
curl -b /tmp/cookies.txt -X POST http://localhost:8000/api/slots/seed | jq
```

### Running Tests

#### Backend Unit Tests

```bash
docker compose exec api pytest -q
```

#### E2E Tests (Playwright)

```bash
# Run via Docker Compose
docker compose --profile e2e up --build --abort-on-container-exit e2e

# Or run from host
cd e2e
npm install
npm run test:e2e
```

### Environment Configuration

Create a `.env` file in `repository_after/meeting-scheduler/` (optional - defaults work for local dev):

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=meeting_scheduler
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/meeting_scheduler
AUTH_JWT_SECRET=dev-secret-change-me
AUTH_DEV_MODE=1
```

### Google Calendar Integration (Optional)

To enable Google Calendar/Meet integration:

```env
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
GOOGLE_CALENDAR_ID=your-calendar-id
```

Or mount a service account file:

```env
GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json
```

---

## Troubleshooting

### Database Connection Issues

If tests fail with database connection errors:
1. Ensure PostgreSQL is running: `pg_isready`
2. Check connection string matches your database configuration
3. Verify database `appdb` exists and user `app` has permissions

### Docker Issues

- Ensure Docker and Docker Compose v2 are installed
- Check ports 5173, 3001, 8000, 5432 are not in use
- Use `docker compose logs` to view service logs

### Import Errors

- Ensure `PYTHONPATH` is set correctly when running tests
- Verify all `__init__.py` files exist in package directories
- Check that dependencies are installed: `pip install -r requirements.txt`

---

## Additional Resources

- **Trajectory**: See `trajectory/trajectory.md` for detailed build steps
- **Instance Config**: See `instances/instance.json` for benchmark configuration
- **Meeting Scheduler README**: See `repository_after/meeting-scheduler/README.md` for detailed app documentation

