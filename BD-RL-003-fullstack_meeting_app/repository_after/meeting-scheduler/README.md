# Meeting Scheduler (React + FastAPI + Node Auth) — Docker Compose

A complete local full‑stack app to:
- View available consultation time slots
- Book a slot (exclusive at DB level)
- View/cancel your bookings (cancel re-opens slot)
- (Optionally) create a Google Calendar event with a Google Meet link

Includes:
- **Auth service** (Node/TypeScript) with email/password, roles (user/consultant), and dev/test helpers
- **API** (FastAPI) with Postgres constraints for slot exclusivity (partial unique index)
- **Web** (Vite + React Router) responsive UI + stable `data-testid` selectors
- **E2E** (Playwright) browser tests covering booking/cancel/consultant view

> Note on “Better Auth”: this repo implements a small, Better-Auth-like auth service in Node/TS with `/api/auth/*` routes, cookie session + `/session`, roles, and dev/test helpers exactly as required.

---

## Repository Structure

```text
meeting-scheduler/
  auth/   # Node/TS auth service
  api/    # FastAPI backend
  web/    # React frontend
  e2e/    # Playwright browser tests
```

---

## Quick Start

### 1) Prereqs
- Docker + Docker Compose (v2)
- (Optional) Node 18+ if you want to run E2E from host instead of container

### 2) Configure env
Copy `.env.example` to `.env` (optional — defaults are usable).

```bash
cp .env.example .env
```

### 3) Start everything
```bash
docker compose up --build
```

Services will be available:
- Web: http://localhost:5173
- Auth: http://localhost:3001
- API: http://localhost:8000

Health checks:
- API: http://localhost:8000/health

---

## Dev Convenience Actions

### Create time slots (consultant-only)
The API provides:
- `POST /api/slots/seed` (consultant-only) — creates slots for the next 14 days, weekdays 09:00–17:00, 30-minute intervals.

In local dev, you can:
1) Create a consultant user (auth)
2) Set role consultant (auth dev helper)
3) Call seed slots (api)

#### Create consultant (dev-only)
```bash
curl -s -X POST http://localhost:3001/api/auth/seed-consultant | jq
```

#### Set role consultant (dev-only)
```bash
curl -s -X POST http://localhost:3001/api/auth/test/set-role \
  -H 'Content-Type: application/json' \
  -d '{"email":"consultant@example.com","role":"consultant"}' | jq
```

Now login in the UI as:
- email: `consultant@example.com`
- password: `consultant123!`

Then open `/consultant` and (optional) create slots from UI's "Create Slots" button (or curl below).

#### Create slots from CLI (needs auth cookie)
Use the UI for simplicity, or use a cookie jar:
```bash
# 1) Login and store cookies
curl -c /tmp/cookies.txt -s -X POST http://localhost:3001/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"consultant@example.com","password":"consultant123!"}' | jq

# 2) Create slots (forward cookies to API)
curl -b /tmp/cookies.txt -s -X POST http://localhost:8000/api/slots/seed | jq
```

---

## Google Calendar / Meet Integration (Optional)

If configured, booking creates a Calendar event with conferenceData and stores:
- `google_calendar_event_id`
- `google_meet_link`

If not configured, booking still succeeds and returns:
- `google_meet_link: null`
- `meet_status: "NOT_CONFIGURED"`

### Env options
Provide either:
- `GOOGLE_SERVICE_ACCOUNT_JSON` (full JSON as a single string)
or
- `GOOGLE_SERVICE_ACCOUNT_FILE` (path inside the API container; you can mount it)

And:
- `GOOGLE_CALENDAR_ID` (recommended: shared calendar id; default is `"primary"`)

If Google is not configured, the UI displays **“Meet link pending / not configured”**.

---

## API Contracts

### Slot exclusivity (DB-level)
A Postgres **partial unique index** guarantees:
> Only one `BOOKED` meeting exists per slot at a time.

If two requests try to book the same slot concurrently:
- one succeeds
- one returns **409**

---

## Run Backend Unit Tests

```bash
docker compose exec api pytest -q
```

Included tests:
- booking same slot twice returns 409 (unique constraint enforced)
- cancel re-opens slot (slot appears available again)

---

## Run E2E Tests (Playwright)

### Option A (recommended): Run via Docker Compose profile
```bash
docker compose --profile e2e up --build --abort-on-container-exit e2e
```

### Option B: Run from host
```bash
cd e2e
npm install
npm run test:e2e
```

E2E covers:
- Register → login → book first available slot
- Slot exclusivity in UI: user A books; user B cannot see that slot
- Cancel re-opens slot: user A cancels; user B sees slot again
- Consultant dashboard: consultant sees booked consultations + join link

---

## Verify Slot Exclusivity Manually (Concurrency)
1) Create slots (as consultant).
2) Open two browser windows in different accounts.
3) Try to book the same slot quickly.
4) One will succeed, the other will see an error (409).

---

## Security Notes (Local Dev)
- Session cookie is **httpOnly**, signed (JWT), and includes role.
- CORS is restricted to the web origin in dev compose.
- Dev/test helper endpoints only work when `AUTH_DEV_MODE=1`.

---
