# Project Campus — Known Issues, Technical Debt & Risk Registry

**Document Version:** 1.0.0  
**Status:** Milestone 0 Baseline Audit  
**Scope:** System Environment, Dependencies, Architecture Constraints, and Open Assumptions  
**Last Updated:** October 2026  

---

## 1. Baseline Repository & Environment Assessment

An exhaustive system inspection performed during Milestone 0 revealed the following state:

### 1.1. Workspace State
* **Initial State:** Empty directory (`c:\Users\LOQ\OneDrive\Desktop\project_campus`).
* **Version Control:** Git repository initialized during Milestone 0 (`git init`). No initial commit has been made yet.
* **Pre-existing Code / Tech Stack:** None. No legacy technical debt, obsolete frameworks, or conflicting dependencies exist in the repository.

### 1.2. Host System Runtime & Tooling Audit
* **Python Runtime:** `Python 3.14.3` installed.
  * *Observation:* Python 3.14 is a cutting-edge release. Certain compiled C-extension wheels (such as specific binary async database drivers) may require pure-Python fallbacks or standard compilation tools. The architecture will specify packages with broad pure-Python or pre-built wheel availability (e.g., `asyncpg`, `aiosqlite`, `pydantic-core`).
* **Node.js & Package Manager:** `Node.js v25.8.0`, `npm 11.16.0` installed.
  * *Observation:* Fully supports modern Vite 5+, React 18+, TypeScript 5+, Tailwind CSS, and Vitest.
* **Database & Container Tooling:**
  * `psql` is not installed or not present in system PATH.
  * `docker` is not installed or not present in system PATH.
  * *Architectural Implication:* To ensure seamless developer onboarding on this host machine without requiring complex manual PostgreSQL installations or Docker daemons, the database access layer must support **Dual-Dialect SQLAlchemy 2.0**:
    * **Development Fallback:** SQLite with `aiosqlite` (zero-configuration, embedded file-based ACID storage).
    * **Production Target:** PostgreSQL 16+ with `asyncpg` (scalable, production-grade relational database).

---

## 2. Technical Risks & Architectural Debt Registry

| Risk ID | Category | Description | Severity | Planned Mitigation |
| :--- | :--- | :--- | :---: | :--- |
| **RISK-01** | **Performance** | **Mobile Math Rendering Latency:** Rendering dozens of complex multi-line LaTeX equations and chemical structures in a single scrollable view can degrade DOM performance on low-end mobile devices. | Medium | Use **KaTeX** (significantly faster than MathJax); implement equation memoization; virtualize long lists of questions so off-screen formulas are rendered only when scrolled into view. |
| **RISK-02** | **AI Safety** | **Hallucination in Scientific Explanations:** Language models can occasionally invent plausible-sounding but scientifically inaccurate physics laws or chemical reaction mechanisms. | High | Enforce **Grounded RAG** (Retrieval-Augmented Generation) bounding responses strictly to verified textbook excerpts; provide prominent AI disclaimers; prioritize verified teacher solutions above AI answers. |
| **RISK-03** | **Cost & Scale** | **LLM API Usage Costs:** Unbounded student queries to paid external LLM APIs could incur unpredictable operational costs. | Medium | Implement Redis-backed token bucket rate limits per student (e.g., max 15 AI concept queries per day); cache frequent concept explanations; support swappable model backends (including local models via Ollama or lightweight models like Gemini Flash). |
| **RISK-04** | **Data Privacy** | **Compliance with India's DPDP Act 2023 for Minors:** Strict regulations penalize behavioral profiling or unauthorized processing of minors' personal data. | Critical | Enforce strict data minimization; zero behavioral advertising trackers; parental consent workflow for learners under age threshold; self-serve data erasure tools. |
| **RISK-05** | **Offline Access** | **Intermittent Rural Connectivity:** Students in remote areas often face network dropouts while solving timed question sets. | Medium | Architect the frontend client to cache active practice sets locally in browser storage (IndexedDB) and sync results atomically once connection is restored. |

---

## 3. Assumptions Requiring Stakeholder Validation

Before proceeding to Milestone 1 implementation, the following key assumptions require stakeholder review:

1. **Dual Database Dialect Strategy:**
   * *Assumption:* Using SQLite (`aiosqlite`) for local development testing and PostgreSQL for staging/production deployments is acceptable, provided all migrations and queries remain strictly dialect-compatible through SQLAlchemy 2.0.
   * *Validation Needed:* Confirm whether local development should utilize this dual-dialect approach or if an external PostgreSQL cloud instance / local daemon should be configured.

2. **Target Curriculum Prioritization for Milestone 3 Seed Data:**
   * *Assumption:* The initial curriculum content for verification testing will focus on **Class 11 & 12 Physics, Chemistry, and Mathematics** (aligning with CBSE and JEE Main foundational topics, e.g., Electrostatics, Thermodynamics, Kinematics).
   * *Validation Needed:* Confirm whether this subject and grade selection aligns with stakeholder expectations for initial demonstration.

3. **AI Tutor Integration Provider:**
   * *Assumption:* The AI Gateway will be architected with a decoupled provider interface (supporting Google Gemini, Anthropic, OpenAI, or local open-weights models) using an environment variable switch (`AI_PROVIDER=gemini|openai|anthropic|mock`). For automated testing and zero-cost local development, a deterministic `mock` provider will be the default.
   * *Validation Needed:* Confirm preferred production LLM provider and API access strategy.

4. **Multi-Tenancy & School Institutional Portals:**
   * *Assumption:* Institutional features (school admin portals, batch student rosters, teacher classroom assignments) are deferred to post-MVP releases to maintain intense focus on the direct student learning experience.
   * *Validation Needed:* Confirm whether B2B institutional features should remain out of MVP scope.

---

## 4. Milestone 2 Implementation Observations & Operational Status

1. **SQLite Canonical Database Path Synchronization:**
   * *Observation:* During Milestone 1, running Alembic from `backend/` versus running `pytest` or `scripts/run_backend.py` from repository root resolved `./project_campus_dev.db` into two distinct physical SQLite files.
   * *Resolution in Milestone 2:* Enforced `BASE_DIR / "project_campus_dev.db"` across `backend/app/core/config.py` and canonical directory references in `alembic.ini`. The root file is now the single source of truth for local development.

2. **Rate Limiting Persistence:**
   * *Observation:* The `AuthRateLimiter` is implemented in-memory for zero-dependency local development. In a multi-worker or containerized cluster deployment, memory states are isolated per process.
   * *Future Action:* For production staging, connect `AuthRateLimiter` to Redis to maintain distributed rate-limit counters.

3. **Schema Migration for Onboarding:**
   * *Observation:* Student onboarding required persistent multi-subject relationships and explicit completion tracking.
   * *Resolution in Milestone 2:* Added `onboarding_completed` flag to `student_profiles` and created the `student_profile_subjects` association table via migration `eeac6986a79e`. Verified idempotent seeding and clean rollback capability.

---

## 5. Milestone 4 Audit Observations & Operational Status

1. **Session Ownership & Duplicate Attempt Protection:**
   * *Observation:* Cross-student session attempt injection and duplicate submission score inflation were identified during the Milestone 4 security audit.
   * *Resolution:* Enforced session ownership checks returning `404 Not Found` for unauthorized session attempts, and rejected duplicate question submissions within the same session with `400 Bad Request`.

2. **Numerical Tolerance Floating-Point Precision:**
   * *Observation:* Exact boundary values for floating-point tolerance comparisons could fail due to standard IEEE 754 precision quirks (e.g. `abs(0.009 - 0.008) > 0.001`).
   * *Resolution:* Added an epsilon buffer (`tol + 1e-9`) in `backend/app/api/v1/endpoints/practice.py` to prevent rounding false negatives on exact boundaries.

3. **Non-Finite Float Sanitization in Validation Errors:**
   * *Observation:* Submitting `NaN` or `Infinity` caused `JSONResponse` in Starlette to fail serializing Pydantic's `RequestValidationError` detail dicts with `ValueError: Out of range float values are not JSON compliant`, resulting in an unhandled 500 error.
   * *Resolution:* Added a custom `RequestValidationError` handler in `backend/app/main.py` that recursively converts non-finite floats to strings, reliably returning a clean 422 HTTP response.

---

## 6. Phase B2 PostgreSQL Recovery & Reliability Status

1. **PostgreSQL Backup & Standalone Restore Utilities:**
   * *Observation:* Automated restoration workflows required production guardrails to prevent accidental overwriting of active databases.
   * *Resolution:* Implemented strict environment inspection in `scripts/restore_postgres.sh` and `scripts/backup_postgres.sh`, rejecting production container targets, enforcing clean temporary databases, and rejecting `--clean` / `--if-exists` flags.
2. **Automated Recovery Drill in CI:**
   * *Observation:* Verification drills required live PostgreSQL 15 execution in continuous integration.
   * *Resolution:* Added a dedicated `postgres:15-alpine` service in `.github/workflows/ci.yml` running `tests/test_backup_restore_drill.py` with synthetic data and strict schema teardown.

---

## 7. Phase C Autonomous Hardening & Defect Resolution

1. **Curriculum Recommendation Isolation (DEFECT-C-01):**
   * *Observation:* In `backend/app/api/v1/endpoints/analytics.py`, Priority 4 recommendations could fall back to global unstarted curriculum lessons when a student had not enrolled in any subjects (`enrolled_subject_ids` empty).
   * *Resolution:* Guarded Priority 4 query with `if enrolled_subject_ids:`, ensuring students without active enrollments receive zero unstarted lesson recommendations from unrelated curricula. Regression tested in `tests/test_progress_and_analytics.py`.

2. **Planner Reschedule Concurrency & Compaction (DEFECT-C-02 & DEFECT-C-03):**
   * *Observation:* The `reschedule_task` endpoint in `backend/app/api/v1/endpoints/planner.py` lacked mutex locking and used naive `max_order + 1` order allocation, risking race conditions and ceiling overflow on rapid concurrent rescheduling requests.
   * *Resolution:* Enforced student-date mutex locking (`_get_student_date_lock`) and database row locking (`_acquire_user_lock`), accompanied by deterministic candidate compaction within the `[1, 4]` daily task range. Added rollback and `409 Conflict` handling for database uniqueness constraints. Regression tested in `tests/test_study_planner.py`.

3. **Modal Dialog Accessibility & State Isolation (DEFECT-C-04):**
   * *Observation:* Modals lacked consistent keyboard dismissal (`Escape`), backdrop click closing, and ARIA dialog semantics. Furthermore, placing modal close handlers in the same `useEffect` as form state resets caused authentication errors to be cleared prematurely on parent re-renders.
   * *Resolution:* Added `role="dialog"`, `aria-modal="true"`, and `Escape` key event listeners across `AuthModal`, `StudyGoalModal`, `ErrataModal`, `PracticeModal`, and `FlashcardReviewModal`. Separated form reset effects from keyboard listener lifecycles. Verified across all 11 Vitest test suites.


