# Project Campus — Phased Milestone Development Plan

**Document Version:** 1.0.0  
**Status:** Approved for Implementation Roadmap  
**Target Completion:** Full MVP Production Pilot  
**Last Updated:** October 2026  

---

## 1. Roadmap Overview & Timeline

Project Campus follows a disciplined, milestone-driven engineering approach. Each milestone delivers concrete, testable functionality with verifiable exit criteria before the subsequent milestone begins.

```mermaid
gantt
    title Project Campus Implementation Roadmap
    dateFormat  YYYY-MM-DD
    section Discovery & Foundations
    Milestone 0: Discovery, Architecture & Docs       :done, m0, 2026-10-14, 1d
    Milestone 1: Project Scaffolding & Core Infra     :active, m1, after m0, 3d
    Milestone 2: Auth, RBAC & Academic Profiles       :m2, after m1, 3d
    section Educational Core
    Milestone 3: Curriculum Taxonomy & Lesson Viewer  :m3, after m2, 4d
    Milestone 4: Question Bank & Assessment Engine    :m4, after m3, 5d
    section Intelligence & Analytics
    Milestone 5: Progress Analytics & Gap Analysis   :m5, after m4, 4d
    Milestone 6: Transparent AI Concept Clarifier     :m6, after m5, 4d
    Milestone 7: Spaced Repetition & Study Planner    :m7, after m6, 3d
    section Hardening & Deployment
    Milestone 8: Mobile UX, Accessibility & Hardening :m8, after m7, 4d
    Milestone 9: Production Readiness & Pilot Launch  :m9, after m8, 3d
```

---

## 2. Detailed Milestone Specifications

### Milestone 0: Discovery, Planning & Architectural Specification (Current Milestone)
* **Goal:** Perform deep discovery on the workspace, establish project principles, define technical architecture, and author all foundational technical and governance documents.
* **Deliverables:**
  * Complete documentation suite (`PRODUCT_REQUIREMENTS.md`, `TECHNICAL_ARCHITECTURE.md`, `DATABASE_DESIGN.md`, `SECURITY_AND_PRIVACY.md`, `CONTENT_QUALITY_POLICY.md`, `MILESTONE_PLAN.md`, `TESTING_STRATEGY.md`, `KNOWN_ISSUES.md`).
  * Discovery report detailing current host environment (Python 3.14, Node v25, Git, etc.).
* **Exit Criteria:** All planning documents approved; architecture reviewed and signed off.
* **Status:** Complete. Awaiting review before starting Milestone 1.

---

### Milestone 1: Development Environment Setup, Core Scaffolding & Database Schema
* **Goal:** Scaffold the frontend and backend applications, configure database connections, set up Alembic migrations, and establish continuous code quality tooling.
* **Deliverables:**
  * Backend: FastAPI application scaffold (`app/main.py`), SQLAlchemy async database engine, Alembic configuration, initial schema migrations for core tables.
  * Frontend: React + TypeScript Vite project scaffold, Tailwind CSS configuration, KaTeX math rendering utility, Axios/Fetch API client.
  * Developer Experience: Docker Compose configuration for local PostgreSQL and Redis; linting with Ruff and ESLint/Prettier.
* **Exit Criteria:**
  * Backend server boots on `http://localhost:8000` with passing `/health` check.
  * Frontend renders on `http://localhost:5173` with KaTeX sample equation rendering.
  * Alembic migration executes successfully on PostgreSQL (and SQLite test runner).

---

### Milestone 2: Authentication, Authorization & Academic Profile Management
* **Goal:** Deliver secure student and educator registration, login, JWT session management, RBAC, and academic onboarding.
* **Deliverables:**
  * Endpoints: `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/auth/me`.
  * Student onboarding flow: Selection of target board (CBSE, JEE Main, NEET), grade level (Class 11/12), target exam year, and daily study goal.
  * Frontend Auth UI: Clean, responsive login and registration modals, protected route guards, student profile editor.
* **Exit Criteria:**
  * Student can register, log in, complete academic onboarding, and view their dashboard.
  * Passwords verified hashed with Argon2id / bcrypt.
  * Automated integration tests verify unauthorized requests return 401/403.

---

### Milestone 3: Curriculum Hierarchy & Structured Lesson Viewer
* **Status:** Completed & Verified (October 15, 2026)
* **Goal:** Implement the academic taxonomy (Board -> Grade -> Subject -> Chapter -> Topic), content models (`lessons`, `lesson_sections`), publication lifecycle controls, and high-quality Markdown + KaTeX lesson viewer.
* **Deliverables Delivered:**
  * Seed data for initial syllabus: CBSE Class 12 Physics, Chemistry, and Mathematics core chapters and published lessons with KaTeX math and worked examples.
  * Publication gating: Distinct DRAFT and IN_REVIEW lessons seeded and confirmed 100% excluded from public/student endpoints (returning 404).
  * Backend endpoints to query syllabus hierarchy (`/subjects/{id}/chapters`, `/chapters/{id}/topics`, `/topics/{id}/lessons`, `/lessons/{id}`).
  * Alembic migration `ac0e5ff2e448` extending the database schema to 11 tables.
  * Frontend Curriculum Browser & Lesson Viewer: Responsive hierarchy navigation, breadcrumbs, KaTeX mathematical typesetting, and distinct styling for Concept, Key Formula, Worked Example, and Note sections.
  * 11 new backend tests (47 total passing) + 9 new frontend tests (19 total passing).
* **Exit Criteria Verified:**
  * Navigation seamlessly transitions through Board -> Grade -> Subject -> Chapter -> Topic -> Lesson.
  * Complex multi-line equations and chemical formulas render with zero typesetting glitches via KaTeX.
  * All 47 backend and 19 frontend unit and integration tests pass with zero failures.

---

### Milestone 4: Question Bank, Assessment Engine & Answer Validation
* **Status:** Completed & Verified (October 15, 2026)
* **Goal:** Build the practice engine with instant evaluation, verified step-by-step solutions, and attempt tracking.
* **Deliverables Delivered:**
  * Six database entities (`Question`, `QuestionOption`, `QuestionAnswerKey`, `PracticeSession`, `QuestionAttempt`, `QuestionErrataReport`) via Alembic migration `0cb437c7683c`.
  * Support for Single-Choice (MCQ), Multiple-Choice (Multi-select), Numerical with tolerance, and Integer question types.
  * Strict answer key security invariant: public and student question listing endpoints never leak answer keys or educator solutions.
  * Editorial publication gating: `DRAFT` and `IN_REVIEW` questions are 100% excluded from student endpoints.
  * Backend endpoints for question retrieval, session creation, IDOR-protected session status, atomic answer evaluation, errata reporting, and practice history.
  * Authentic CBSE Class 12 Physics, Chemistry, and Mathematics questions seeded with KaTeX formulas and step-by-step solutions.
  * Interactive Frontend Practice Engine: `QuestionCard`, `PracticeModal`, `ErrataModal`, and dashboard practice history.
  * 14 new backend tests (61 total passing) + 5 new frontend tests (24 total passing).
* **Exit Criteria Verified:**
  * Topic practice session can be launched from curriculum browser or lesson viewer, answered, scored, and reviewed.
  * Tolerance evaluation, integer validation, multi-select matching, and draft exclusion verified by automated test suites.
  * Question errata reporting verified persisting into database with issue types.

---

### Milestone 5: Student Analytics, Progress Tracking & Learning-Gap Analysis
* **Status:** Completed & Verified (October 16, 2026)
* **Goal:** Provide students with deep diagnostic insights into topic mastery, practice volume, weak conceptual areas, and explainable next-step recommendations.
* **Deliverables Delivered:**
  * Database entity `LessonProgress` with unique `(user_id, lesson_id)` constraint via Alembic migration `be8ed8718838` (18 tables active).
  * Dynamic practice metric aggregation directly from `question_attempts` and `practice_sessions` ensuring zero state drift.
  * Deterministic topic performance classifier with 4 categories: `INSUFFICIENT_DATA` (<5 Qs), `NEEDS_REVIEW` (>=5 Qs, <60%), `DEVELOPING` (>=5 Qs, 60-79.9%), and `STRONG` (>=5 Qs, >=80%).
  * Explainable rule-based learning recommendation engine prioritizing active lessons, revision targets, confidence drills, and syllabus progression.
  * Student Dashboard with 5-KPI analytics bar, interactive topic performance matrix with status badges, recommendation cards, recent activity timeline, and new-student empty state.
  * Lesson Viewer with automatic progress initiation, status header badges, and explicit lesson completion action.
  * Curriculum Browser with lesson completion status pills (`Completed`, `In Progress`, `Not Started`).
  * DPDP Act 2023 compliant cascading cleanup of all progress and practice records on account deletion.
  * 17 new tests: 8 new backend tests (78 total passing) + 3 new frontend tests (27 total passing across 8 suites).
* **Exit Criteria Verified:**
  * Lesson start and completion persist idempotently with ISO timestamps.
  * Topic accuracy and practice metrics recalculate dynamically on question submission.
  * All 78 backend Pytest tests and 27 frontend Vitest tests pass with 100% success rate.
  * Production frontend build passes with 0 TypeScript errors.

---

### Milestone 6: Study Planner & Learning Roadmap
* **Status:** Completed & Verified (October 16, 2026)
* **Goal:** Enable students to manage daily study goals, receive prioritized daily study task lists, and track their curriculum roadmap across subjects.
* **Deliverables Delivered:**
  * Database entities `StudyGoal` and `StudyTask` via Alembic migration `0c92f4b6848c` (20 tables active).
  * 4-tier deterministic task generator capped at a strict ceiling of 4 tasks per day and bounded by student's daily time budget (15–300 minutes, default 120 minutes).
  * Anti-snowball missed-day policy marking incomplete past tasks as `SKIPPED` without deleting history.
  * Task rescheduling (`POST /api/v1/planner/tasks/{id}/reschedule`) and atomic task completion toggle.
  * Hierarchical curriculum roadmap endpoint (`GET /api/v1/planner/roadmap`) detailing syllabus completion per enrolled subject and chapter.
  * Frontend UI: `DailyStudyPlanCard` (positioned directly beneath the 5-KPI section), `CurriculumRoadmapCard`, and `StudyGoalModal`.
  * DPDP Act 2023 compliant cascading deletion of study goals and tasks on student account erasure.
  * 18 new automated tests: 11 backend Pytest tests (89 total passing) + 7 frontend Vitest tests (34 total passing across 9 suites).
* **Exit Criteria Verified:**
  * Daily plans generated deterministically with a maximum of 4 tasks matching the time budget.
  * Task completion toggle updates task status without mutating lesson progress records.
  * All 89 backend Pytest tests and 34 frontend Vitest tests pass with 100% success rate.
  * Frontend production build passes with 0 TypeScript errors.

---

### Milestone 7: Spaced Repetition Scheduling & Active Recall Queue
* **Status:** Completed & Verified (October 2026)
* **Goal:** Enable students to retain long-term memory through automated revision queues and SM-2 active recall scheduling.
* **Deliverables Delivered:**
  * Implementation of SuperMemo SM-2 algorithm: Computes interval ($I_1=1, I_2=6, I_n=I_{n-1} \cdot EF$) and E-Factor adjustments bounded at $1.3$.
  * Relational entities `ReviewItem` and `ReviewLog` via Alembic migration `7d1a2b3c4e5f`.
  * Daily Revision Queue widget on student dashboard and `FlashcardReviewModal` with keyboard controls.
  * DPDP Act 2023 cascading erasure of review records upon student account deletion.
* **Exit Criteria Verified:**
  * Questions missed during practice are automatically enqueued for revision in `review_items`.
  * Unit tests verify mathematical correctness of interval and ease-factor adjustments.

---

### Milestone 8: Diagnostic Trends, Performance Classification & Analytics Methodology
* **Status:** Completed & Verified (October 2026)
* **Goal:** Provide longitudinal mastery trends, mathematical transparency, and accessibility.
* **Deliverables Delivered:**
  * Endpoint `GET /api/v1/student/analytics/trends` and `PracticeTrendChart` component with accessible screen-reader tables.
  * `AnalyticsMethodologyModal` documenting diagnostic algorithms and classification boundaries.
  * Alembic migration `0cbebed2ada2` (head).

---

### Milestone 9 & Phase B2: Production Hardening, Reverse Proxy & PostgreSQL Recovery Drill
* **Status:** Completed & Verified (October 2026)
* **Goal:** Final security review, reverse proxy configuration, automated PostgreSQL backup and restore recovery drill in CI.
* **Deliverables Delivered:**
  * Nginx reverse proxy routing, SSL/TLS termination, HTTP security headers, and cookie isolation.
  * Production-safe backup (`scripts/backup_postgres.sh`) and standalone restore (`scripts/restore_postgres.sh`) utilities.
  * Automated recovery drill in CI (`tests/test_backup_restore_drill.py`) verifying synthetic schema restoration and teardown on PostgreSQL 15.

---

### Phase C: Autonomous Audit, Security Hardening & Release Readiness Pass
* **Status:** Completed & Verified (October 2026)
* **Goal:** Cross-curriculum isolation, planner concurrency serialization, modal accessibility, and end-to-end student journey testing.
* **Deliverables Delivered:**
  * Enforced curriculum isolation in recommendations (`analytics.py`), eliminating cross-curriculum leaks.
  * Serialized task rescheduling via row-level User locks and mutexes (`planner.py`).
  * Modal dialog accessibility with Escape key listeners, backdrop dismissal, and isolated state lifecycles.
  * Comprehensive end-to-end student journey integration test suite (`tests/test_student_journey_e2e.py`).
  * GitHub Actions CI modernized to `ubuntu-24.04` and Actions `v7` running on Node 24.
* **Exit Criteria Verified:**
  * 240 backend Pytest tests (234 passing locally, 6 skipped: 5 PostgreSQL + 1 drill; 100% passing in CI).
  * 48 frontend Vitest tests passing across 11 suites.
  * Remote CI run succeeded across all matrix jobs.

---

## 3. Risk Assessment & Mitigation Strategy

| Risk Factor | Probability | Impact | Mitigation Strategy |
| :--- | :---: | :---: | :---: |
| **Complex Math Rendering Lag on Mobile** | Medium | High | Use KaTeX over MathJax; memoize rendered equations; defer off-screen math blocks via lazy rendering. |
| **LLM Hallucinations in Science Concepts** | Medium | Critical | Strictly bound LLM with verified chapter excerpts (RAG); enforce prominent AI disclaimer; provide immediate one-click human educator solution. |
| **Local PostgreSQL Availability** | High | Low | Support both PostgreSQL (production target) and SQLite (`aiosqlite` local fallback) seamlessly via SQLAlchemy abstraction. |
| **Student Data Privacy Non-Compliance** | Low | Critical | Strict DPDP Act alignment; zero third-party trackers; parental consent workflow for minors; self-serve data erasure. |
