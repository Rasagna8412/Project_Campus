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
* **Goal:** Provide students with deep diagnostic insights into topic mastery, time management, and weak conceptual areas.
* **Deliverables:**
  * Calculation engine for `topic_mastery` (accuracy %, attempt count, mastery score).
  * Learning-Gap Classifier: Automatically categorizes topics into "Mastered" ($\ge 85\%$), "Developing" ($60-84\%$), and "Struggling / Needs Revision" ($<60\%$).
  * Visual Analytics Dashboard: Interactive mastery heatmaps, accuracy by subject, and time spent metrics.
* **Exit Criteria:**
  * Accuracy metrics recalculate accurately in real-time upon question submission.
  * Visual charts render crisply on both mobile viewports and desktop browsers.

---

### Milestone 6: Transparent AI Concept Clarifier (Grounded RAG)
* **Goal:** Implement the contextual AI tutor with strict syllabus grounding, clear provenance, and safety guardrails.
* **Deliverables:**
  * Backend AI Gateway service supporting pluggable LLM providers (Google Gemini / Anthropic / OpenAI / Local Ollama) with prompt sanitization.
  * Grounded context injection: Pulls relevant chapter text into the system prompt.
  * Frontend Chat Drawer: Floating AI concept assistant inside lessons and practice questions with distinct purple AI badge and disclaimer.
  * Student feedback logging (`Helpful` / `Unclear` / `Inaccurate`).
* **Exit Criteria:**
  * AI assistant successfully answers concept clarification questions bounded to the active chapter.
  * System prompt blocks prompt injection attempts and refuses to output direct keys to unattempted tests.
  * Visual AI disclaimer is prominently displayed on 100% of AI messages.

---

### Milestone 7: Spaced Repetition Scheduling & Study Planner
* **Goal:** Enable students to retain long-term memory through automated revision queues and exam preparation milestones.
* **Deliverables:**
  * Implementation of SuperMemo SM-2 algorithm: Computes next review date ($1, 3, 7, 21$ days) based on answer accuracy and student confidence rating.
  * Daily Revision Queue widget on student dashboard.
  * Exam countdown timer and daily study hour tracking.
* **Exit Criteria:**
  * Questions missed during practice are automatically enqueued for revision in `revision_items`.
  * Unit tests verify mathematical correctness of interval and ease-factor adjustments.

---

### Milestone 8: Mobile Optimization, Accessibility & End-to-End Hardening
* **Goal:** Ensure flawless mobile responsiveness, WCAG 2.1 AA accessibility, and thorough end-to-end user journey validation.
* **Deliverables:**
  * Responsive design audit: Validated on 360px, 390px, 768px, 1024px, and 1440px widths.
  * Accessibility audit: Keyboard navigation for all practice flows, high contrast ratios, screen-reader MathML/aria-labels.
  * Comprehensive Playwright E2E test suite covering student onboarding to exam completion.
  * Performance tuning: Bundle optimization, image compression, API response caching in Redis.
* **Exit Criteria:**
  * 0 critical accessibility violations under `axe-core` scan.
  * Playwright tests pass 100% in headless CI.
  * Lighthouse score $\ge 90$ on Performance, Accessibility, and Best Practices.

---

### Milestone 9: Production Readiness, Security Review & Pilot Launch
* **Goal:** Final security penetration testing, production deployment configuration, and onboarding of pilot student cohort.
* **Deliverables:**
  * Production Docker builds and CI/CD GitHub Actions / GitLab CI workflows.
  * Penetration testing check: OWASP Top 10 automated vulnerability scanning.
  * Database backup automation and disaster recovery playbook.
  * Pilot onboarding guide and system monitoring dashboards (Prometheus / Grafana or CloudWatch).
* **Exit Criteria:**
  * Zero high/critical vulnerability findings in security scan.
  * Clean end-to-end smoke test on production staging environment.
  * Formal sign-off for public pilot launch.

---

## 3. Risk Assessment & Mitigation Strategy

| Risk Factor | Probability | Impact | Mitigation Strategy |
| :--- | :---: | :---: | :---: |
| **Complex Math Rendering Lag on Mobile** | Medium | High | Use KaTeX over MathJax; memoize rendered equations; defer off-screen math blocks via lazy rendering. |
| **LLM Hallucinations in Science Concepts** | Medium | Critical | Strictly bound LLM with verified chapter excerpts (RAG); enforce prominent AI disclaimer; provide immediate one-click human educator solution. |
| **Local PostgreSQL Availability** | High | Low | Support both PostgreSQL (production target) and SQLite (`aiosqlite` local fallback) seamlessly via SQLAlchemy abstraction. |
| **Student Data Privacy Non-Compliance** | Low | Critical | Strict DPDP Act alignment; zero third-party trackers; parental consent workflow for minors; self-serve data erasure. |
