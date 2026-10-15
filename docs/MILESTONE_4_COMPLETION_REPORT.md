# Project Campus — Milestone 4 Completion Report

**Milestone:** 4 — Question Bank, Topic-Based Practice Engine, and Assessment Foundation  
**Status:** Completed & Formally Verified  
**Date:** October 15, 2026  
**Target Platform:** Indian Higher Secondary & Entrance Examinations (CBSE, JEE Main, NEET)

---

## 1. Executive Summary

Milestone 4 establishes the **Question Bank, Topic-Based Practice Engine, and Assessment Foundation** for Project Campus. Building upon the verified curriculum taxonomy, secure student identity system, and structured lesson delivery (Milestones 1–3), Milestone 4 transforms Project Campus into an active, deliberate learning environment.

Students can now practise questions linked to their selected curriculum topics, test their comprehension under authentic examination formats, submit answers, receive immediate atomic evaluation, study verified step-by-step educator derivations, and flag potential errata directly to editorial staff.

Key capabilities delivered in Milestone 4:
- **Comprehensive Question Bank Entities:** Supporting `single_choice`, `multiple_choice`, `numerical` (with decimal tolerance), and `integer` questions.
- **Answer Key Security Invariant:** Questions queried by students strictly exclude answer keys, correct option sets, numerical targets, integer targets, and derivations. Solutions and explanations are exposed only after a student submits their attempt.
- **Editorial Publication Safeguards:** Only questions marked `PUBLISHED` are queryable or evaluatable by learners. Questions in `DRAFT` or `IN_REVIEW` states return 404.
- **Deliberate Practice Sessions:** Topic-scoped practice session management with attempt recording, score tracking, completion status, and IDOR access control.
- **Student Errata Reporting Workflow:** Built-in error reporting mechanism for students to report answer key ambiguities, LaTeX rendering defects, and typos with categorized issue codes.
- **Interactive Mathematical Practice UI:** KaTeX-powered question prompt and option rendering, dynamic input controls per question type, instant evaluation banners, step-by-step solution reveals, and session accuracy summaries.

All pre-existing authentication, authorization, DPDP compliance, and lesson delivery controls from Milestones 1–3 remain 100% operational with zero regressions.

---

## 2. Regression & Operational Verification of Prior Milestones

A full regression inspection was conducted across the backend and frontend codebases:
1. **Milestones 1 & 2 Capabilities:**
   - FastAPI service, health endpoints (`/health`, `/api/v1/health?check_db=true`), Argon2id password hashing, JWT bearer tokens, cookie clearing on logout, IP rate limiting, DPDP Act student account erasure, and academic onboarding lifecycle remain intact.
2. **Milestone 3 Capabilities:**
   - Curriculum taxonomy navigation, chapter/topic retrieval, published lesson listing, and KaTeX mathematical lesson viewer with section types remain operational.
3. **Database Migration Lineage:**
   - Prior migrations (`6ec2307658ee` -> `eeac6986a79e` -> `ac0e5ff2e448`) were strictly preserved.
   - The new migration (`0cb437c7683c`) cleanly extends `ac0e5ff2e448` to form the new head.

---

## 3. Data Models, Relationships, and Alembic Migration

### 3.1 Assessment Entities
Six core assessment entities were implemented in `backend/app/models/assessment.py`:

```
                       ┌──────────────────────┐
                       │        Topic         │ (from taxonomy.py)
                       └──────────┬───────────┘
                                  │ 1
                                  │
                                  ▼ N
                       ┌──────────────────────┐
                       │       Question       │
                       │──────────────────────│
                       │ id (UUID, PK)        │
                       │ topic_id (UUID, FK)  │
                       │ lesson_id (UUID, FK) │
                       │ question_type (Enum) │ [single_choice, multiple_choice,
                       │ difficulty (Enum)    │  numerical, integer]
                       │ content_latex (Text) │ [EASY, MEDIUM, HARD]
                       │ status (Enum)        │ [DRAFT, IN_REVIEW, PUBLISHED]
                       │ is_verified (Bool)   │
                       └──────────┬───────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │ 1                     │ 1                     │ 1
          ▼ N                     ▼ 1                     ▼ N
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────────┐
│  QuestionOption   │   │ QuestionAnswerKey │   │ QuestionErrataReport  │
│───────────────────│   │───────────────────│   │───────────────────────│
│ id (UUID, PK)     │   │ id (UUID, PK)     │   │ id (UUID, PK)         │
│ question_id (FK)  │   │ question_id (FK)  │   │ question_id (FK)      │
│ option_key (Str)  │   │ correct_options   │   │ user_id (FK)          │
│ content_latex     │   │ numerical_value   │   │ issue_type (Enum)     │
│ order (Int)       │   │ tolerance (Float) │   │ description (Text)    │
└───────────────────┘   │ integer_value     │   │ status (Str)          │
                        │ explanation_latex │   └───────────────────────┘
                        └───────────────────┘
                                  │
                                  ▼ N
                       ┌──────────────────────┐
                       │   QuestionAttempt    │
                       │──────────────────────│
                       │ id (UUID, PK)        │
                       │ session_id (FK, opt) │
                       │ user_id (FK)         │
                       │ question_id (FK)     │
                       │ selected_options     │
                       │ numerical_value      │
                       │ integer_value        │
                       │ is_correct (Bool)    │
                       │ score (Float)        │
                       │ time_spent_seconds   │
                       └──────────────────────┘
                                  ▲ N
                                  │
                                  │ 1
                       ┌──────────────────────┐
                       │   PracticeSession    │
                       │──────────────────────│
                       │ id (UUID, PK)        │
                       │ user_id (FK)         │
                       │ topic_id (FK)        │
                       │ total_questions      │
                       │ correct_count        │
                       │ score (Float)        │
                       │ is_completed (Bool)  │
                       │ started_at (DateTime)│
                       │ completed_at         │
                       └──────────────────────┘
```

1. **`QuestionType` (Enum):**
   - `single_choice`: Traditional 4-option single-correct MCQ (CBSE / JEE Section A / NEET).
   - `multiple_choice`: Multi-correct MCQ requiring all correct choices to be marked (JEE Advanced style).
   - `numerical`: Floating-point numerical value evaluated with `tolerance` ($\pm \epsilon$).
   - `integer`: Single non-negative integer response (0–9 or integer grid-in).
2. **`DifficultyLevel` (Enum):**
   - `EASY`: Direct formula application and definitions.
   - `MEDIUM`: Multi-step reasoning and standard entrance problems.
   - `HARD`: Complex multi-concept synthesis and non-trivial approximations.
3. **`ErrataIssueType` (Enum):**
   - `INCORRECT_ANSWER`, `TYPO_OR_GRAMMAR`, `AMBIGUOUS_QUESTION`, `LATEX_RENDERING_ERROR`, `OTHER`.

### 3.2 Alembic Migration: `0cb437c7683c`
- Migration file: `backend/alembic/versions/0cb437c7683c_milestone_4_question_bank_and_assessment.py`
- Revises: `ac0e5ff2e448` (Milestone 3 head)
- Tables created: `questions`, `question_options`, `question_answer_keys`, `practice_sessions`, `question_attempts`, `question_errata_reports`.
- Includes foreign key constraints, cascade rules, indices on `(topic_id, status)` and `(user_id, topic_id)`, and unique constraints.
- Successfully applied and verified on development and isolated test databases.

---

## 4. Academic Questions Seeded & Content Quality

Authentic, syllabus-accurate questions across CBSE Class 12 and entrance examination curricula were implemented in `backend/app/core/seed_questions.py`:

| Subject | Topic | Question Type | Difficulty | Summary / Academic Core | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Physics** | Coulomb's Law & Superposition | `single_choice` | Medium | Force scaling when charges halved and distance doubled ($F' = F/16$). | `PUBLISHED` |
| **Physics** | Coulomb's Law & Superposition | `numerical` | Easy | Force magnitude between two $1\,\mu\text{C}$ charges at $1\,\text{m}$ ($F = 0.009\,\text{N}$, tolerance 0.001). | `PUBLISHED` |
| **Chemistry** | Rate Law & Order of Reaction | `single_choice` | Easy | Units of rate constant for first-order reaction ($\text{s}^{-1}$). | `PUBLISHED` |
| **Chemistry** | Rate Law & Order of Reaction | `integer` | Medium | Overall reaction order from rate law $r = k [A]^1 [B]^2$ ($1 + 2 = 3$). | `PUBLISHED` |
| **Mathematics** | Matrix Multiplication & Properties | `multiple_choice` | Hard | Non-commutativity and algebraic properties of matrix multiplication. | `PUBLISHED` |
| **Physics** | Coulomb's Law & Superposition | `single_choice` | Medium | Draft test question verifying student filtering. | `DRAFT` |
| **Physics** | Coulomb's Law & Superposition | `numerical` | Hard | In-review test question verifying editorial isolation. | `IN_REVIEW` |

Every answer key includes step-by-step educator derivations written in standard LaTeX, showing intermediate formulas, physical substitutions, algebraic rearrangements, and dimensional units.

---

## 5. API Endpoints Implemented

All endpoints are mounted under `/api/v1/practice`:

| Method | Endpoint | Access Control | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/practice/topics/{topic_id}/questions` | Public | Returns published questions for a topic. **Answer keys and derivations are strictly omitted.** |
| `POST` | `/api/v1/practice/sessions` | Authenticated Student | Starts a deliberate practice session batch for a topic with optional difficulty filtering. |
| `GET` | `/api/v1/practice/sessions/{session_id}` | Authenticated Student | Retrieves practice session status and questions. Protected against IDOR (403 for other students). |
| `POST` | `/api/v1/practice/submit` | Authenticated Student | Atomically evaluates student attempt, increments session progress, and returns educator derivation. |
| `POST` | `/api/v1/practice/questions/{id}/report-errata` | Authenticated Student | Submits errata report for a question with categorized issue type and description. |
| `GET` | `/api/v1/practice/history` | Authenticated Student | Retrieves student's recent practice sessions with total questions, correct counts, and accuracy. |

---

## 6. Frontend Practice Interface

1. **`frontend/src/types/assessment.ts`:**
   - Full TypeScript definitions for `StudentQuestion`, `QuestionOption`, `QuestionEvaluation`, `PracticeSession`, `PracticeSessionSummary`, and `ErrataReport`.
2. **`frontend/src/services/api.ts`:**
   - API client methods: `getTopicQuestions`, `createPracticeSession`, `getPracticeSession`, `submitAnswer`, `reportQuestionErrata`, `getPracticeHistory`.
3. **`frontend/src/components/practice/QuestionCard.tsx`:**
   - Interactive question display with KaTeX math rendering.
   - Dynamic answer input: radio options (single-choice), checkboxes (multiple-choice), decimal inputs (numerical), and integer inputs.
   - Instant visual feedback banner with correct/incorrect status.
   - Verified step-by-step educator derivation revealed upon submission.
   - Errata reporting shortcut button.
4. **`frontend/src/components/practice/PracticeModal.tsx`:**
   - Deliberate topic practice session modal.
   - Stepper navigation across questions with live completion status.
   - Session summary card with score breakdown, accuracy percentage, and pedagogical guidance.
5. **`frontend/src/components/practice/ErrataModal.tsx`:**
   - Categorized issue selection dropdown with live validation (minimum 10 characters).
   - Instant submission feedback and editorial team routing.
6. **Curriculum Integration:**
   - "Practise Questions" CTA button added to topic header in `CurriculumBrowser.tsx`.
   - "Ready to Test Your Understanding?" callout section added to `LessonViewer.tsx`.
   - "Practice & Assessment Activity" history card added to `StudentDashboard.tsx`.

---

## 7. Automated Test Suite & Verification Results

### 7.1 Backend Test Suite (Pytest)
Command: `pytest -v`  
Result: **61 passed, 0 failed, 100% pass rate** (in 17.46s)

Milestone 4 test coverage (`tests/test_practice.py` — 14 targeted tests):
- `test_get_topic_questions_published_only`: Confirms published questions returned without leaking answer keys.
- `test_topic_questions_draft_and_in_review_excluded`: Verifies `DRAFT` and `IN_REVIEW` questions are excluded from student queries.
- `test_get_topic_questions_nonexistent_topic_404`: Verifies 404 on invalid topic UUID.
- `test_create_practice_session_authenticated`: Verifies authenticated student can initialize practice sessions.
- `test_create_practice_session_unauthenticated_401`: Verifies unauthenticated session creation returns 401.
- `test_submit_single_choice_answer_correct`: Confirms correct evaluation (score 1.0) and reveals LaTeX explanation.
- `test_submit_single_choice_answer_incorrect`: Confirms incorrect evaluation (score 0.0) without crashing.
- `test_submit_numerical_answer_within_and_outside_tolerance`: Verifies floating-point tolerance logic ($0.009 \pm 0.001$).
- `test_submit_multiple_choice_answer`: Confirms all correct options required for multi-correct evaluation.
- `test_submit_integer_answer`: Confirms integer value comparison.
- `test_submit_answer_for_draft_question_returns_404`: Confirms attempts on non-published questions return 404.
- `test_practice_session_progress_and_completion`: Confirms session completion status updates upon answering all questions.
- `test_report_question_errata`: Confirms errata reports are saved with issue codes and descriptions.
- `test_practice_session_idor_protection`: Confirms IDOR guard returns 403 when another student accesses a session.

### 7.2 Frontend Test Suite (Vitest)
Command: `npm test -- --run`  
Result: **7 test files, 24 passed, 0 failed, 100% pass rate** (in 8.99s)

Coverage includes:
- `src/test/Practice.test.tsx` (5 tests):
  - Renders question prompt, difficulty badges, and option cards.
  - Option selection, submission, feedback banner, and step-by-step derivation reveal.
  - Numerical question decimal input and evaluation.
  - Errata reporting modal submission.
  - PracticeModal session stepper navigation and completion summary screen.
- All prior frontend tests (`App`, `Auth`, `Onboarding`, `CurriculumBrowser`, `LessonViewer`, `LessonContentRenderer`) pass cleanly.

### 7.3 Frontend Production Build
Command: `npm run build` (`tsc && vite build`)  
Result: **Exit code 0 — Clean build**
- `dist/index.html`: 0.78 kB
- `dist/assets/index-Dn1Xst4-.css`: 36.49 kB (gzip: 6.48 kB)
- `dist/assets/index-C5s2-Kyz.js`: 519.98 kB (gzip: 150.78 kB)

---

## 8. Security & Architectural Invariants Verified

1. **Answer Key Protection:** Question serialization schemas (`QuestionStudentResponse`) never include `QuestionAnswerKey` fields. Answer keys and educator derivations are only returned upon POST submission of an attempt.
2. **Editorial Guardrails:** DRAFT and IN_REVIEW questions are excluded from public/student endpoints using SQL filter `Question.status == ContentStatus.PUBLISHED.value`.
3. **IDOR Prevention:** Session retrieval (`GET /practice/sessions/{id}`) verifies that `session.user_id == current_user.id`, returning 403 Forbidden for unauthorized access.
4. **No External AI / API Key Dependencies:** Zero third-party LLM APIs, cloud services, or paid infrastructure introduced. All evaluation and derivations rely on deterministic, verified academic answer keys.

---

## 9. Conclusion

Milestone 4 is fully implemented, verified, and ready for deployment. The platform now provides high-quality topic-based practice with atomic scoring, step-by-step educator derivations, KaTeX formulas, and student errata workflows.
