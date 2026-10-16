# Project Campus

An enterprise-grade, serious educational technology platform architected for mastery learning, curriculum-aligned study, competitive examination preparation (CBSE, JEE, NEET), and transparent AI pedagogical support.

---

## Architecture & Governance Documentation

Comprehensive specifications and governance policies are maintained in the [`docs/`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/docs) directory:

* [**Product Requirements Document (PRD)**](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/docs/PRODUCT_REQUIREMENTS.md) — Product vision, principles, user personas, MVP scope vs. future horizons.
* [**Technical Architecture Specification**](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/docs/TECHNICAL_ARCHITECTURE.md) — System topology, React+TypeScript frontend, FastAPI backend, KaTeX math engine, RAG AI gateway.
* [**Database Design & Schema Specification**](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/docs/DATABASE_DESIGN.md) — Relational ERD, table definitions, data dictionary, indexing, and authorization rules.
* [**Security & Privacy Specification**](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/docs/SECURITY_AND_PRIVACY.md) — Student data privacy (DPDP Act 2023), minor protection, Argon2id, JWT lifecycle, RBAC, and AI guardrails.
* [**Content Quality & Verification Policy**](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/docs/CONTENT_QUALITY_POLICY.md) — Zero-tolerance policy for unverified answers, multi-stage editorial lifecycle, verified vs. AI separation, errata SLA.
* [**Phased Milestone Development Plan**](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/docs/MILESTONE_PLAN.md) — Step-by-step 10-milestone engineering roadmap with concrete deliverables and exit criteria.
* [**Comprehensive Testing Strategy**](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/docs/TESTING_STRATEGY.md) — Testing pyramid (unit, integration, E2E via Playwright, a11y via axe-core, LaTeX content linting).
* [**Known Issues & Risk Registry**](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/docs/KNOWN_ISSUES.md) — Milestone 0 discovery findings, host tooling audit, risk mitigations, and stakeholder assumptions.

---

## Technology Stack

* **Frontend:** React 18+, TypeScript 5, Vite, Tailwind CSS, KaTeX 0.16.
* **Backend:** Python 3.14+, FastAPI 0.115+, Pydantic v2, SQLAlchemy 2.0 (asyncio), Uvicorn.
* **Persistence & Cache:** PostgreSQL 16+ (production target) / SQLite (`aiosqlite` local development fallback).
* **Database Migrations:** Alembic (async runner with batch mode).
* **Testing:** Pytest, pytest-asyncio, HTTPX (backend); Vitest, React Testing Library, jsdom (frontend).
* **Version Control:** Git.

---

## Project Structure

```
project_campus/
├── README.md                            # Project overview and run guides
├── .gitignore                           # Git exclusions (venv, node_modules, dist, db files)
├── .env.example                         # Environment variable template
├── docs/                                # Architecture & governance documentation suite
├── backend/                             # Python FastAPI application
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py                  # JWT authentication, role guards & student dependency injection
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── auth.py          # Student registration, login, logout, me endpoints
│   │   │       │   ├── curricula.py     # Curriculum, grade, and subject taxonomy queries
│   │   │       │   ├── health.py        # Health endpoint with genuine DB verification
│   │   │       │   └── student.py       # Profile management, onboarding lifecycle & DPDP account erasure
│   │   │       └── api.py               # API v1 router mounting all modular endpoints
│   │   ├── core/                        # Config, async database engine, security (bcrypt/JWT/rate limiter), seed
│   │   ├── models/                      # SQLAlchemy 2.0 declarative models (identity, taxonomy)
│   │   ├── schemas/                     # Pydantic v2 schemas (auth, student, curriculum)
│   │   └── main.py                      # FastAPI app entry point, rate limiting & error handling
│   ├── alembic/                         # Alembic async migration scripts (up to eeac6986a79e)
│   ├── alembic.ini                      # Alembic configuration
│   └── requirements.txt                 # Backend Python dependencies (fastapi, sqlalchemy, bcrypt, pyjwt, etc.)
├── frontend/                            # React + TypeScript + Vite application
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/                    # AuthModal (Sign In / Register with tab switching & validations)
│   │   │   ├── common/                  # Header (live auth & connectivity), Footer, MathSnippet
│   │   │   ├── dashboard/               # StudentDashboard (workspace, subject badges, goal slider, account deletion)
│   │   │   └── onboarding/              # OnboardingWizard (4-step curriculum, grade, subject & goal setup)
│   │   ├── context/                     # AuthContext (session persistence, login, register, logout, profile)
│   │   ├── services/api.ts              # Modular HTTP client with JWT Authorization & credentials handling
│   │   ├── types/                       # TypeScript contracts (api, auth)
│   │   ├── test/                        # Vitest suites (App.test.tsx, Auth.test.tsx, Onboarding.test.tsx)
│   │   ├── App.tsx                      # App shell orchestrating guest hero, auth modal, onboarding & dashboard
│   │   └── main.tsx                     # React DOM entry point
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── tests/                               # Backend automated test suite (Pytest - 24 test cases)
│   ├── conftest.py                      # Isolated test database and async HTTP client fixtures
│   ├── test_auth.py                     # Registration, login, logout, password validation & me tests
│   ├── test_authorization.py            # IDOR isolation, role guards & DPDP account erasure tests
│   ├── test_onboarding.py               # Taxonomy retrieval, 4-step onboarding lifecycle & validation tests
│   ├── test_health.py                   # GET /health & /api/v1/health tests
│   ├── test_database.py                 # DB connectivity & table presence tests
│   ├── test_models.py                   # Model hierarchy & constraint validation tests
│   └── test_error_handling.py           # Stack trace leak & secret protection tests
└── scripts/                             # Utility & verification scripts
    ├── run_backend.py                   # Start local backend uvicorn server
    ├── verify_milestone_1.py            # Milestone 1 verification runner
    └── verify_milestone_2.py            # Comprehensive Milestone 2 verification runner
```

---

## Local Development Setup

### 1. Backend Setup
```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run database migrations
cd backend
alembic upgrade head
cd ..

# Optional: Seed initial curriculum & role taxonomy
python -c "import asyncio; from app.core.seed import seed_initial_data; asyncio.run(seed_initial_data())"

# Start backend server (binds to http://127.0.0.1:8000)
python scripts/run_backend.py
```

* Backend Health Check: `http://127.0.0.1:8000/health`
* Interactive API Documentation (Swagger): `http://127.0.0.1:8000/docs`
* API v1 Endpoints:
  * `POST /api/v1/auth/register` — Student registration with bcrypt hashing
  * `POST /api/v1/auth/login` — Login with rate-limiting, JWT response & HttpOnly cookie
  * `POST /api/v1/auth/logout` — Session termination
  * `GET /api/v1/auth/me` — Authenticated student identity
  * `GET /api/v1/curricula/` — Board, grade & subject taxonomy for onboarding
  * `GET /api/v1/curricula/subjects/{subject_id}/chapters` — Subject chapters and nested topics with published counts
  * `GET /api/v1/curricula/chapters/{chapter_id}/topics` — Topics under chapter with lesson counts
  * `GET /api/v1/curricula/topics/{topic_id}/lessons` — Topic published lessons strictly excluding drafts
  * `GET /api/v1/curricula/lessons/{lesson_id}` — Full lesson detail and ordered sections (404 for unapproved)
  * `GET /api/v1/practice/topics/{topic_id}/questions` — Student topic questions (answer keys and derivations omitted)
  * `POST /api/v1/practice/sessions` — Start deliberate practice session for a topic
  * `GET /api/v1/practice/sessions/{session_id}` — Practice session progress and question retrieval (IDOR protected)
  * `POST /api/v1/practice/submit` — Atomic answer evaluation and educator solution reveal
  * `POST /api/v1/practice/questions/{id}/report-errata` — Student errata report submission with issue categorization
  * `GET /api/v1/practice/history` — Student practice history and topic accuracy metrics
  * `GET /api/v1/student/profile` — Fetch current student's academic profile
  * `POST /api/v1/student/onboarding` — Multi-step academic onboarding submission
  * `PUT /api/v1/student/profile` — Update study goals & language preference
  * `DELETE /api/v1/student/account` — DPDP Act 2023 compliant account & profile erasure
  * `GET /api/v1/student/progress/lessons` — List student lesson reading progress
  * `POST /api/v1/student/progress/lessons/{id}/start` — Record idempotent lesson access start
  * `POST /api/v1/student/progress/lessons/{id}/complete` — Mark lesson as completed
  * `GET /api/v1/student/analytics/dashboard` — Aggregated KPI metrics, accuracy %, practice time & activity feed
  * `GET /api/v1/student/analytics/topics` — Topic performance breakdown with deterministic mastery classification
  * `GET /api/v1/student/analytics/recommendations` — Explainable prioritized next-step learning actions

### 2. Frontend Setup
```bash
cd frontend

# Run development server (binds to http://localhost:5173)
npm run dev

# Run TypeScript check & production build
npm run build
```

---

## Running Automated Tests

### Backend Tests (Pytest - 78 Tests)
```bash
# Run all backend unit & integration tests
$env:PYTHONPATH="backend"
.\.venv\Scripts\pytest.exe -v
```

### Frontend Tests (Vitest - 27 Tests across 8 Suites)
```bash
cd frontend
npm test
```

---

## Milestone Status

* **Milestone 0:** Discovery, Product Planning, and Architecture Specification — **COMPLETE**
* **Milestone 1:** Development Environment, Core Scaffolding, and Database Schema — **COMPLETE**
* **Milestone 2:** Secure Authentication, Authorization, and Academic Profile Management — **COMPLETE**
* **Milestone 3:** Curriculum Content Foundation and Structured Lesson Viewer — **COMPLETE**
* **Milestone 4:** Question Bank, Topic-Based Practice Engine, and Assessment Foundation — **COMPLETE**
* **Milestone 5:** Student Progress Tracking & Learning Analytics — **COMPLETE**
  * **Relational Progress Schema:** Alembic migration `be8ed8718838` adding `lesson_progress` table with unique constraint `(user_id, lesson_id)` (18 tables active).
  * **Zero Cache Drift Metric Engine:** Aggregates total questions solved, correct attempts, overall accuracy, and estimated practice time dynamically from atomic records.
  * **Deterministic Topic Mastery Classifier:** Categorizes topics into `INSUFFICIENT_DATA` (<5 Qs), `NEEDS_REVIEW` (>=5 Qs, <60%), `DEVELOPING` (>=5 Qs, 60-79.9%), and `STRONG` (>=5 Qs, >=80%).
  * **Explainable Learning Recommendations:** Generates priority-ordered suggestions (`RESUME_LESSON` -> `REVISE_TOPIC` -> `PRACTICE_TOPIC` -> `NEXT_LESSON`).
  * **Interactive Frontend Analytics & Progress UI:** 5-KPI header bar, topic performance matrix with status pills, recommendation action cards, activity feed, and lesson progress badges/completion toggles.
  * **Automated Verification:** 78/78 backend Pytest tests passing; 27/27 frontend Vitest tests passing; production compilation verified with zero TypeScript errors.
