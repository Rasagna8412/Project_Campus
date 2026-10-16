# Project Campus — Milestone 4 Security, Correctness, and Quality Audit Report

**Audit Date:** October 16, 2026  
**Auditor Role:** Senior Application Security Engineer & Assessment Platform Quality Lead  
**Baseline Git Commit:** `e662554` (`feat: complete milestone 4 question bank, practice engine, and assessment foundation`)  
**Audit Target:** Question Bank, Topic-Based Practice Engine, Evaluation Services, and Assessment Foundation  

---

## 1. Executive Summary & Verification Decision

An independent security, correctness, and regression audit of Project Campus Milestone 4 was conducted on top of baseline commit `e662554`. The evaluation systematically inspected question confidentiality invariants, scoring engine precision, option validity enforcement, session lifecycle state machines, authorization and IDOR protections, editorial content barriers, and test suite health across both frontend and backend stacks.

### Formal Verification Decision:
> **PASSED WITH RESOLVED AUDIT DEFECTS AND DOCUMENTED OPERATIONAL LIMITATIONS**
> **READY FOR MILESTONE 5 PLANNING & EXECUTION**

All confirmed defects discovered during the audit—including a cross-student session attempt injection vulnerability, duplicate submission score inflation, floating-point tolerance boundary comparison failure, non-finite float serialization crashes, and unvalidated option keys—have been remediated with surgical, safe fixes and verified by 9 targeted automated audit tests. The full backend test suite passes with 70/70 tests, the frontend test suite passes with 24/24 tests across 7 test suites, and the frontend production build completes with zero errors.

---

## 2. Audit Scope & Files Inspected

The following repository components were inspected line-by-line during the audit:

| Component | File Path | Focus Area |
| :--- | :--- | :--- |
| **Assessment Models** | [`backend/app/models/assessment.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/models/assessment.py) | `Question`, `QuestionOption`, `QuestionAnswerKey`, `PracticeSession`, `QuestionAttempt`, `QuestionErrataReport`, relationships, cascade behaviors, and default timestamps |
| **Assessment Schemas** | [`backend/app/schemas/assessment.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/schemas/assessment.py) | Public response schemas (`QuestionPublicResponse`, `PracticeSessionResponse`), submission schemas (`SubmitAnswerRequest`, `SubmitAnswerResponse`), answer-key exclusion |
| **Practice API Endpoints** | [`backend/app/api/v1/endpoints/practice.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/practice.py) | Question retrieval, session generation, answer grading logic, tolerance boundaries, session ownership, attempt storage, errata submission, attempt history |
| **Application & Handlers** | [`backend/app/main.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/main.py) | `RequestValidationError` handling, sanitization of non-finite float values (NaN, Infinity), and global exception shielding |
| **Database Migrations** | [`backend/alembic/versions/741e469d76c7_milestone_4_question_bank_and_practice_.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/alembic/versions/741e469d76c7_milestone_4_question_bank_and_practice_.py) | Foreign keys, indexes, table structures, and constraints |
| **Frontend UI Components** | [`frontend/src/components/Practice.tsx`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/frontend/src/components/Practice.tsx) | Practice session runner, single/multiple choice options, numerical/integer input fields, feedback display, LaTeX formatting, errata modal |
| **Frontend Services** | [`frontend/src/services/api.ts`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/frontend/src/services/api.ts) | Practice API client methods (`getTopicQuestions`, `createPracticeSession`, `submitAnswer`, `getPracticeSession`, `reportErrata`, `getStudentPracticeHistory`) |
| **Automated Test Suites** | [`tests/test_practice.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/tests/test_practice.py), [`tests/test_practice_audit.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/tests/test_practice_audit.py), [`frontend/src/test/Practice.test.tsx`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/frontend/src/test/Practice.test.tsx) | Baseline and targeted security audit assertions covering confidentiality, math boundaries, IDOR, score inflation, and history isolation |

---

## 3. Answer-Key Confidentiality Invariant Analysis

A core security requirement of Project Campus is that **no answer keys, correct option flags, numerical target values, or worked explanations may be revealed to students before they submit their answers**.

### Endpoint Tracing & Verification:

1. **`GET /api/v1/practice/topics/{topic_id}/questions`**:
   - Serializes questions via `QuestionPublicResponse`.
   - Options are serialized via `QuestionOptionPublicResponse`, containing only `id`, `option_key`, `content_latex`, and `order_index`.
   - The fields `is_correct`, `answer_key`, `correct_options`, `numerical_value`, `numerical_tolerance`, `integer_value`, and `explanation_latex` are strictly excluded from the schema and SQL query serialization.
   - Verified by test `test_audit_answer_key_never_leaked_in_question_lists`.

2. **`POST /api/v1/practice/sessions`**:
   - Returns a `PracticeSessionResponse` embedding questions typed as `QuestionPublicResponse`.
   - Verified that no secret evaluation fields or explanation LaTeX are included in session creation.
   - Verified by test `test_audit_answer_key_never_leaked_in_session_creation_or_status`.

3. **`GET /api/v1/practice/sessions/{session_id}`**:
   - Returns session progress and questions as `QuestionPublicResponse`.
   - Strictly enforces session ownership (`session.user_id == current_user.id`), returning `404 Not Found` for unauthorized students to prevent session reconnaissance.
   - Verified by test `test_practice_session_idor_protection`.

4. **`GET /api/v1/practice/history`**:
   - Returns historical `QuestionAttemptResponse` items for the authenticated user only.
   - Only displays `is_correct`, submitted options/values, and time spent. Does not expose private keys of unattempted questions.
   - Verified by test `test_audit_history_isolation_between_two_students`.

5. **`POST /api/v1/practice/submit`**:
   - Answer key and detailed explanation LaTeX are revealed **only after** an answer is submitted and stored.
   - Response contains `is_correct`, `correct_options`, `numerical_value`, and `explanation_latex` to provide constructive pedagogical feedback.

**Verdict on Confidentiality:** **PASSED IN FULL.** No pre-submission answer leakage exists in the API or frontend layers.

---

## 4. Audit Findings & Remediations Registry

### Finding Summary

| ID | Title | Severity | Status | Scope |
| :--- | :--- | :---: | :---: | :---: |
| **AUD-01** | Cross-Student Session Attempt Injection (IDOR via `session_id`) | **HIGH** | **RESOLVED** | Authorization / Data Integrity |
| **AUD-02** | Duplicate Question Submission Permitted Score Inflation | **MEDIUM** | **RESOLVED** | Scoring Engine |
| **AUD-03** | IEEE 754 Binary Floating-Point Exact Tolerance Boundary Failure | **MEDIUM** | **RESOLVED** | Numerical Precision |
| **AUD-04** | Non-Finite Float Inputs (NaN / Infinity) Caused Unhandled 500 Error | **MEDIUM** | **RESOLVED** | Robustness / Validation |
| **AUD-05** | Question Option Keys Lacked Question Association Validation | **LOW** | **RESOLVED** | Input Validation |
| **AUD-06** | Answer Submissions Permitted on Completed Practice Sessions | **LOW** | **RESOLVED** | State Machine Lifecycle |
| **AUD-07** | Use of Deprecated `datetime.utcnow` in `QuestionAttempt` Model | **INFORMATIONAL** | **RESOLVED** | Code Quality |
| **AUD-08** | Client-Reported `time_spent_seconds` Untrusted Execution Context | **INFORMATIONAL** | **DOCUMENTED** | Anti-Tampering |

---

### Detailed Audit Findings & Technical Remediations

#### Finding AUD-01: Cross-Student Session Attempt Injection (IDOR via `session_id`)
* **Severity:** **HIGH**
* **Location:** [`backend/app/api/v1/endpoints/practice.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/practice.py)
* **Description:**
  When invoking `POST /api/v1/practice/submit`, if a student supplied a valid `session_id` belonging to *another* student, the endpoint failed to validate session ownership before recording the attempt. The attempt was committed to the database with `attempt.session_id = victim_session.id`. While the session progress increment checked `session.user_id == current_user.id`, the foreign key association remained intact, polluting the victim student's session attempt list and corrupting subsequent completion counts.
* **Remediation:**
  Enforced strict session ownership validation prior to processing any submission:
  ```python
  session = None
  if payload.session_id:
      session = await db.get(PracticeSession, payload.session_id)
      if not session or session.user_id != current_user.id:
          raise HTTPException(
              status_code=status.HTTP_404_NOT_FOUND,
              detail="Practice session not found",
          )
  ```
  Returns `404 Not Found` to prevent session enumeration or unauthorized linkage. Verified via `test_audit_session_ownership_cross_student_submission_protection`.

---

#### Finding AUD-02: Duplicate Question Submission Permitted Score Inflation
* **Severity:** **MEDIUM**
* **Location:** [`backend/app/api/v1/endpoints/practice.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/practice.py)
* **Description:**
  A student could submit an answer for the same question multiple times within a single session. On each correct submission, `session.correct_count` was incremented and the total attempt count grew, allowing a student to artificially inflate their score and prematurely complete the session without attempting other questions.
* **Remediation:**
  Added an idempotency check querying `QuestionAttempt` within the session before grading:
  ```python
  if session:
      existing_stmt = select(QuestionAttempt.id).where(
          QuestionAttempt.session_id == session.id,
          QuestionAttempt.question_id == question.id,
      )
      if (await db.execute(existing_stmt)).scalar_one_or_none():
          raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
              detail="Question already submitted in this session",
          )
  ```
  Verified via `test_audit_duplicate_submission_score_inflation`.

---

#### Finding AUD-03: IEEE 754 Binary Floating-Point Exact Tolerance Boundary Failure
* **Severity:** **MEDIUM**
* **Location:** [`backend/app/api/v1/endpoints/practice.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/practice.py)
* **Description:**
  Numerical answers evaluated `abs(submitted - target) <= tol`. Due to IEEE 754 binary floating-point representation, an exact boundary value such as target `0.008` with tolerance `0.001` and submitted value `0.009` yielded `abs(0.009 - 0.008) = 0.0010000000000000009`. Because this exceeded `0.001` by `9e-17`, mathematically correct answers on exact tolerance boundaries were marked incorrect.
* **Remediation:**
  Incorporated an epsilon relaxation into the tolerance comparison:
  ```python
  # Use tol + 1e-9 to avoid binary floating-point roundoff at exact boundary
  is_correct = abs(payload.submitted_numerical - answer_key.numerical_value) <= (tol + 1e-9)
  ```
  Verified via `test_audit_numerical_tolerance_exact_boundaries`.

---

#### Finding AUD-04: Non-Finite Float Inputs (NaN / Infinity) Caused Unhandled 500 Error
* **Severity:** **MEDIUM**
* **Location:** [`backend/app/schemas/assessment.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/schemas/assessment.py) and [`backend/app/main.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/main.py)
* **Description:**
  When a client submitted raw JSON containing `NaN` or `Infinity` for `submitted_numerical`, Pydantic rejected it under `allow_inf_nan=False`, generating a `RequestValidationError` with `input: nan`. When FastAPI attempted to serialize this error detail into a 422 JSON response, Python's standard `json.dumps()` crashed with `ValueError: Out of range float values are not JSON compliant: nan`, causing the global exception handler to catch an unhandled exception and return a `500 Internal Server Error`.
* **Remediation:**
  1. Configured `submitted_numerical: Optional[float] = Field(default=None, allow_inf_nan=False)` in `SubmitAnswerRequest`.
  2. Implemented a dedicated `@app.exception_handler(RequestValidationError)` in `backend/app/main.py` that recursively sanitizes non-finite floats (converting `nan` and `inf` to strings) prior to serialization with `jsonable_encoder`.
  3. Ensured `math.isfinite(payload.submitted_numerical)` is validated in the practice endpoint.
  Returns `422 Unprocessable Content` gracefully. Verified via `test_audit_numerical_nan_and_inf_handling`.

---

#### Finding AUD-05: Question Option Keys Lacked Question Association Validation
* **Severity:** **LOW**
* **Location:** [`backend/app/api/v1/endpoints/practice.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/practice.py)
* **Description:**
  In single-choice and multiple-choice questions, the API accepted arbitrary option keys in `selected_options` (e.g., `["Z"]` or `["INVALID_KEY"]`), silently recording them in the database attempt table without checking if those keys were valid choices for that question.
* **Remediation:**
  Added validation ensuring `set(payload.selected_options).issubset(valid_keys)` where `valid_keys` are extracted from `question.options`. Rejects invalid option submissions with `400 Bad Request: "Selected options do not belong to this question"`. Verified via `test_audit_option_keys_must_belong_to_question`.

---

#### Finding AUD-06: Answer Submissions Permitted on Completed Practice Sessions
* **Severity:** **LOW**
* **Location:** [`backend/app/api/v1/endpoints/practice.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/api/v1/endpoints/practice.py)
* **Description:**
  The submission handler did not verify `session.is_completed`. A student could continue submitting attempts to a session that had already concluded and received a completion timestamp.
* **Remediation:**
  Added a guard:
  ```python
  if session.is_completed:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Practice session is already completed",
      )
  ```
  Verified via `test_audit_submission_to_completed_session`.

---

#### Finding AUD-07: Use of Deprecated `datetime.utcnow` in `QuestionAttempt` Model
* **Severity:** **INFORMATIONAL**
* **Location:** [`backend/app/models/assessment.py`](file:///c:/Users/LOQ/OneDrive/Desktop/project_campus/backend/app/models/assessment.py#L270)
* **Description:**
  The `attempted_at` column used `default=datetime.utcnow`, which is deprecated in Python 3.12+ and produces naive datetime objects without timezone awareness.
* **Remediation:**
  Updated to timezone-aware UTC datetime callable: `default=lambda: datetime.now(timezone.utc)`.

---

#### Finding AUD-08: Client-Reported `time_spent_seconds` Untrusted Execution Context
* **Severity:** **INFORMATIONAL**
* **Location:** Practice Client & Endpoint
* **Description:**
  The `time_spent_seconds` field is tracked by the student's browser timer and sent in the submission payload. While constrained by schema validation `ge=0`, in untrusted client environments an adversarial user could report fabricated durations (e.g., `0` seconds for complex multi-step problems).
* **Operational Assessment:**
  For formative, unproctored topic practice, client-side timing is standard industry practice. For high-stakes, proctored summative examinations in future milestones, server-side session timestamps (`started_at` vs `attempted_at`) and heartbeat monitoring should be mandated.

---

## 5. Content Editorial & Lifecycle Barriers

The assessment engine was audited to ensure strict separation between draft authoring and published student-facing materials:

1. **Editorial Status Filtering**:
   - `Question.status == ContentStatus.PUBLISHED.value` is strictly enforced on all question retrieval queries (`/topics/{id}/questions` and `/sessions`).
   - Questions in `DRAFT`, `IN_REVIEW`, or `ARCHIVED` statuses are never included in question lists or practice sessions.
2. **Direct Attempt Rejection for Unpublished Content**:
   - `POST /api/v1/practice/submit` queries questions with status `PUBLISHED`.
   - Attempting to submit an answer to a question in `DRAFT` or `IN_REVIEW` status returns `404 Not Found`, denying existence of unpublished content.
   - Verified by test `test_submit_answer_for_draft_question_returns_404`.

---

## 6. Comprehensive Verification & Test Execution Evidence

### Backend Pytest Results (70/70 Tests Passing)

```text
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\LOQ\OneDrive\Desktop\project_campus
plugins: anyio-4.15.1, asyncio-1.4.0
collected 70 items

tests/test_auth.py .............                                         [ 18%]
tests/test_authorization.py ........                                     [ 30%]
tests/test_content.py ...........                                        [ 45%]
tests/test_database.py ..                                                [ 48%]
tests/test_error_handling.py ...                                         [ 52%]
tests/test_health.py ...                                                 [ 57%]
tests/test_models.py ...                                                 [ 61%]
tests/test_onboarding.py ....                                            [ 67%]
tests/test_practice.py .............                                     [ 87%]
tests/test_practice_audit.py .........                                   [100%]

============================= 70 passed in 30.27s =============================
```

### Frontend Vitest Results (24/24 Tests Passing)

```text
 RUN  v4.1.11 C:/Users/LOQ/OneDrive/Desktop/project_campus/frontend

 ✓ src/test/LessonContentRenderer.test.tsx (5 tests) 437ms
 ✓ src/test/LessonViewer.test.tsx (2 tests) 1652ms
 ✓ src/test/CurriculumBrowser.test.tsx (2 tests) 1724ms
 ✓ src/test/Onboarding.test.tsx (2 tests) 1946ms
 ✓ src/test/Practice.test.tsx (5 tests) 1919ms
 ✓ src/test/App.test.tsx (4 tests) 1931ms
 ✓ src/test/Auth.test.tsx (4 tests) 3266ms

 Test Files  7 passed (7)
      Tests  24 passed (24)
   Start at  09:19:47
   Duration  12.94s
```

### Frontend Production Build (`tsc && vite build`)

```text
> project-campus-frontend@0.1.0 build
> tsc && vite build

vite v5.4.21 building for production...
transforming...
✓ 1593 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.78 kB │ gzip:   0.48 kB
dist/assets/index-Dn1Xst4-.css   36.49 kB │ gzip:   6.48 kB
dist/assets/index-C5s2-Kyz.js   519.98 kB │ gzip: 150.78 kB
✓ built in 10.29s
```

---

## 7. Audit Sign-Off & Recommendations for Milestone 5

### Gate Verdict:
**APPROVED FOR PROGRESSION TO MILESTONE 5.**

### Recommendations for Subsequent Milestones:
1. **Analytics Engine (Milestone 5):**
   - Leverage the immutable `QuestionAttempt` table for mastery calculations, calculating accuracy and pacing per topic.
   - Aggregate time-spent data with outlier trimming (capping single attempts at 600s) to prevent browser-idle skewing student analytics.
2. **Adaptive Practice:**
   - Future session generation can incorporate difficulty progression (EASY $\rightarrow$ MEDIUM $\rightarrow$ HARD) based on prior student attempt history.
3. **Errata Review Portal:**
   - Introduce administrative review workflows for `QuestionErrataReport` entries created by students during practice sessions.
