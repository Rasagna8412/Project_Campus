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
  * `GET /api/v1/curricula` — Board, grade & subject taxonomy for onboarding
  * `GET /api/v1/student/profile` — Fetch current student's academic profile
  * `POST /api/v1/student/onboarding` — Multi-step academic onboarding submission
  * `PUT /api/v1/student/profile` — Update study goals & language preference
  * `DELETE /api/v1/student/account` — DPDP Act 2023 compliant account & profile erasure

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

### Backend Tests (Pytest - 24 Tests)
```bash
# Run all backend unit & integration tests
$env:PYTHONPATH="backend"
.\.venv\Scripts\pytest.exe -v tests
```

### Frontend Tests (Vitest - 10 Tests across 3 Suites)
```bash
cd frontend
npm test -- --run
```

### Comprehensive Milestone 2 Verification Runner
```bash
$env:PYTHONPATH="backend"
python scripts/verify_milestone_2.py
```

---

## Milestone Status

* **Milestone 0:** Discovery, Product Planning, and Architecture Specification — **COMPLETE**
* **Milestone 1:** Development Environment, Core Scaffolding, and Database Schema — **COMPLETE**
  * FastAPI application scaffolding with genuine `/health` checks.
  * React 18 + TypeScript + Vite frontend with live API connectivity indicator & KaTeX math rendering.
  * SQLAlchemy 2.0 models for academic taxonomy (`boards_curricula`, `grades_stages`, `subjects`, `chapters`, `topics`) and identity foundation (`users`, `roles`, `user_roles`, `student_profiles`).
  * Alembic initial async migration applied cleanly.
  * 10/10 backend tests passing; 4/4 frontend tests passing; production compilation verified.
* **Milestone 2:** Secure Authentication, Authorization, and Academic Profile Management — **COMPLETE**
  * **Backend Security:** Password hashing via bcrypt with salt; stateless JWT issuance and verification; in-memory sliding-window rate limiter protecting login and registration against brute-force attacks; role-aware authorization (`STUDENT`, `EDUCATOR`, `REVIEWER`, `ADMIN`).
  * **Strict Data Isolation (IDOR Defense):** All student profile and onboarding queries derive identity solely from authenticated JWT claims (`current_user.id`), rejecting spoofed client parameters.
  * **Relational Schema Migration:** Alembic migration `eeac6986a79e` adding `onboarding_completed` flag and `student_profile_subjects` join table.
  * **Academic Onboarding Workflow:** Multi-step wizard supporting curriculum selection (CBSE, JEE Main, NEET), grade stage, subject selection with validation, and daily study goal configuration.
  * **Privacy Compliance (DPDP Act 2023):** `DELETE /api/v1/student/account` self-service endpoint cleanly cascading removal of student profile, subject links, and user account.
  * **Frontend Experience:** Modal authentication with instant switching between Sign In and Register; animated multi-step onboarding wizard; responsive student workspace displaying active board, grade, target exam year, subject badges, and interactive goal slider.
  * **Automated Verification:** 24/24 backend tests passing; 10/10 frontend tests passing; production build verified with zero TypeScript errors.
