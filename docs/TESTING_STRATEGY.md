# Project Campus — Comprehensive Testing Strategy

**Document Version:** 1.0.0  
**Status:** Approved for Quality Assurance  
**Testing Frameworks:** Pytest, Vitest, Playwright, axe-core, k6  
**Last Updated:** October 2026  

---

## 1. Testing Philosophy & Guiding Principles

At Project Campus, software quality and educational correctness are inseparable:
1. **Never Invent Test Results:** A feature is never claimed to work based on conjecture or simulated assumptions. Every assertion must be proven by a passing, reproducible test suite.
2. **Deterministic Evaluation:** Student assessment scoring and spaced repetition algorithms must behave with 100% deterministic mathematical precision.
3. **Automated Quality Gates:** Pull requests cannot be merged without clean linting, zero type errors, passing automated tests, and validated LaTeX syntax.
4. **Zero Flakiness:** Tests must be isolated, independent of external network availability, and clean up their test state automatically.

---

## 2. Testing Pyramid & Test Levels

```
                     / \
                    /   \
                   / E2E \       <-- Playwright (Critical Student Journeys)
                  /-------\
                 /  Integ  \     <-- Pytest + AsyncClient (API & DB Operations)
                /-----------\
               /    Unit     \   <-- Pytest (Domain Services) & Vitest (React Components)
              /---------------\
             / Static Analysis \ <-- Ruff, Mypy, ESLint, TypeScript Compiler, KaTeX Validator
            /-------------------\
```

### 2.1. Static Analysis & Type Checking
* **Backend:**
  * **Ruff:** Ultra-fast linting and code formatting conforming to PEP 8.
  * **Mypy:** Strict static type analysis with `--strict` mode enforced across all domain models, schemas, and services.
* **Frontend:**
  * **TypeScript (`tsc --noEmit`):** Strict null checks and complete interface enforcement.
  * **ESLint & Prettier:** Automated code style and React hook dependency enforcement.
* **Content / LaTeX Syntax Linter:**
  * Automated validator parses every question and lesson LaTeX string to guarantee zero unescaped brackets or unsupported KaTeX macros before saving.

### 2.2. Unit Testing
* **Backend Unit Tests (Pytest):**
  * **Assessment Evaluation Engine:** Validates Single-Choice matching, Multi-Choice partial and full scoring, Numerical tolerance bounds (e.g., $9.81 \pm 0.05$), and Integer verification.
  * **Spaced Repetition Engine (SM-2):** Tests interval progressions ($I(1) = 1, I(2) = 6$), ease factor adjustments ($EF' = EF + (0.1 - (5 - q) \cdot (0.08 + (5 - q) \cdot 0.02))$), and boundary clamps ($EF \ge 1.3$).
  * **Analytics Aggregator:** Tests topic mastery score calculations, accuracy percentage edge cases (0 attempts, 100% accuracy), and learning gap tier classification.
* **Frontend Unit Tests (Vitest + React Testing Library):**
  * Presentation components: `Button`, `Modal`, `Alert`, `MathRenderer`.
  * Practice components: `QuestionCard` renders options, handles selection, triggers callbacks.
  * Accessibility: Screen-reader labels present on interactive controls.

### 2.3. Integration Testing (API & Database)
* **Framework:** `pytest-asyncio` with `httpx.AsyncClient` executing against an isolated test database.
* **Database Strategy:**
  * Migrations are executed via Alembic on the test database prior to test execution.
  * Each test function executes within a transactional rollback block or uses a dedicated ephemeral database container to ensure 100% test isolation.
* **Key Integration Test Suites:**
  * **Auth & Security:** User registration, duplicate email rejection, password verification, expired JWT rejection, role-based authorization denials (e.g., Student trying to publish a question).
  * **Curriculum Traversal:** Fetching syllabus trees, handling non-existent subject IDs with 404 responses.
  * **Assessment Lifecycle:** Starting a practice session, submitting individual attempts, verifying atomic score increments and mastery updates.
  * **Errata Reporting:** Student submitting an errata ticket, reviewer fetching queue, reviewer updating question status.

### 2.4. End-to-End (E2E) Testing (Playwright)
Playwright tests simulate real user interactions in headless Chromium, Firefox, and WebKit across desktop and mobile viewports:

* **Journey 1 (Student Core Onboarding & Practice):**
  1. Student navigates to landing page.
  2. Registers with valid credentials.
  3. Completes onboarding survey (selects CBSE 12, Physics).
  4. Selects Chapter "Electrostatics" -> Topic "Coulomb's Law".
  5. Reads lesson and renders LaTeX equations.
  6. Starts practice drill: Answers Question 1 correctly, Question 2 incorrectly.
  7. Verifies instant feedback and step-by-step solution display.
  8. Navigates to Dashboard: Verifies mastery score reflects attempt.
  9. Verifies Question 2 appears in Daily Revision Queue.
* **Journey 2 (Educator Content Authoring & Editorial Sign-off):**
  1. Educator logs in, enters Author CMS.
  2. Creates new question with LaTeX stem and options.
  3. Previews KaTeX rendering live.
  4. Submits for review (`status = UNDER_REVIEW`).
  5. Reviewer logs in, reviews question in queue, approves it.
  6. Question is now published and available in student practice drills.

### 2.5. Accessibility & Mobile Responsive Testing
* **Automated Accessibility Testing:** `@axe-core/playwright` runs during E2E test passes. Zero critical or serious accessibility violations permitted.
* **Keyboard Navigation Audits:** Focus traps inside modals, tab traversal through quiz options, Enter/Space key submission.
* **Viewport Matrix:** Automated screenshot and layout regression checks on:
  * Mobile Portrait: 360 x 800 (Samsung Galaxy / Android standard)
  * Mobile Modern: 390 x 844 (iPhone 14/15)
  * Tablet: 768 x 1024 (iPad)
  * Desktop: 1440 x 900 and 1920 x 1080

### 2.6. Performance & Load Benchmarking
* **Tool:** `k6` or `Locust`.
* **Targets:**
  * 100 concurrent students taking practice quizzes: API p95 response time $< 250$ms.
  * Cache hit ratio on published syllabus endpoints $\ge 95\%$.

---

## 3. Test Automation & CI/CD Pipeline Gates

Every pull request must pass the following automated gate stages in sequence:

```mermaid
flowchart LR
    Commit["Git Push / PR"] --> LintCheck["1. Lint & Format\n(Ruff, ESLint, Prettier)"]
    LintCheck --> TypeCheck["2. Strict Type Check\n(Mypy, tsc)"]
    TypeCheck --> LaTeXCheck["3. Educational Content\nLaTeX Syntax Check"]
    LaTeXCheck --> UnitInteg["4. Unit & Integration Tests\n(Pytest, Vitest)"]
    UnitInteg --> E2E["5. E2E & A11y Tests\n(Playwright, Axe)"]
    E2E --> MergeReady["PR Merge Approved"]
```

---

## 4. Content Integrity Automated Check Suite

To enforce the Content Quality Policy, the repository includes an automated pedagogical validation test suite (`tests/content/test_content_integrity.py`):

1. **LaTeX Compilability Check:** Every question and lesson string is tested against KaTeX grammar to catch unclosed brackets, invalid math commands, or malformed matrices.
2. **Single-Choice Integrity:** Verifies that every `SINGLE_CHOICE` question has exactly one option matching the answer key.
3. **Multiple-Choice Integrity:** Verifies that every `MULTIPLE_CHOICE` question has $\ge 1$ correct options and $\le$ total options.
4. **Numerical Bounds Check:** Verifies that every `NUMERICAL` question specifies a non-null numerical value and a positive tolerance ($\delta > 0$).
5. **Solution Completeness:** Asserts that every published question has a non-empty `step_by_step_explanation_latex` of at least 50 characters.
