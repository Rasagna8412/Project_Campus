"""Tests for Question Bank, Topic-Based Practice Engine, Answer Evaluation, and Errata."""

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
async def authenticated_student_token(client: AsyncClient) -> str:
    """Helper fixture to register, login, and obtain a valid student bearer token."""
    unique_email = f"practice_student_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "SecurePassword123!",
            "full_name": "Practice Student",
        },
    )
    assert reg_res.status_code == 201
    return reg_res.json()["access_token"]


@pytest.mark.asyncio
async def test_get_topic_questions_published_only(client: AsyncClient, db_session):
    """Verify that student question queries return published questions without leaking answers."""
    stmt = select(Topic).where(Topic.slug == "coulombs-law-and-superposition")
    res = await db_session.execute(stmt)
    topic = res.scalar_one_or_none()
    assert topic is not None

    response = await client.get(f"/api/v1/practice/topics/{topic.id}/questions")
    assert response.status_code == 200
    questions = response.json()
    assert len(questions) >= 1

    for q in questions:
        assert q["topic_id"] == str(topic.id)
        assert "content_latex" in q
        assert "options" in q

        # CRITICAL SECURITY INVARIANT: Answers and derivations must NOT be exposed
        assert "answer_key" not in q
        assert "correct_options" not in q
        assert "numerical_value" not in q
        assert "integer_value" not in q
        assert "explanation_latex" not in q


@pytest.mark.asyncio
async def test_topic_questions_draft_and_in_review_excluded(client: AsyncClient, db_session):
    """Verify that DRAFT and IN_REVIEW questions are excluded from student-facing question lists."""
    stmt = select(Topic).where(Topic.slug == "coulombs-law-and-superposition")
    res = await db_session.execute(stmt)
    topic = res.scalar_one_or_none()
    assert topic is not None

    # Check directly in DB that both PUBLISHED and DRAFT questions exist
    q_all = (
        await db_session.execute(
            select(Question).where(Question.topic_id == topic.id)
        )
    ).scalars().all()
    statuses = {q.status for q in q_all}
    assert ContentStatus.PUBLISHED.value in statuses
    assert ContentStatus.DRAFT.value in statuses

    # Verify through API endpoint: only PUBLISHED questions appear
    response = await client.get(f"/api/v1/practice/topics/{topic.id}/questions")
    assert response.status_code == 200
    public_questions = response.json()

    for q in public_questions:
        assert "Draft Question" not in q["content_latex"]


@pytest.mark.asyncio
async def test_get_topic_questions_nonexistent_topic_404(client: AsyncClient):
    """Verify 404 response when querying questions for a non-existent topic."""
    random_id = uuid.uuid4()
    response = await client.get(f"/api/v1/practice/topics/{random_id}/questions")
    assert response.status_code == 404
    assert response.json()["detail"] == "Topic not found"


@pytest.mark.asyncio
async def test_create_practice_session_authenticated(
    client: AsyncClient, authenticated_student_token: str, db_session
):
    """Verify that an authenticated student can start an interactive practice session."""
    stmt = select(Topic).where(Topic.slug == "coulombs-law-and-superposition")
    res = await db_session.execute(stmt)
    topic = res.scalar_one_or_none()
    assert topic is not None

    headers = {"Authorization": f"Bearer {authenticated_student_token}"}
    response = await client.post(
        "/api/v1/practice/sessions",
        json={"topic_id": str(topic.id), "limit": 3},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["topic_id"] == str(topic.id)
    assert data["session_type"] == "TOPIC_PRACTICE"
    assert data["is_completed"] is False
    assert len(data["questions"]) >= 1

    # Security check on questions in session
    for q in data["questions"]:
        assert "explanation_latex" not in q
        assert "correct_options" not in q


@pytest.mark.asyncio
async def test_create_practice_session_unauthenticated_401(client: AsyncClient):
    """Verify that unauthenticated requests to start practice sessions are rejected with 401."""
    response = await client.post(
        "/api/v1/practice/sessions",
        json={"limit": 5},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_submit_single_choice_answer_correct(
    client: AsyncClient, authenticated_student_token: str, db_session
):
    """Verify atomic evaluation and explanation reveal for correct single-choice answer."""
    # Find Coulomb force MCQ question
    stmt = (
        select(Question)
        .where(
            Question.question_type == QuestionType.SINGLE_CHOICE.value,
            Question.status == ContentStatus.PUBLISHED.value,
            Question.content_latex.contains("experiencing an electrostatic repulsive force"),
        )
        .options(selectinload(Question.answer_key))
    )
    res = await db_session.execute(stmt)
    question = res.scalar_one_or_none()
    assert question is not None
    assert question.answer_key is not None
    correct_opt = question.answer_key.correct_options[0]  # "B"

    headers = {"Authorization": f"Bearer {authenticated_student_token}"}
    response = await client.post(
        "/api/v1/practice/submit",
        json={
            "question_id": str(question.id),
            "selected_options": [correct_opt],
            "time_spent_seconds": 25,
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["question_id"] == str(question.id)
    assert data["is_correct"] is True
    assert data["score"] == 1.0
    assert data["correct_options"] == [correct_opt]
    assert "explanation_latex" in data
    assert r"\frac{F}{16}" in data["explanation_latex"]


@pytest.mark.asyncio
async def test_submit_single_choice_answer_incorrect(
    client: AsyncClient, authenticated_student_token: str, db_session
):
    """Verify evaluation for incorrect single-choice answer."""
    stmt = (
        select(Question)
        .where(
            Question.question_type == QuestionType.SINGLE_CHOICE.value,
            Question.status == ContentStatus.PUBLISHED.value,
            Question.content_latex.contains("experiencing an electrostatic repulsive force"),
        )
        .options(selectinload(Question.answer_key))
    )
    res = await db_session.execute(stmt)
    question = res.scalar_one_or_none()
    assert question is not None

    headers = {"Authorization": f"Bearer {authenticated_student_token}"}
    response = await client.post(
        "/api/v1/practice/submit",
        json={
            "question_id": str(question.id),
            "selected_options": ["A"],  # Wrong option (F/4)
            "time_spent_seconds": 15,
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["is_correct"] is False
    assert data["score"] == 0.0
    assert data["correct_options"] == ["B"]
    assert "explanation_latex" in data


@pytest.mark.asyncio
async def test_submit_numerical_answer_within_and_outside_tolerance(
    client: AsyncClient, authenticated_student_token: str, db_session
):
    """Verify numerical answer evaluation with decimal tolerance."""
    stmt = (
        select(Question)
        .where(
            Question.question_type == QuestionType.NUMERICAL.value,
            Question.status == ContentStatus.PUBLISHED.value,
        )
        .options(selectinload(Question.answer_key))
    )
    res = await db_session.execute(stmt)
    question = res.scalar_one_or_none()
    assert question is not None
    # Correct value is 0.90, tolerance 0.02

    headers = {"Authorization": f"Bearer {authenticated_student_token}"}

    # 1. Submit within tolerance: 0.91 -> Correct
    res_correct = await client.post(
        "/api/v1/practice/submit",
        json={
            "question_id": str(question.id),
            "submitted_numerical": 0.91,
            "time_spent_seconds": 45,
        },
        headers=headers,
    )
    assert res_correct.status_code == 200
    assert res_correct.json()["is_correct"] is True

    # 2. Submit outside tolerance: 0.95 -> Incorrect
    res_incorrect = await client.post(
        "/api/v1/practice/submit",
        json={
            "question_id": str(question.id),
            "submitted_numerical": 0.95,
            "time_spent_seconds": 30,
        },
        headers=headers,
    )
    assert res_incorrect.status_code == 200
    assert res_incorrect.json()["is_correct"] is False


@pytest.mark.asyncio
async def test_submit_multiple_choice_answer(
    client: AsyncClient, authenticated_student_token: str, db_session
):
    """Verify multiple-choice evaluation requiring all correct options."""
    stmt = (
        select(Question)
        .where(
            Question.question_type == QuestionType.MULTIPLE_CHOICE.value,
            Question.status == ContentStatus.PUBLISHED.value,
        )
        .options(selectinload(Question.answer_key))
    )
    res = await db_session.execute(stmt)
    question = res.scalar_one_or_none()
    assert question is not None
    # Correct options: ["A", "C", "D"]

    headers = {"Authorization": f"Bearer {authenticated_student_token}"}

    # Partial answers: ["A", "C"] -> Incorrect (full credit requires exact set)
    res_partial = await client.post(
        "/api/v1/practice/submit",
        json={
            "question_id": str(question.id),
            "selected_options": ["A", "C"],
        },
        headers=headers,
    )
    assert res_partial.json()["is_correct"] is False

    # Exact set in different order: ["D", "A", "C"] -> Correct
    res_full = await client.post(
        "/api/v1/practice/submit",
        json={
            "question_id": str(question.id),
            "selected_options": ["D", "A", "C"],
        },
        headers=headers,
    )
    assert res_full.json()["is_correct"] is True


@pytest.mark.asyncio
async def test_submit_integer_answer(
    client: AsyncClient, authenticated_student_token: str, db_session
):
    """Verify integer answer evaluation."""
    stmt = (
        select(Question)
        .where(
            Question.question_type == QuestionType.INTEGER.value,
            Question.status == ContentStatus.PUBLISHED.value,
        )
        .options(selectinload(Question.answer_key))
    )
    res = await db_session.execute(stmt)
    question = res.scalar_one_or_none()
    assert question is not None
    # Correct value is 1

    headers = {"Authorization": f"Bearer {authenticated_student_token}"}

    res_correct = await client.post(
        "/api/v1/practice/submit",
        json={"question_id": str(question.id), "submitted_integer": 1},
        headers=headers,
    )
    assert res_correct.json()["is_correct"] is True

    res_wrong = await client.post(
        "/api/v1/practice/submit",
        json={"question_id": str(question.id), "submitted_integer": 2},
        headers=headers,
    )
    assert res_wrong.json()["is_correct"] is False


@pytest.mark.asyncio
async def test_submit_answer_for_draft_question_returns_404(
    client: AsyncClient, authenticated_student_token: str, db_session
):
    """Verify that attempting to submit answers to DRAFT questions returns 404."""
    stmt = select(Question).where(Question.status == ContentStatus.DRAFT.value)
    res = await db_session.execute(stmt)
    draft_q = res.scalar_one_or_none()
    assert draft_q is not None

    headers = {"Authorization": f"Bearer {authenticated_student_token}"}
    response = await client.post(
        "/api/v1/practice/submit",
        json={"question_id": str(draft_q.id), "selected_options": ["B"]},
        headers=headers,
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_practice_session_progress_and_completion(
    client: AsyncClient, authenticated_student_token: str, db_session
):
    """Verify that practice session tracks correct count and completes when all questions are answered."""
    stmt = select(Topic).where(Topic.slug == "coulombs-law-and-superposition")
    res = await db_session.execute(stmt)
    topic = res.scalar_one_or_none()
    assert topic is not None

    headers = {"Authorization": f"Bearer {authenticated_student_token}"}

    # Start 2-question session
    sess_res = await client.post(
        "/api/v1/practice/sessions",
        json={"topic_id": str(topic.id), "limit": 2},
        headers=headers,
    )
    assert sess_res.status_code == 201
    session_data = sess_res.json()
    sess_id = session_data["id"]
    questions = session_data["questions"]
    assert len(questions) == 2

    # Submit Q1
    q1 = questions[0]
    await client.post(
        "/api/v1/practice/submit",
        json={
            "session_id": sess_id,
            "question_id": q1["id"],
            "selected_options": ["B"],
        },
        headers=headers,
    )

    # Check session still in progress
    s_check = await client.get(f"/api/v1/practice/sessions/{sess_id}", headers=headers)
    assert s_check.json()["is_completed"] is False

    # Submit Q2
    q2 = questions[1]
    await client.post(
        "/api/v1/practice/submit",
        json={
            "session_id": sess_id,
            "question_id": q2["id"],
            "submitted_numerical": 0.90,
            "selected_options": ["A"],
        },
        headers=headers,
    )

    # Check session is now completed
    s_done = await client.get(f"/api/v1/practice/sessions/{sess_id}", headers=headers)
    assert s_done.json()["is_completed"] is True
    assert s_done.json()["completed_at"] is not None


@pytest.mark.asyncio
async def test_report_question_errata(
    client: AsyncClient, authenticated_student_token: str, db_session
):
    """Verify that student can report an errata ticket on a question."""
    stmt = select(Question).where(Question.status == ContentStatus.PUBLISHED.value).limit(1)
    res = await db_session.execute(stmt)
    question = res.scalar_one_or_none()
    assert question is not None

    headers = {"Authorization": f"Bearer {authenticated_student_token}"}
    response = await client.post(
        f"/api/v1/practice/questions/{question.id}/report-errata",
        json={
            "question_id": str(question.id),
            "issue_type": "TYPO",
            "description": "Typo in the unit of permittivity in the third line of the problem statement.",
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["question_id"] == str(question.id)
    assert data["issue_type"] == "TYPO"
    assert data["status"] == "OPEN"


@pytest.mark.asyncio
async def test_practice_session_idor_protection(
    client: AsyncClient, authenticated_student_token: str, db_session
):
    """Verify that student A cannot access student B's practice session."""
    # Register student B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"student_b_{uuid.uuid4().hex[:8]}@example.com",
            "password": "Password123!",
            "full_name": "Student B",
        },
    )
    token_b = res_b.json()["access_token"]

    stmt = select(Topic).limit(1)
    topic = (await db_session.execute(stmt)).scalar_one_or_none()
    assert topic is not None

    # Student A creates session
    sess_res = await client.post(
        "/api/v1/practice/sessions",
        json={"topic_id": str(topic.id), "limit": 2},
        headers={"Authorization": f"Bearer {authenticated_student_token}"},
    )
    session_a_id = sess_res.json()["id"]

    # Student B attempts to access Student A's session
    attack_res = await client.get(
        f"/api/v1/practice/sessions/{session_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert attack_res.status_code == 404
    assert attack_res.json()["detail"] == "Practice session not found"
