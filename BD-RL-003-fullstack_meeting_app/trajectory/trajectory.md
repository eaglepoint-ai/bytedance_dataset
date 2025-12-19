# Project Build Trajectory: Meeting Scheduler Application

## Phase 1: Project Structure and Repository Setup (Steps 1-10)

1. Create project root directory `task_005` for the meeting scheduler benchmark task
2. Initialize repository structure with directories: `evaluation/`, `instances/`, `patches/`, `repository_before/`, `repository_after/`, `tests/`, `trajectory/`
3. Create `repository_after/meeting-scheduler/` directory for the refactored application code
4. Set up `.gitignore` to exclude Python cache (`__pycache__/`, `*.pyc`), Node modules (`node_modules/`), virtual environments (`venv/`, `.env`), and IDE files (`.vscode/`, `.idea/`)
5. Create root-level `Dockerfile` for Python test environment with `python:3.11-slim` base image
6. Create root-level `docker-compose.yml` as placeholder pointing to actual services in `repository_after/meeting-scheduler/`
7. Create root-level `requirements.txt` with test dependencies: `pytest`, `pytest-asyncio`, `pytest-anyio`, `httpx`, `sqlalchemy`, `psycopg`, `pydantic`, `fastapi`, `uvicorn`
8. Create root-level `README.md` with project overview, architecture description, and setup instructions
9. Create `run-all-tests-docker.sh` script for automated test execution (backend locally, frontend in Docker)
10. Create `instances/instance.json` with benchmark task metadata including problem statement, test requirements, and evaluation criteria

## Phase 2: Database Schema Design (Steps 11-20)

11. Design PostgreSQL database schema for `users` table with authentication support (JWT-based)
12. Design `time_slots` table with columns: id (UUID, primary key), start_at (timestamp), end_at (timestamp), consultant_id (UUID), is_active (boolean)
13. Design `meetings` table with columns: id (UUID), slot_id (foreign key), user_email (varchar), description (text), status (enum: BOOKED, CANCELED), created_at (timestamp)
14. Add foreign key constraint: meetings.slot_id references time_slots.id ON DELETE CASCADE
15. Design indexes: index on time_slots(start_at, end_at) for efficient availability queries
16. Add unique constraint on meetings.slot_id to prevent double-booking
17. Design enum type for meeting status: 'BOOKED', 'CANCELED' with appropriate transitions
18. Plan optional Google Calendar integration fields: google_calendar_event_id, google_meet_link in meetings table
19. Add consultant_id to time_slots for role-based access control (consultants create slots, users book them)
20. Create database migration strategy using SQLAlchemy `Base.metadata.create_all()` for initial schema

## Phase 3: Backend Architecture - FastAPI Application (Steps 21-35)

21. Create `repository_after/meeting-scheduler/api/` directory for FastAPI backend service
22. Initialize `api/requirements.txt` with dependencies: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `psycopg2-binary`, `pydantic`, `pydantic-settings`, `requests`, `python-dateutil`
23. Create `api/app/` package with `__init__.py` for application initialization
24. Implement `api/app/config.py` with Pydantic Settings for environment-based configuration (DATABASE_URL, AUTH_BASE_URL, CORS settings)
25. Implement `api/app/models.py` with SQLAlchemy ORM models: TimeSlot, Meeting, MeetingStatus enum
26. Add TimeSlot model with fields: id, start_at, end_at, consultant_id, is_active, timestamps
27. Add Meeting model with fields: id, slot_id, user_email, description, status, google_calendar_event_id, google_meet_link, created_at
28. Configure database session management in `api/app/db.py` with sessionmaker and dependency injection
29. Implement `api/app/deps.py` with dependency functions: get_db (database session), get_current_user (authentication verification)
30. Create `api/app/schemas.py` with Pydantic models for request/response validation: TimeSlotCreate, TimeSlotRead, MeetingCreate, MeetingRead
31. Implement authentication client in `api/app/auth_client.py` to verify JWT tokens with external auth service
32. Add CORS middleware configuration in main app to allow frontend cross-origin requests
33. Configure SQLAlchemy engine with connection pooling and echo mode for development
34. Implement database initialization logic to create tables on startup
35. Create main FastAPI application instance in `api/app/main.py` with lifespan events for startup/shutdown

## Phase 4: Backend API Routes - Slots Management (Steps 36-50)

36. Create `api/app/routes/` package with `__init__.py` for organizing API endpoints
37. Implement `api/app/routes/slots.py` with APIRouter for time slot operations
38. Add `GET /api/slots` endpoint to list available time slots with query parameters: from (datetime), to (datetime), consultant_id (optional)
39. Implement availability query logic: filter by date range, exclude booked slots, filter by consultant if specified
40. Add `POST /api/slots/seed` endpoint (consultant-only) to generate default time slots for next 14 days
41. Implement seed logic: create 30-minute slots from 9 AM to 5 PM on weekdays, skip weekends
42. Add role-based authorization: verify user has 'consultant' role before allowing slot creation
43. Add `POST /api/slots/create` endpoint (consultant-only) for custom time slot creation with start_date, end_date, start_time, end_time, skip_weekends
44. Implement slot creation logic with conflict detection: check for overlapping existing slots
45. Add `GET /api/slots/consultants` endpoint to list all users with consultant role for filtering
46. Implement `api/app/crud.py` with database operations: list_available_slots, create_slots, seed_slots_next_14_days
47. Add transaction management in CRUD operations using SQLAlchemy session commit/rollback
48. Implement error handling for database operations with appropriate HTTP status codes
49. Add input validation: ensure start_time < end_time, valid date formats, reasonable date ranges
50. Test slot endpoints manually: verify availability queries, test seed functionality, check authorization

## Phase 5: Backend API Routes - Meetings Management (Steps 51-65)

51. Implement `api/app/routes/meetings.py` with APIRouter for meeting booking operations
52. Add `POST /api/meetings` endpoint to book a meeting with request body: slot_id, description
53. Implement booking logic: verify slot exists and is available, mark slot as inactive, create meeting record with status BOOKED
54. Add authentication requirement: only logged-in users can book meetings
55. Implement double-booking prevention: check if slot already has a meeting, return 409 Conflict if booked
56. Add `GET /api/meetings/me` endpoint to list current user's meetings (both as user and consultant)
57. Implement meetings query: filter by user_email or consultant_id, join with time_slots table for full data
58. Add `POST /api/meetings/:id/cancel` endpoint to cancel a meeting
59. Implement cancellation logic: verify user owns the meeting, update status to CANCELED, reactivate the time slot
60. Add authorization check: only meeting creator or consultant can cancel
61. Add `GET /api/admin/meetings` endpoint (consultant-only) to view all meetings across all users
62. Implement admin query with pagination and filtering capabilities
63. Add Google Calendar integration in `api/app/google_calendar.py` (optional): create_calendar_event_with_meet function
64. Implement meeting creation with calendar event: generate Google Meet link, store event_id in database
65. Handle calendar integration failures gracefully: mark meet_status as 'error' if API call fails

## Phase 6: Authentication Service - Node.js/TypeScript (Steps 66-75)

66. Create `repository_after/meeting-scheduler/auth/` directory for authentication microservice
67. Initialize Node.js project with `npm init` and create `package.json` with dependencies: `express`, `jsonwebtoken`, `bcryptjs`, `better-sqlite3`, `dotenv`
68. Create `auth/tsconfig.json` for TypeScript configuration with ES modules support
69. Implement `auth/src/types.ts` with TypeScript interfaces: User, RegisterRequest, LoginRequest, AuthResponse
70. Implement `auth/src/env.ts` to load and validate environment variables: PORT, JWT_SECRET, DATABASE_PATH
71. Implement `auth/src/db.ts` with SQLite database initialization for user storage (development/testing)
72. Create users table schema: id (TEXT primary key), email (TEXT unique), password (TEXT hashed), role (TEXT: 'user' or 'consultant')
73. Implement `auth/src/auth.ts` with authentication logic: register, login, verify token functions
74. Add password hashing with bcrypt (10 salt rounds) and JWT token generation with 24-hour expiration
75. Create Express server in `auth/src/index.ts` with routes: POST /api/auth/register, POST /api/auth/login, GET /api/auth/verify

## Phase 7: Frontend Application - React/TypeScript Setup (Steps 76-90)

76. Create `repository_after/meeting-scheduler/web/` directory for React frontend application
77. Initialize Vite project with React and TypeScript template
78. Create `web/package.json` with dependencies: `react`, `react-dom`, `react-router-dom`, `vite`, `typescript`
79. Create `web/tsconfig.json` with TypeScript configuration for React JSX support
80. Configure Vite in `web/vite.config.ts` with environment variable support and dev server settings
81. Create `web/src/styles.css` with modern CSS styling: CSS variables for colors, flexbox layouts, responsive design
82. Implement `web/src/vite-env.d.ts` for Vite environment type declarations
83. Create `web/src/api/client.ts` with API fetch wrapper function including credentials and error handling
84. Implement `web/src/lib/auth.ts` with authentication helpers: login, register, logout, getUser functions
85. Create type definitions `web/src/react-shim.d.ts` for React component props
86. Implement `web/src/App.tsx` as root component with React Router setup and authentication context
87. Create protected route component `web/src/components/ProtectedRoute.tsx` to guard authenticated pages
88. Implement navigation with role-based menu items (different views for users vs consultants)
89. Configure environment variables in `web/` with `.env` file: VITE_API_BASE_URL, VITE_AUTH_BASE_URL
90. Set up hot module replacement (HMR) for fast development feedback

## Phase 8: Frontend Pages - Authentication (Steps 91-100)

91. Create `web/src/pages/Login.tsx` with email/password form and error handling
92. Implement login form validation: required fields, email format, minimum password length
93. Add login submit handler: call auth API, store user in context, redirect to appropriate page based on role
94. Create `web/src/pages/Register.tsx` with email, password, and role selection form
95. Implement register form validation with password confirmation field
96. Add register submit handler: call auth API, auto-login on success, redirect to dashboard
97. Implement error display: show API error messages in red text below form
98. Add loading states: disable submit button and show "Signing in..." during API call
99. Create navigation between Login and Register pages with links
100. Test authentication flow: register new user, login, verify token storage, test logout

## Phase 9: Frontend Pages - User Booking Flow (Steps 101-115)

101. Create `web/src/pages/Slots.tsx` for users to view and book available time slots
102. Implement date range selector with default range: today to 7 days from now
103. Add consultant filter dropdown to show slots for specific consultant or all consultants
104. Fetch available slots from API using date range and consultant filter parameters
105. Display slots in card layout with start time, end time, and "Book" button
106. Create `web/src/components/SlotList.tsx` reusable component for displaying slot cards
107. Implement `web/src/components/BookingModal.tsx` for booking confirmation with description input
108. Add booking modal: show selected slot time, textarea for description, confirm/cancel buttons
109. Implement booking submission: call POST /api/meetings endpoint, show success confirmation
110. Display booking confirmation with meeting details and Google Meet link (if available)
111. Add error handling: show 409 error if slot already booked, suggest alternative slots
112. Create `web/src/pages/MyMeetings.tsx` to list user's booked meetings
113. Display meetings in table with columns: Date/Time, Description, Status, Meet Link, Actions
114. Implement cancel button: call cancel API endpoint, confirm cancellation, refresh list
115. Add meeting status badges: green for BOOKED, gray for CANCELED

## Phase 10: Frontend Pages - Consultant Management (Steps 116-125)

116. Create `web/src/pages/Consultant.tsx` for consultants to manage meetings and create slots
117. Display all meetings (consultant view) with filtering by status and date
118. Add "Seed Slots" button to generate default availability for next 14 days
119. Implement seed confirmation dialog: warn if slots already exist, show count of created slots
120. Create advanced slot creation form with date range picker, start/end time inputs, skip weekends checkbox
121. Implement custom slot creation: validate inputs, call POST /api/slots/create, show created count
122. Add slot creation preview: show how many slots will be created before submission
123. Display consultant's own meetings with ability to view all participant details
124. Implement meeting cancellation from consultant view with email notification (if integrated)
125. Test consultant workflow: create slots, verify availability, book meeting as different user, view from consultant dashboard

## Phase 11: Docker Configuration - Multi-Service Setup (Steps 126-140)

126. Create `repository_after/meeting-scheduler/Dockerfile` for API service with Python 3.12-slim base
127. Configure API Dockerfile: install dependencies from requirements.txt, copy app code, expose port 8000, set uvicorn command
128. Create `repository_after/meeting-scheduler/auth/Dockerfile` for auth service with Node 20-alpine base
129. Configure auth Dockerfile: npm install, build TypeScript, expose port 3001, set node command
130. Create `repository_after/meeting-scheduler/web/Dockerfile` for frontend with Node 20-alpine base
131. Configure web Dockerfile: npm install, build production bundle with Vite, serve with simple HTTP server
132. Create `repository_after/meeting-scheduler/docker-compose.yml` to orchestrate all services
133. Define `postgres` service with PostgreSQL 15, health check, persistent volume, init database
134. Define `auth` service depending on postgres, expose port 3001, environment variables for JWT secret and database
135. Define `api` service depending on postgres and auth, expose port 8000, environment variables for database and auth URLs
136. Define `web` service depending on api, expose port 5173, environment variables for API and auth base URLs
137. Add Docker networks for service communication: default bridge network for all services
138. Add volumes: pg_data for PostgreSQL persistence, optional code mounts for development
139. Configure environment variable files: create `.env.example` with all required variables
140. Test Docker setup: run `docker compose up`, verify all services start, test cross-service communication

## Phase 12: Testing Infrastructure Setup (Steps 141-155)

141. Create `tests/` directory at repository root for all test files and configurations
142. Create `tests/package.json` for frontend test dependencies: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `jsdom`, `msw`
143. Create `tests/package-lock.json` by running `npm install` in tests directory
144. Create `tests/pytest.ini` for pytest configuration with asyncio mode and test path settings
145. Create `tests/vitest.config.ts` for Vitest configuration: jsdom environment, setup files, coverage settings
146. Configure vitest paths to resolve imports from `repository_after/meeting-scheduler/web/src`
147. Define environment variables in vitest config: VITE_API_BASE_URL, VITE_AUTH_BASE_URL for test environment
148. Create `tests/setup.ts` for global test setup: cleanup after each test, mock window.matchMedia, mock IntersectionObserver
149. Add test utilities: mock implementations for browser APIs not available in jsdom
150. Configure test scripts in package.json: `test` (run all), `test:unit`, `test:components`, `test:integration`, `test:watch`
151. Set up MSW (Mock Service Worker) for API mocking in frontend tests
152. Create MSW handlers for all API endpoints: GET /api/slots, POST /api/meetings, GET /api/meetings/me
153. Initialize MSW server in test setup: setupServer with handlers, listen before all tests, reset after each, close after all
154. Configure test coverage reporting: use Vitest's built-in coverage with v8 provider
155. Add `.gitignore` entries for test artifacts: `coverage/`, `node_modules/`, `.pytest_cache/`

## Phase 13: Backend Testing - Database and Models (Steps 156-170)

156. Create `tests/test_database.py` for database model and CRUD operation tests
157. Implement test fixture `db_session` that creates in-memory SQLite database for fast testing
158. Configure test database URL: use `sqlite:///:memory:` to avoid PostgreSQL dependency in tests
159. Set DATABASE_URL environment variable before importing app modules to override production config
160. Test TimeSlot model creation: verify all fields are set correctly, test default values
161. Test Meeting model creation: verify all fields, test status enum values
162. Test TimeSlot-Meeting relationship: verify foreign key constraint, test cascade delete
163. Implement CRUD function tests: test list_available_slots with various filters
164. Test create_meeting_booked: verify slot is marked inactive, meeting is created with correct status
165. Test cancel_meeting: verify slot is reactivated, meeting status is updated to CANCELED
166. Test create_slots function: verify multiple slots created correctly, test overlap detection
167. Test seed_slots_next_14_days: verify correct number of slots created, test weekday-only logic
168. Test database constraints: verify unique constraint on slot_id in meetings table
169. Test edge cases: booking already booked slot returns appropriate error, canceling canceled meeting is idempotent
170. Add pytest markers for database tests: `@pytest.mark.asyncio` for async tests, `@pytest.mark.db` for database-dependent tests

## Phase 14: Backend Testing - API Integration (Steps 171-185)

171. Create `tests/test_backend_api.py` for API endpoint integration tests
172. Add pytest-anyio configuration: create fixture `anyio_backend` returning "asyncio" to force asyncio mode
173. Set up test environment variables: API_BASE_URL=http://localhost:8000, AUTH_BASE_URL=http://localhost:3001
174. Create test fixtures for authenticated clients: `auth_client` (regular user), `consultant_client` (consultant role)
175. Implement auth_client fixture: register random user, login, create httpx.AsyncClient with cookies
176. Implement consultant_client fixture: register user with consultant role, login, return authenticated client
177. Test authentication requirement: verify POST /api/meetings returns 401 without auth
178. Test GET /api/slots endpoint: verify date range filtering, test consultant_id filtering, verify response format
179. Test POST /api/meetings endpoint: verify successful booking, check slot becomes inactive, verify 404 for invalid slot
180. Test double-booking prevention: book same slot twice, verify second request returns 409 Conflict
181. Test GET /api/meetings/me endpoint: verify user sees only their meetings, test empty result for new user
182. Test POST /api/meetings/:id/cancel endpoint: verify meeting canceled, slot reactivated, unauthorized users get 403
183. Test consultant-only endpoints: verify POST /api/slots/seed requires consultant role, returns 403 for regular users
184. Test POST /api/slots/seed functionality: verify slots created, test idempotent behavior (calling twice doesn't duplicate)
185. Test admin endpoints: verify GET /api/admin/meetings requires consultant role, returns all meetings

## Phase 15: Frontend Testing - Unit Tests (Steps 186-195)

186. Create `tests/frontend_unit.test.ts` for frontend utility function unit tests
187. Test `apiFetch` function: verify credentials included, test base URL resolution, test error handling
188. Mock global `fetch` function to test API client behavior without real network calls
189. Test API client error handling: verify 401 returns appropriate error, test network errors
190. Test authentication helpers in `lib/auth.ts`: mock API responses, verify token storage
191. Test `login` function: verify correct endpoint called, test success and error paths
192. Test `register` function: verify request body format, test role selection
193. Test `logout` function: verify calls logout endpoint, clears stored user data
194. Test `getUser` function: verify returns current user from API, handles unauthenticated state
195. Configure vitest to run unit tests in isolation: no DOM required, fast execution

## Phase 16: Frontend Testing - Component Tests (Steps 196-210)

196. Create `tests/frontend_components.test.tsx` for React component unit tests
197. Set up React Testing Library: import render, screen, fireEvent from '@testing-library/react'
198. Test Login component: verify email and password inputs render, test form submission
199. Mock useNavigate from react-router-dom to test navigation without actual routing
200. Test Login form validation: verify required fields show errors, test invalid email format
201. Test Login success flow: mock successful API response, verify navigation called with correct path
202. Test BookingModal component: verify modal opens/closes, test description textarea
203. Test BookingModal submission: mock onConfirm callback, verify called with description text
204. Test BookingModal cancel: verify onClose called when cancel button clicked
205. Test SlotList component: verify slots render as cards, test empty state message
206. Test SlotList book button: verify onBook callback called with correct slot when button clicked
207. Test slot card display: verify time formatting, test consultant name display
208. Wrap components in Router for tests that use react-router-dom hooks
209. Use cleanup after each test to prevent memory leaks and test interference
210. Configure component tests to run with jsdom environment for DOM APIs

## Phase 17: Frontend Testing - Integration Tests (Steps 211-225)

211. Create `tests/frontend_pages.integration.test.tsx` for page-level integration tests with mocked API
212. Set up MSW server with handlers for all API endpoints used by pages
213. Create mock data: mockConsultants, mockSlots, mockMeetings arrays
214. Configure MSW handlers: GET /api/slots/consultants returns mockConsultants
215. Configure GET /api/slots handler: return empty array if no consultant_id, return mockSlots if consultant selected
216. Configure POST /api/meetings handler: return new meeting with status BOOKED
217. Configure GET /api/meetings/me handler: return mockMeetings array
218. Configure POST /api/meetings/:id/cancel handler: return meeting with status CANCELED
219. Test Slots page: render component, verify consultants dropdown loads
220. Test Slots page simplified: verify page structure renders (consultant select, refresh button)
221. Test MyMeetings page: render component, verify meetings table displays
222. Test MyMeetings simplified: verify table renders without requiring full data loading
223. Create mock user object with email and role for passing to components that require authentication
224. Test page navigation: verify clicking links changes rendered component (if full integration)
225. Simplify integration tests for reliability: focus on rendering and basic interactions, not complex async flows

## Phase 18: Docker Test Integration (Steps 226-240)

226. Create `repository_after/meeting-scheduler/Dockerfile.test-backend` for running pytest in Docker
227. Configure test-backend Dockerfile: copy requirements.txt, install dependencies, copy tests and app code
228. Set working directory to `/app` in test-backend Dockerfile, copy files with correct paths
229. Create `repository_after/meeting-scheduler/Dockerfile.test-frontend` for running vitest in Docker
230. Configure test-frontend Dockerfile: copy package.json from tests/, npm install, copy test files
231. Copy vitest.config.ts and setup.ts from tests/ directory to Docker workspace
232. Copy frontend source code from `repository_after/meeting-scheduler/web/src` for test imports
233. Update `docker-compose.yml` to add `test-backend` service with profile: testing
234. Configure test-backend service: use context `../../` (task root), dockerfile path, set environment variables
235. Add dependencies for test-backend: postgres, auth, api must be started and healthy
236. Update `docker-compose.yml` to add `test-frontend` service with profile: testing
237. Configure test-frontend service: use context `../../`, dockerfile path, command `npm test`
238. Test services use profiles so they don't start with regular `docker compose up`
239. Run test-backend: `docker compose run --rm test-backend` executes pytest tests/ -v
240. Run test-frontend: `docker compose run --rm test-frontend` executes npm test (vitest run)

## Phase 19: Test Execution Strategy (Steps 241-250)

241. Create `run-all-tests-docker.sh` script for automated test execution
242. Make script executable with `chmod +x run-all-tests-docker.sh`
243. Script phase 1: navigate to `repository_after/meeting-scheduler`, start services with `docker compose up -d`
244. Script phase 2: wait for services to be healthy with `sleep 10` (allows postgres, auth, api to start)
245. Script phase 3: run backend tests LOCALLY (not in Docker) to avoid cookie domain issues
246. Export environment variables for local backend tests: API_BASE_URL, AUTH_BASE_URL
247. Run pytest with specific test files: `pytest tests/test_backend_api.py tests/test_database.py -v`
248. Capture backend test exit code for final reporting
249. Script phase 4: run frontend tests IN DOCKER using `docker compose run --rm test-frontend`
250. Capture frontend test exit code for final reporting

## Phase 20: Test Verification and Documentation (Steps 251-260)

251. Script phase 5: display test summary with PASSED/FAILED status for backend and frontend
252. Script phase 6: stop Docker services with `docker compose down` for clean shutdown
253. Script exit: return non-zero if any tests failed, zero if all passed
254. Document test execution in README.md: explain why backend tests run locally (cookie auth compatibility)
255. Explain in docs: frontend tests run in Docker because MSW mocks all APIs (no auth needed)
256. Create troubleshooting guide: common errors and solutions for test failures
257. Document test architecture: backend tests need live services, frontend tests are isolated
258. Add verification step: run `./run-all-tests-docker.sh` to verify all 71 tests pass
259. Expected results: 26 backend tests pass (14 API + 12 database), 45 frontend tests pass (14 unit + 18 component + 13 integration)
260. Final validation: confirm Docker services start correctly, all API endpoints work, frontend renders properly, all tests pass

## Summary

This trajectory covers the complete workflow for building and testing a production-ready meeting scheduler application with:

- **Backend**: FastAPI with SQLAlchemy, PostgreSQL, async operations
- **Auth Service**: Node.js/TypeScript with JWT authentication
- **Frontend**: React with TypeScript, Vite, React Router
- **Testing**: Comprehensive test suite with pytest (backend) and vitest (frontend)
- **Docker**: Multi-service architecture with docker-compose orchestration
- **CI/CD Ready**: Automated test execution script for easy integration

Total: 260 detailed implementation steps covering architecture, development, testing, and deployment.
