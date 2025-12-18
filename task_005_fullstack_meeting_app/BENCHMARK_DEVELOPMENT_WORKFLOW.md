# Benchmark Dataset Development Workflow

## Complete End-to-End Guide for Creating High-Quality Benchmark Tasks

---

## Phase 1: Prompt Design & Validation

### 1.1 Initial Prompt Review
**Objective:** Identify ambiguities and gaps before implementation

**Checklist:**
- [ ] Is the application domain clearly defined?
- [ ] Are all features explicitly listed?
- [ ] Are technology stack requirements specified?
- [ ] Are non-functional requirements included (performance, security)?
- [ ] Are edge cases and error scenarios mentioned?
- [ ] Is the expected user flow described?
- [ ] Are integration points defined?

**Common Ambiguities to Watch For:**
- Vague terms like "handle authentication" (JWT? Session? OAuth?)
- Missing data models/schema definitions
- Unclear API contracts (request/response formats)
- Undefined error handling strategies
- Missing authorization rules (who can do what?)
- Unspecified validation requirements

### 1.2 Prompt Rewriting
**Objective:** Create unambiguous, detailed specifications

**Template Structure:**
```markdown
## Application Overview
[Clear description of what the app does]

## Technical Stack
- Backend: [Framework + Version]
- Frontend: [Framework + Version]
- Database: [Type + Version]
- Authentication: [Method]

## Core Features
1. [Feature Name]
   - User Story: As a [role], I can [action] so that [benefit]
   - Acceptance Criteria:
     - [ ] Criterion 1
     - [ ] Criterion 2
   - API Endpoints: [List]
   - UI Components: [List]

## Data Models
[Entity]: {field: type, ...}

## API Specifications
POST /api/endpoint
Request: {...}
Response: {...}
Error Cases: {...}

## Authorization Matrix
| Role | Feature | Permission |
|------|---------|------------|
| User | Create  | Yes/No     |

## Validation Rules
- Field X: [requirements]
- Field Y: [requirements]
```

### 1.3 Prompt Testing
**Objective:** Validate that prompt produces buildable specifications

**Test Methods:**
1. **Paper Test:** Can you draw the architecture on paper?
2. **API Test:** Can you write mock API responses without code?
3. **State Test:** Can you map all application states?
4. **Flow Test:** Can you trace user actions end-to-end?

**Iteration Criteria:**
- ✅ All features have clear acceptance criteria
- ✅ All data flows are documented
- ✅ All error cases are specified
- ✅ No "TBD" or "etc." in specifications

---

## Phase 2: Detailed Implementation Plan

### 2.1 Architecture Design
**Deliverables:**
- System architecture diagram
- Component interaction diagram
- Data flow diagram
- Database schema (ERD)

**Documentation Template:**
```markdown
## Architecture Overview
[High-level description]

## Components
1. Component A
   - Responsibility: [What it does]
   - Technology: [Stack]
   - Dependencies: [What it needs]
   - Exposes: [APIs/Interfaces]

## Data Flow
[User Action] → [Component A] → [Component B] → [Database]

## External Dependencies
- Service X: [Purpose]
- API Y: [Purpose]
```

### 2.2 Technology Stack Selection
**Decision Criteria:**
- Matches prompt requirements
- Well-documented and stable
- Good testing ecosystem
- Docker support
- Active community

**Document Choices:**
```markdown
## Stack Justification
- Backend Framework: [Choice] - Reason: [Performance/Ecosystem/Type Safety]
- Database: [Choice] - Reason: [Data model fit/Performance]
- Testing: [Tools] - Reason: [Coverage/DX]
```

### 2.3 Development Roadmap
**Create Detailed Trajectory:**
```markdown
## Phase 1: Foundation (Steps 1-20)
1. Initialize project structure
2. Set up version control
3. Configure Docker environment
...

## Phase 2: Database (Steps 21-40)
21. Design schema
22. Create migrations
...

## Phase 3: Backend Core (Steps 41-80)
...

## Phase N: Testing & Documentation (Steps 201-260)
```

---

## Phase 3: Iterative Development

### 3.1 Development Environment Setup
**Initial Setup Checklist:**
- [ ] Initialize git repository
- [ ] Create `.gitignore` (exclude node_modules, __pycache__, .env, etc.)
- [ ] Set up Docker and docker-compose
- [ ] Configure development environment variables
- [ ] Install linters and formatters
- [ ] Set up IDE/editor configuration

### 3.2 Development Cycle
**Iterative Approach:**

```
1. Pick Feature from Roadmap
   ↓
2. Write Pseudo-code/API Contract
   ↓
3. Implement Backend
   ↓
4. Test Backend Manually (Postman/curl)
   ↓
5. Implement Frontend
   ↓
6. Test Frontend Manually (Browser)
   ↓
7. Fix Integration Issues
   ↓
8. Document API Endpoint
   ↓
9. Commit Working Feature
   ↓
10. Repeat for Next Feature
```

**Best Practices:**
- Work on one feature at a time
- Keep services running during development
- Test after each significant change
- Commit frequently with clear messages
- Document as you code

### 3.3 Manual Testing Strategy
**Backend Testing:**
```bash
# Test each endpoint after implementation
curl -X POST http://localhost:8000/api/endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# Verify database changes
docker exec -it postgres psql -U user -d db -c "SELECT * FROM table;"
```

**Frontend Testing:**
- Test in browser with DevTools open
- Verify network requests
- Check console for errors
- Test different user roles
- Test edge cases (empty states, errors)

---

## Phase 4: Comprehensive Testing

### 4.1 Backend Testing

#### 4.1.1 Database Tests
**What to Test:**
- Model creation and relationships
- Constraints (unique, foreign keys, NOT NULL)
- Cascade deletes
- Default values
- Timestamps

**Test File Structure:**
```python
# tests/test_database.py
import pytest
from sqlalchemy import create_engine

@pytest.fixture
def db_session():
    """Create in-memory test database"""
    engine = create_engine("sqlite:///:memory:")
    # ... setup and teardown
    yield session

def test_model_creation(db_session):
    """Test basic model CRUD"""
    pass

def test_relationships(db_session):
    """Test foreign key relationships"""
    pass

def test_constraints(db_session):
    """Test database constraints"""
    pass
```

#### 4.1.2 API Integration Tests
**What to Test:**
- Authentication requirements
- Authorization (role-based access)
- Input validation
- Business logic
- Error responses
- Edge cases

**Test File Structure:**
```python
# tests/test_backend_api.py
import pytest
import httpx

@pytest.fixture
async def auth_client():
    """Authenticated test client"""
    # Register and login
    yield client

@pytest.mark.asyncio
async def test_endpoint_requires_auth():
    """Test authentication requirement"""
    pass

@pytest.mark.asyncio
async def test_endpoint_validates_input():
    """Test input validation"""
    pass

@pytest.mark.asyncio
async def test_endpoint_business_logic():
    """Test core functionality"""
    pass
```

**Coverage Goals:**
- 100% of API endpoints
- All success paths
- All error paths
- All authorization rules

### 4.2 Frontend Testing

#### 4.2.1 Unit Tests
**What to Test:**
- Utility functions
- API client helpers
- Authentication helpers
- Data transformations

**Test File Structure:**
```typescript
// tests/frontend_unit.test.ts
import { describe, it, expect, vi } from 'vitest';
import { apiFetch, authHelpers } from '../src/api';

describe('API Client', () => {
  it('includes credentials in requests', () => {
    // Test implementation
  });

  it('handles errors correctly', () => {
    // Test implementation
  });
});
```

#### 4.2.2 Component Tests
**What to Test:**
- Component renders correctly
- Props are used properly
- Events trigger callbacks
- User interactions work
- Conditional rendering

**Test File Structure:**
```typescript
// tests/frontend_components.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Component } from '../src/components/Component';

describe('Component', () => {
  it('renders with props', () => {
    render(<Component prop="value" />);
    expect(screen.getByText('value')).toBeDefined();
  });

  it('handles click events', () => {
    const mockFn = vi.fn();
    render(<Component onClick={mockFn} />);
    fireEvent.click(screen.getByRole('button'));
    expect(mockFn).toHaveBeenCalled();
  });
});
```

#### 4.2.3 Integration Tests
**What to Test:**
- Page-level interactions
- Multi-component workflows
- Mocked API responses
- Navigation flows

**Test File Structure:**
```typescript
// tests/frontend_pages.integration.test.tsx
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

const server = setupServer(
  http.get('/api/endpoint', () => {
    return HttpResponse.json({ data: [] });
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Page Integration', () => {
  it('loads and displays data', async () => {
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByText('data')).toBeDefined();
    });
  });
});
```

### 4.3 Test Configuration

#### 4.3.1 Backend (pytest)
```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

#### 4.3.2 Frontend (vitest)
```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html']
    }
  }
});
```

---

## Phase 5: Docker Integration

### 5.1 Service Dockerfiles
**Create Dockerfile for Each Service:**

```dockerfile
# Backend Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

### 5.2 Docker Compose Configuration
**Multi-Service Orchestration:**

```yaml
version: '3.8'

services:
  database:
    image: postgres:15
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    healthcheck:
      test: ["CMD", "pg_isready"]
      interval: 5s

  backend:
    build: ./backend
    depends_on:
      database:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://user:pass@database/appdb
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    depends_on:
      - backend
    ports:
      - "5173:5173"

  # Test services
  test-backend:
    build:
      context: .
      dockerfile: Dockerfile.test-backend
    profiles:
      - testing

  test-frontend:
    build:
      context: .
      dockerfile: Dockerfile.test-frontend
    profiles:
      - testing
```

### 5.3 Test Docker Images
**Create Separate Dockerfiles for Tests:**

```dockerfile
# Dockerfile.test-backend
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY tests ./tests
COPY app ./app
CMD ["pytest", "tests/", "-v"]
```

---

## Phase 6: Folder Structure Organization

### 6.1 Standard Benchmark Structure
```
TASK_XXX/
├── Dockerfile                    # Root-level test environment
├── docker-compose.yml            # Placeholder/reference
├── requirements.txt              # Python test dependencies
├── README.md                     # Project documentation
├── run-all-tests-docker.sh       # Automated test runner
│
├── evaluation/                   # Evaluation scripts
│   └── evaluate.py
│
├── instances/                    # Task definitions
│   └── instance.json
│
├── patches/                      # Code patches (before→after)
│   └── implementation.patch
│
├── repository_before/            # Initial/baseline code
│   └── (minimal or empty)
│
├── repository_after/             # Refactored/implemented code
│   └── app/                      # Actual application
│       ├── backend/
│       ├── frontend/
│       ├── services/
│       └── docker-compose.yml    # Application services
│
├── tests/                        # All test files
│   ├── test_backend_*.py         # Backend tests
│   ├── frontend_*.test.ts(x)     # Frontend tests
│   ├── package.json              # Frontend test deps
│   ├── pytest.ini                # Pytest config
│   ├── vitest.config.ts          # Vitest config
│   └── setup.ts                  # Test setup
│
└── trajectory/                   # Implementation guide
    └── trajectory.md             # Step-by-step breakdown
```

### 6.2 Cleanup Checklist
**Before Finalizing:**
- [ ] Remove `node_modules/` from root
- [ ] Remove `__pycache__/` directories
- [ ] Remove `.pytest_cache/` directories
- [ ] Remove duplicate markdown files
- [ ] Remove development helper scripts
- [ ] Remove `.DS_Store` files
- [ ] Move all test configs to `tests/`
- [ ] Ensure only canonical files in root

---

## Phase 7: Documentation

### 7.1 README.md
**Essential Sections:**

```markdown
# Project Name

## Overview
Brief description of what the application does.

## Architecture
High-level architecture diagram and explanation.

## Technology Stack
- Backend: [Framework + Version]
- Frontend: [Framework + Version]
- Database: [Database + Version]

## Setup & Installation

### Prerequisites
- Docker & Docker Compose
- Python 3.x (for local testing)
- Node.js 20+ (for local testing)

### Quick Start
\`\`\`bash
# Start all services
cd repository_after/app
docker compose up

# Run tests
./run-all-tests-docker.sh
\`\`\`

## Project Structure
[Brief explanation of folder organization]

## Testing
[How to run tests and what they cover]

## API Documentation
[Link to API docs or inline documentation]

## Development Guide
[How to contribute or extend]
```

### 7.2 Trajectory Documentation
**Implementation Steps (trajectory.md):**

```markdown
# Project Build Trajectory

## Phase 1: Setup (Steps 1-10)
1. Initialize project structure
2. Set up version control
...

## Phase 2: Database (Steps 11-30)
11. Design schema
...

## Phase N: Testing (Steps X-Y)
X. Create test infrastructure
...

Total: [N] detailed steps
```

### 7.3 Instance Configuration
**instances/instance.json:**

```json
{
  "instance_id": "task_xxx_description",
  "problem_statement": "Clear description of what needs to be implemented",
  "base_commit": "repository_before",
  "test_patch": "tests/",
  "repo": "https://github.com/...",
  "environment_setup": "Dockerfile",
  "FAIL_TO_PASS": [
    "test_feature_1",
    "test_feature_2"
  ],
  "PASS_TO_PASS": [
    "test_existing_functionality"
  ]
}
```

### 7.4 Patch Documentation
**patches/implementation.patch:**

```diff
From: implementation_author
Subject: [PATCH] Brief description of changes

Detailed explanation of what was implemented:
- Feature A
- Feature B
- Test coverage

Architecture highlights:
- Design decisions
- Technology choices
- Trade-offs

---
diff --git a/path/to/file.ext b/path/to/file.ext
new file mode 100644
index 0000000..abc123
--- /dev/null
+++ b/path/to/file.ext
@@ -0,0 +1,50 @@
+[File contents showing implementation]
...
```

---

## Phase 8: Final Validation

### 8.1 Pre-Submission Checklist

**Structure Validation:**
- [ ] Folder structure matches benchmark standard
- [ ] No clutter in root directory
- [ ] All test files in `tests/` directory
- [ ] README.md is comprehensive
- [ ] trajectory.md has detailed steps
- [ ] instance.json is accurate
- [ ] Patch file is complete

**Code Quality:**
- [ ] No commented-out code
- [ ] No debug print statements
- [ ] Consistent code style
- [ ] No hardcoded credentials
- [ ] Environment variables properly used
- [ ] Error handling implemented
- [ ] Logging configured

**Testing:**
- [ ] All tests pass locally
- [ ] All tests pass in Docker
- [ ] Test coverage is comprehensive
- [ ] Test execution is automated
- [ ] Tests are deterministic (no flaky tests)

**Documentation:**
- [ ] All features documented
- [ ] API endpoints documented
- [ ] Setup instructions are clear
- [ ] Architecture is explained
- [ ] Design decisions are justified

**Docker:**
- [ ] All services build successfully
- [ ] Services start and communicate
- [ ] Health checks configured
- [ ] Environment variables documented
- [ ] Ports don't conflict
- [ ] Volumes configured correctly

### 8.2 Test Execution Validation

```bash
# 1. Clean environment
docker compose down -v
docker system prune -f

# 2. Build from scratch
docker compose build --no-cache

# 3. Run application
docker compose up -d

# 4. Verify services
docker compose ps
# All services should be "running" or "healthy"

# 5. Run all tests
./run-all-tests-docker.sh

# 6. Verify test results
# Expected: All tests pass (e.g., 71/71)

# 7. Clean up
docker compose down
```

### 8.3 Documentation Review

**Read Through:**
- [ ] README makes sense to new developer
- [ ] Setup instructions are complete
- [ ] Architecture is understandable
- [ ] Test execution is clear

**Test Instructions:**
- Follow your own README from scratch
- Set up on clean machine/container
- Verify everything works as documented

---

## Phase 9: Continuous Improvement

### 9.1 Iteration Based on Feedback
- Collect feedback from reviews
- Identify ambiguous instructions
- Fix failing tests
- Improve documentation
- Optimize performance

### 9.2 Lessons Learned Documentation
**Capture:**
- What worked well
- What was challenging
- Design decisions and trade-offs
- Testing strategies that helped
- Time estimates vs actual

---

## Quick Reference Checklist

### Development Phase
- [ ] Prompt reviewed and rewritten
- [ ] Architecture designed
- [ ] Technology stack selected
- [ ] Development roadmap created
- [ ] Feature implemented iteratively
- [ ] Manual testing performed
- [ ] Integration verified

### Testing Phase
- [ ] Database tests written (models, relationships)
- [ ] Backend API tests written (endpoints, auth, validation)
- [ ] Frontend unit tests written (utilities, helpers)
- [ ] Frontend component tests written (rendering, interactions)
- [ ] Frontend integration tests written (pages, flows)
- [ ] Test configs created (pytest.ini, vitest.config.ts)
- [ ] All tests passing

### Docker Phase
- [ ] Service Dockerfiles created
- [ ] docker-compose.yml configured
- [ ] Test Dockerfiles created
- [ ] All services build and run
- [ ] Test execution automated

### Structure Phase
- [ ] Folder structure cleaned
- [ ] Root directory organized
- [ ] Test files consolidated in tests/
- [ ] No build artifacts committed
- [ ] .gitignore configured

### Documentation Phase
- [ ] README.md complete
- [ ] trajectory.md detailed
- [ ] instance.json accurate
- [ ] Patch file generated
- [ ] API documented
- [ ] Setup instructions verified

### Validation Phase
- [ ] All tests pass locally
- [ ] All tests pass in Docker
- [ ] Documentation accurate
- [ ] Structure matches standard
- [ ] Ready for submission

---

## Time Estimates

**Typical Timeline:**
- Prompt design: 2-4 hours
- Architecture & planning: 2-3 hours
- Core implementation: 8-16 hours
- Testing setup: 2-4 hours
- Test writing: 4-8 hours
- Docker integration: 2-3 hours
- Documentation: 2-4 hours
- Cleanup & validation: 1-2 hours

**Total: 23-44 hours** (depends on complexity)

---

## Tips for Success

1. **Start Simple:** Build minimal viable version first
2. **Test Early:** Don't wait until end to test
3. **Document As You Go:** Don't leave docs for last
4. **Commit Often:** Small, working commits are safer
5. **Use Tools:** Linters, formatters, type checkers
6. **Ask Questions:** Clarify ambiguities early
7. **Follow Standards:** Consistency matters
8. **Automate:** Scripts for repetitive tasks
9. **Validate Often:** Check tests frequently
10. **Stay Organized:** Clean structure from day 1

---

## Common Pitfalls to Avoid

❌ **Don't:**
- Skip planning phase
- Implement everything at once
- Leave testing for the end
- Hardcode configuration values
- Ignore error handling
- Write untestable code
- Over-engineer solutions
- Skip documentation
- Leave clutter in repository
- Forget to test Docker setup

✅ **Do:**
- Plan thoroughly first
- Work incrementally
- Test continuously
- Use environment variables
- Handle all error cases
- Write testable code
- Keep it simple
- Document everything
- Maintain clean structure
- Validate final setup

---

## Conclusion

This workflow provides a complete framework for developing high-quality benchmark tasks. Adapt the process to your specific needs, but maintain the core principles:

1. **Clarity First:** Clear specifications prevent problems
2. **Incremental Progress:** Small steps, continuous validation
3. **Comprehensive Testing:** Tests prove quality
4. **Clean Organization:** Structure matters
5. **Thorough Documentation:** Others must understand your work

Follow this workflow, and you'll produce consistent, high-quality benchmark datasets.

