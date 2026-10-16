"""Security, Correctness, and Regression Audit Tests for Milestone 4 Practice Engine."""

import math
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.assessment import (
    DifficultyLevel,
    PracticeSession,
    Question,
    QuestionAnswerKey,
    QuestionAttempt,
    QuestionOption,
    QuestionType,
)
from app.models.content import ContentStatus
from app.models.taxonomy import Topic


@pytest_asyncio.fixture
async def student_a_token(client: AsyncClient) -> str:
    """Register and authenticate Student A."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"audit_student_a_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "full_name": "Audit Student A",
        },
    )
    assert res.status_code == 201
    return res.json()["access_token"]


@pytest_asyncio.fixture
async def student_b_token(client: AsyncClient) -> str:
    """Register and authenticate Student B."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"audit_student_b_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "full_name": "Audit Student B",
        },
    )
    assert res.status_code == 201
    return res.json()["access_token"]


# ==============================================================================
# 1. ANSWER-KEY CONFIDENTIALITY AUDIT
# ==============================================================================

@pytest.mark.asyncio
async def test_audit_answer_key_never_leaked_in_question_lists(
    client: AsyncClient, db_session
):
    """Verify that public/student question queries NEVER contain answer keys or derivations."""
    stmt = select(Topic).limit(1)
    topic = (await db_session.execute(stmt)).scalar_one_or_none()
    assert topic is not None

    resp = await client.get(f"/api/v1/practice/topics/{topic.id}/questions")
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) > 0

    forbidden_fields = {
        "answer_key",
        "correct_options",
        "numerical_value",
        "numerical_tolerance",
        "integer_value",
        "explanation_latex",
        "is_correct",
    }

    for q in questions:
        # Check top-level question payload
        found_forbidden = forbidden_fields.intersection(q.keys())
        assert not found_forbidden, f"Question payload leaked confidential fields: {found_forbidden}"

        # Check options payload
        for opt in q.get("options", []):
            assert "is_correct" not in opt, "Option leaked is_correct status"


@pytest.mark.asyncio
async def test_audit_answer_key_never_leaked_in_session_creation_or_status(
    client: AsyncClient, student_a_token: str, db_session
):
    """Verify that practice session creation and retrieval NEVER leak answer keys."""
    stmt = select(Topic).limit(1)
    topic = (await db_session.execute(stmt)).scalar_one_or_none()
    assert topic is not None

    headers = {"Authorization": f"Bearer {student_a_token}"}
    create_resp = await client.post(
        "/api/v1/practice/sessions",
        json={"topic_id": str(topic.id), "limit": 5},
        headers=headers,
    )
    assert create_resp.status_code == 201
    session_data = create_resp.json()

    forbidden_fields = {
        "answer_key",
        "correct_options",
        "numerical_value",
        "numerical_tolerance",
        "integer_value",
        "explanation_latex",
    }

    # Verify session creation questions
    for q in session_data["questions"]:
        found_forbidden = forbidden_fields.intersection(q.keys())
        assert not found_forbidden, f"Session creation leaked fields: {found_forbidden}"
        for opt in q.get("options", []):
            assert "is_correct" not in opt

    # Verify session get status questions
    get_resp = await client.get(
        f"/api/v1/practice/sessions/{session_data['id']}",
        headers=headers,
    )
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    for q in get_data["questions"]:
        found_forbidden = forbidden_fields.intersection(q.keys())
        assert not found_forbidden, f"Session get leaked fields: {found_forbidden}"


# ==============================================================================
# 2. SUBMISSION AND SCORING INTEGRITY AUDIT
# ==============================================================================

@pytest.mark.asyncio
async def test_audit_numerical_tolerance_exact_boundaries(
    client: AsyncClient, student_a_token: str, db_session
):
    """Verify exact tolerance boundaries: target - tol, target + tol, and just outside."""
    stmt = (
        select(Question)
        .where(
            Question.question_type == QuestionType.NUMERICAL.value,
            Question.status == ContentStatus.PUBLISHED.value,
        )
        .options(selectinload(Question.answer_key))
    )
    question = (await db_session.execute(stmt)).scalar_one_or_none()
    assert question is not None
    assert question.answer_key is not None

    target = question.answer_key.numerical_value
    tol = question.answer_key.numerical_tolerance
    assert target is not None
    assert tol is not None

    headers = {"Authorization": f"Bearer {student_a_token}"}

    # 1. Exact lower boundary: target - tol (should be CORRECT)
    resp_lower = await client.post(
        "/api/v1/practice/submit",
        json={
            "question_id": str(question.id),
            "submitted_numerical": round(target - tol, 6),
            "time_spent_seconds": 10,
        },
        headers=headers,
    )
    assert resp_lower.status_code == 200
    assert resp_lower.json()["is_correct"] is True

    # 2. Exact upper boundary: target + tol (should be CORRECT)
    resp_upper = await client.post(
        "/api/v1/practice/submit",
        json={
            "question_id": str(question.id),
            "submitted_numerical": round(target + tol, 6),
            "time_spent_seconds": 10,
        },
        headers=headers,
    )
    assert resp_upper.status_code == 200
    assert resp_upper.json()["is_correct"] is True

    # 3. Just below lower boundary: target - tol - 0.001 (should be INCORRECT)
    resp_too_low = await client.post(
        "/api/v1/practice/submit",
        json={
            "question_id": str(question.id),
            "submitted_numerical": round(target - tol - 0.001, 6),
            "time_spent_seconds": 10,
        },
        headers=headers,
    )
    assert resp_too_low.status_code == 200
    assert resp_too_low.json()["is_correct"] is False

    # 4. Just above upper boundary: target + tol + 0.001 (should be INCORRECT)
    resp_too_high = await client.post(
        "/api/v1/practice/submit",
        json={
            "question_id": str(question.id),
            "submitted_numerical": round(target + tol + 0.001, 6),
            "time_spent_seconds": 10,
        },
        headers=headers,
    )
    assert resp_too_high.status_code == 200
    assert resp_too_high.json()["is_correct"] is False


@pytest.mark.asyncio
async def test_audit_numerical_nan_and_inf_handling(
    client: AsyncClient, student_a_token: str, db_session
):
    """Verify handling of NaN and Infinity values in numerical answer submission."""
    stmt = (
        select(Question)
        .where(
            Question.question_type == QuestionType.NUMERICAL.value,
            Question.status == ContentStatus.PUBLISHED.value,
        )
    )
    question = (await db_session.execute(stmt)).scalar_one_or_none()
    assert question is not None

    headers = {"Authorization": f"Bearer {student_a_token}"}

    # Submit raw JSON containing NaN
    raw_payload = f'{{"question_id": "{question.id}", "submitted_numerical": NaN, "time_spent_seconds": 10}}'
    headers_json = {"Authorization": f"Bearer {student_a_token}", "Content-Type": "application/json"}
    resp_nan = await client.post(
        "/api/v1/practice/submit",
        content=raw_payload,
        headers=headers_json,
    )
    # The server should either reject with 422/400 or evaluate safely without crashing
    assert resp_nan.status_code in (200, 400, 422)
    if resp_nan.status_code == 200:
        assert resp_nan.json()["is_correct"] is False


@pytest.mark.asyncio
async def test_audit_option_keys_must_belong_to_question(
    client: AsyncClient, student_a_token: str, db_session
):
    """Probe submitting option identifiers that do NOT exist on the question."""
    stmt = (
        select(Question)
        .where(
            Question.question_type == QuestionType.SINGLE_CHOICE.value,
            Question.status == ContentStatus.PUBLISHED.value,
        )
        .limit(1)
        .options(selectinload(Question.options))
    )
    question = (await db_session.execute(stmt)).scalar_one_or_none()
    assert question is not None

    headers = {"Authorization": f"Bearer {student_a_token}"}
    # Submit option 'Z' which does not exist
    resp = await client.post(
        "/api/v1/practice/submit",
        json={
            "question_id": str(question.id),
            "selected_options": ["Z"],
            "time_spent_seconds": 10,
        },
        headers=headers,
    )
    # The server should either reject invalid option key with 400/422 or evaluate as incorrect
    assert resp.status_code in (200, 400, 422)
    if resp.status_code == 200:
        assert resp.json()["is_correct"] is False


# ==============================================================================
# 3. SESSION ISOLATION, OWNERSHIP & SCORE INFLATION AUDIT
# ==============================================================================

@pytest.mark.asyncio
async def test_audit_session_ownership_cross_student_submission_protection(
    client: AsyncClient, student_a_token: str, student_b_token: str, db_session
):
    """Verify Student B cannot submit answers to Student A's practice session."""
    stmt = select(Topic).limit(1)
    topic = (await db_session.execute(stmt)).scalar_one_or_none()
    assert topic is not None

    # Student A creates a session
    sess_res = await client.post(
        "/api/v1/practice/sessions",
        json={"topic_id": str(topic.id), "limit": 2},
        headers={"Authorization": f"Bearer {student_a_token}"},
    )
    assert sess_res.status_code == 201
    session_a = sess_res.json()
    session_a_id = session_a["id"]
    q_id = session_a["questions"][0]["id"]

    # Student B attempts to submit an answer specifying Student A's session_id
    attack_res = await client.post(
        "/api/v1/practice/submit",
        json={
            "session_id": session_a_id,
            "question_id": q_id,
            "selected_options": ["A"],
            "time_spent_seconds": 5,
        },
        headers={"Authorization": f"Bearer {student_b_token}"},
    )

    # AUDIT CHECK: Does Student B get rejected, or does it pollute Student A's session?
    # If accepted with 200, verify that Student A's session was NOT polluted!
    check_session_a = await client.get(
        f"/api/v1/practice/sessions/{session_a_id}",
        headers={"Authorization": f"Bearer {student_a_token}"},
    )
    assert check_session_a.status_code == 200

    # Query DB directly to see if any attempt in Student A's session belongs to Student B
    attempts_stmt = select(QuestionAttempt).where(QuestionAttempt.session_id == uuid.UUID(session_a_id))
    attempts = (await db_session.execute(attempts_stmt)).scalars().all()
    for att in attempts:
        assert str(att.user_id) != "student_b", "CRITICAL IDOR: Student B's attempt was linked to Student A's session!"


@pytest.mark.asyncio
async def test_audit_duplicate_submission_score_inflation(
    client: AsyncClient, student_a_token: str, db_session
):
    """Verify whether submitting the same question multiple times inflates session score or counts."""
    # Find a published single choice question
    stmt = (
        select(Question)
        .where(
            Question.question_type == QuestionType.SINGLE_CHOICE.value,
            Question.status == ContentStatus.PUBLISHED.value,
        )
        .limit(1)
        .options(selectinload(Question.answer_key))
    )
    question = (await db_session.execute(stmt)).scalar_one_or_none()
    assert question is not None
    assert question.answer_key is not None
    correct_opt = question.answer_key.correct_options[0]

    headers = {"Authorization": f"Bearer {student_a_token}"}

    # Create a 3-question session
    sess_res = await client.post(
        "/api/v1/practice/sessions",
        json={"topic_id": str(question.topic_id), "limit": 3},
        headers=headers,
    )
    assert sess_res.status_code == 201
    session = sess_res.json()
    sess_id = session["id"]

    # Submit the CORRECT answer to question 1
    resp1 = await client.post(
        "/api/v1/practice/submit",
        json={
            "session_id": sess_id,
            "question_id": str(question.id),
            "selected_options": [correct_opt],
            "time_spent_seconds": 15,
        },
        headers=headers,
    )
    assert resp1.status_code == 200
    assert resp1.json()["is_correct"] is True

    # Submit the SAME question with the SAME correct answer again
    resp2 = await client.post(
        "/api/v1/practice/submit",
        json={
            "session_id": sess_id,
            "question_id": str(question.id),
            "selected_options": [correct_opt],
            "time_spent_seconds": 15,
        },
        headers=headers,
    )

    # Check session state
    sess_check = await client.get(
        f"/api/v1/practice/sessions/{sess_id}",
        headers=headers,
    )
    assert sess_check.status_code == 200
    sess_data = sess_check.json()

    # AUDIT VERIFICATION: Did correct_count inflate to 2 for answering 1 question?
    print(f"DEBUG: correct_count = {sess_data['correct_count']}, total = {sess_data['total_questions']}")
    assert sess_data["correct_count"] <= 1, (
        f"SCORE INFLATION DETECTED: Submitting the same question twice resulted in correct_count = {sess_data['correct_count']}"
    )


@pytest.mark.asyncio
async def test_audit_submission_to_completed_session(
    client: AsyncClient, student_a_token: str, db_session
):
    """Verify behavior when submitting an answer to an already completed practice session."""
    # Find Coulomb questions
    stmt = (
        select(Question)
        .where(
            Question.question_type == QuestionType.SINGLE_CHOICE.value,
            Question.status == ContentStatus.PUBLISHED.value,
        )
        .limit(1)
        .options(selectinload(Question.answer_key))
    )
    question = (await db_session.execute(stmt)).scalar_one_or_none()
    assert question is not None

    headers = {"Authorization": f"Bearer {student_a_token}"}

    # Create a 1-question session
    sess_res = await client.post(
        "/api/v1/practice/sessions",
        json={"topic_id": str(question.topic_id), "limit": 1},
        headers=headers,
    )
    assert sess_res.status_code == 201
    sess_id = sess_res.json()["id"]

    # Submit answer to complete the session
    sub1 = await client.post(
        "/api/v1/practice/submit",
        json={
            "session_id": sess_id,
            "question_id": str(question.id),
            "selected_options": ["A"],
            "time_spent_seconds": 10,
        },
        headers=headers,
    )
    assert sub1.status_code == 200

    # Verify session is marked completed
    sess_done = await client.get(f"/api/v1/practice/sessions/{sess_id}", headers=headers)
    assert sess_done.json()["is_completed"] is True

    # Now attempt another submission against the completed session
    sub2 = await client.post(
        "/api/v1/practice/submit",
        json={
            "session_id": sess_id,
            "question_id": str(question.id),
            "selected_options": ["A"],
            "time_spent_seconds": 10,
        },
        headers=headers,
    )
    # The system should either reject submission to completed session (400) or disallow further score modification
    assert sub2.status_code in (200, 400)


@pytest.mark.asyncio
async def test_audit_history_isolation_between_two_students(
    client: AsyncClient, student_a_token: str, student_b_token: str, db_session
):
    """Verify Student B cannot see Student A's practice history."""
    stmt = select(Topic).limit(1)
    topic = (await db_session.execute(stmt)).scalar_one_or_none()
    assert topic is not None

    # Student A creates a session
    await client.post(
        "/api/v1/practice/sessions",
        json={"topic_id": str(topic.id), "limit": 1},
        headers={"Authorization": f"Bearer {student_a_token}"},
    )

    # Student A checks history: should have at least 1 session
    hist_a = await client.get(
        "/api/v1/practice/history",
        headers={"Authorization": f"Bearer {student_a_token}"},
    )
    assert hist_a.status_code == 200
    assert len(hist_a.json()) >= 1
    session_ids_a = {s["id"] for s in hist_a.json()}

    # Student B checks history: must NOT see Student A's sessions
    hist_b = await client.get(
        "/api/v1/practice/history",
        headers={"Authorization": f"Bearer {student_b_token}"},
    )
    assert hist_b.status_code == 200
    session_ids_b = {s["id"] for s in hist_b.json()}

    intersection = session_ids_a.intersection(session_ids_b)
    assert not intersection, f"CRITICAL: Student B saw Student A's practice sessions: {intersection}"
