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

* **Frontend:** React 18+, TypeScript, Vite, Tailwind CSS, KaTeX.
* **Backend:** Python (FastAPI), Pydantic v2, SQLAlchemy 2.0 (asyncio), Uvicorn.
* **Persistence & Cache:** PostgreSQL 16+ (production) / SQLite (`aiosqlite` local development fallback), Redis 7+.
* **Testing:** Pytest, Vitest, Playwright, axe-core.
* **Version Control:** Git.

---

## Milestone Status

* **Milestone 0:** Discovery, Product Planning, and Architecture Specification — **COMPLETE** (Awaiting Review).
