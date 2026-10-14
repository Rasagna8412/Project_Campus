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
│   │   ├── api/v1/endpoints/health.py   # Health endpoint with genuine DB verification
│   │   ├── core/                        # Config, async database engine, logging
│   │   ├── models/                      # SQLAlchemy 2.0 declarative models (identity, taxonomy)
│   │   ├── schemas/                     # Pydantic v2 response schemas
│   │   └── main.py                      # FastAPI app entry point & CORS
│   ├── alembic/                         # Alembic async migration scripts
│   ├── alembic.ini                      # Alembic configuration
│   └── requirements.txt                 # Backend Python dependencies
├── frontend/                            # React + TypeScript + Vite application
│   ├── src/
│   │   ├── components/common/           # Header, Footer, MathSnippet, CurriculumFoundation
│   │   ├── services/api.ts              # Live backend health check service
│   │   ├── types/api.ts                 # TypeScript API contracts
│   │   ├── test/                        # Vitest & Testing Library suites
│   │   ├── App.tsx                      # Main application shell with live health indicator
│   │   └── main.tsx                     # React DOM entry point
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── tests/                               # Backend automated test suite (Pytest)
│   ├── conftest.py                      # Isolated test database and async HTTP client fixtures
│   ├── test_health.py                   # GET /health & /api/v1/health tests
│   ├── test_database.py                 # DB connectivity & table presence tests
│   ├── test_models.py                   # Model hierarchy & constraint validation tests
│   └── test_error_handling.py           # Stack trace leak & secret protection tests
└── scripts/                             # Utility & verification scripts
    ├── run_backend.py                   # Start local backend uvicorn server
    └── verify_milestone_1.py            # Comprehensive cross-stack verification runner
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

# Start backend server (binds to http://127.0.0.1:8000)
python scripts/run_backend.py
```

* Backend Health Check: `http://127.0.0.1:8000/health`
* Interactive API Documentation (Swagger): `http://127.0.0.1:8000/docs`

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

### Backend Tests (Pytest)
```bash
# Run all backend unit & integration tests
$env:PYTHONPATH="backend"
.\.venv\Scripts\pytest.exe -v tests
```

### Frontend Tests (Vitest)
```bash
cd frontend
npm test
```

### Comprehensive Milestone 1 Verification
```bash
$env:PYTHONPATH="backend"
python scripts/verify_milestone_1.py
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
