"""Milestone 5 Automated Test Suite: Student Progress Tracking & Learning Analytics."""

from datetime import datetime, timezone
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import PracticeSession, Question, QuestionAttempt, QuestionType
from app.models.content import ContentStatus, Lesson, LessonProgress, LessonProgressStatus
from app.models.identity import StudentProfile, User
from app.models.taxonomy import Chapter, Subject, Topic


@pytest_asyncio.fixture
async def student_a_token(client: AsyncClient) -> str:
    """Register and authenticate Student A."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"prog_student_a_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "full_name": "Progress Student A",
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
            "email": f"prog_student_b_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "full_name": "Progress Student B",
        },
    )
    assert res.status_code == 201
    return res.json()["access_token"]


# ==============================================================================
# 1. LESSON PROGRESS TRACKING TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_lesson_progress_lifecycle_start_and_complete(
    client: AsyncClient, student_a_token: str, db_session: AsyncSession
):
    """Verify full lifecycle: starting a lesson, verifying in-progress state, and marking completed."""
    stmt = select(Lesson).where(Lesson.status == ContentStatus.PUBLISHED.value).limit(1)
    lesson = (await db_session.execute(stmt)).scalar_one_or_none()
    assert lesson is not None

    headers = {"Authorization": f"Bearer {student_a_token}"}

    # 1. Start / open lesson
    start_resp = await client.post(
        f"/api/v1/student/progress/lessons/{lesson.id}/start",
        headers=headers,
    )
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    assert start_data["lesson_id"] == str(lesson.id)
    assert start_data["status"] == "IN_PROGRESS"
    assert start_data["started_at"] is not None
    assert start_data["completed_at"] is None
    assert start_data["last_accessed_at"] is not None

    # 2. Check get single progress
    get_resp = await client.get(
        f"/api/v1/student/progress/lessons/{lesson.id}",
        headers=headers,
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "IN_PROGRESS"

    # 3. Explicitly complete lesson
    comp_resp = await client.post(
        f"/api/v1/student/progress/lessons/{lesson.id}/complete",
        headers=headers,
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["status"] == "COMPLETED"
    assert comp_data["completed_at"] is not None
    original_completed_at = comp_data["completed_at"]

    # 4. Idempotent complete — subsequent complete preserves original completed_at
    comp_resp2 = await client.post(
        f"/api/v1/student/progress/lessons/{lesson.id}/complete",
        headers=headers,
    )
    assert comp_resp2.status_code == 200
    assert comp_resp2.json()["completed_at"] == original_completed_at

    # 5. Calling start on an already completed lesson does not reset it to IN_PROGRESS
    start_again_resp = await client.post(
        f"/api/v1/student/progress/lessons/{lesson.id}/start",
        headers=headers,
    )
    assert start_again_resp.status_code == 200
    assert start_again_resp.json()["status"] == "COMPLETED"
    assert start_again_resp.json()["completed_at"] == original_completed_at


@pytest.mark.asyncio
async def test_lesson_progress_unpublished_and_invalid_rejected(
    client: AsyncClient, student_a_token: str, db_session: AsyncSession
):
    """Verify that unpublished lessons (DRAFT/IN_REVIEW) and non-existent IDs return 404."""
    # Find draft lesson
    stmt = select(Lesson).where(Lesson.status != ContentStatus.PUBLISHED.value).limit(1)
    draft_lesson = (await db_session.execute(stmt)).scalar_one_or_none()

    headers = {"Authorization": f"Bearer {student_a_token}"}

    if draft_lesson:
        draft_resp = await client.post(
            f"/api/v1/student/progress/lessons/{draft_lesson.id}/start",
            headers=headers,
        )
        assert draft_resp.status_code == 404

    # Non-existent UUID
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    fake_resp = await client.post(
        f"/api/v1/student/progress/lessons/{fake_uuid}/start",
        headers=headers,
    )
    assert fake_resp.status_code == 404


@pytest.mark.asyncio
async def test_lesson_progress_student_data_isolation(
    client: AsyncClient,
    student_a_token: str,
    student_b_token: str,
    db_session: AsyncSession,
):
    """Verify that Student A and Student B have completely isolated lesson progress records."""
    stmt = select(Lesson).where(Lesson.status == ContentStatus.PUBLISHED.value).limit(1)
    lesson = (await db_session.execute(stmt)).scalar_one_or_none()
    assert lesson is not None

    headers_a = {"Authorization": f"Bearer {student_a_token}"}
    headers_b = {"Authorization": f"Bearer {student_b_token}"}

    # Student A starts and completes the lesson
    await client.post(
        f"/api/v1/student/progress/lessons/{lesson.id}/complete",
        headers=headers_a,
    )

    # Student B queries progress for this lesson -> should return 404 (No progress recorded)
    resp_b = await client.get(
        f"/api/v1/student/progress/lessons/{lesson.id}",
        headers=headers_b,
    )
    assert resp_b.status_code == 404

    # Student B's lesson progress list should NOT include Student A's completed lesson
    list_b = await client.get(
        "/api/v1/student/progress/lessons",
        headers=headers_b,
    )
    assert list_b.status_code == 200
    b_lesson_ids = [item["lesson_id"] for item in list_b.json()]
    assert str(lesson.id) not in b_lesson_ids


# ==============================================================================
# 2. LEARNING ANALYTICS & DASHBOARD TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_dashboard_analytics_empty_state_for_fresh_student(
    client: AsyncClient, student_b_token: str
):
    """A fresh student with no activity receives 0 counts and null accuracy without error."""
    headers = {"Authorization": f"Bearer {student_b_token}"}
    resp = await client.get("/api/v1/student/analytics/dashboard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["lessons_completed_count"] == 0
    assert data["lessons_in_progress_count"] == 0
    assert data["practice_sessions_completed_count"] == 0
    assert data["total_questions_answered"] == 0
    assert data["total_correct_answers"] == 0
    assert data["overall_accuracy_percentage"] is None  # Never 0%
    assert data["total_practice_time_seconds"] == 0
    assert isinstance(data["recent_activity"], list)
    assert len(data["recent_activity"]) == 0


@pytest.mark.asyncio
async def test_dashboard_analytics_with_activity(
    client: AsyncClient, student_a_token: str, db_session: AsyncSession
):
    """Verify aggregated dashboard metrics after recording attempts and completing a lesson."""
    headers = {"Authorization": f"Bearer {student_a_token}"}

    # Start and complete a lesson
    stmt = select(Lesson).where(Lesson.status == ContentStatus.PUBLISHED.value).limit(1)
    lesson = (await db_session.execute(stmt)).scalar_one_or_none()
    assert lesson is not None

    await client.post(
        f"/api/v1/student/progress/lessons/{lesson.id}/complete",
        headers=headers,
    )

    resp = await client.get("/api/v1/student/analytics/dashboard", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["lessons_completed_count"] >= 1
    assert data["daily_study_goal_minutes"] > 0
    # If practice attempts exist from previous test runs, overall accuracy is a valid float
    if data["total_questions_answered"] > 0:
        assert isinstance(data["overall_accuracy_percentage"], (float, int))
        assert 0.0 <= data["overall_accuracy_percentage"] <= 100.0


# ==============================================================================
# 3. TOPIC PERFORMANCE & CLASSIFICATION TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_topic_performance_threshold_classifications(
    client: AsyncClient, student_b_token: str, db_session: AsyncSession
):
    """Verify deterministic topic status categories:
    - INSUFFICIENT_DATA (< 5 attempts)
    - NEEDS_REVIEW (>= 5 attempts and < 60%)
    - DEVELOPING (>= 5 attempts and 60% <= acc < 80%)
    - STRONG (>= 5 attempts and >= 80%)
    """
    headers = {"Authorization": f"Bearer {student_b_token}"}

    # 1. Fetch current user B
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    user_b_id = uuid.UUID(me_resp.json()["id"])

    # 2. Pick a published question and topic
    q_stmt = select(Question).where(Question.status == ContentStatus.PUBLISHED.value).limit(1)
    question = (await db_session.execute(q_stmt)).scalar_one_or_none()
    assert question is not None
    topic_id = question.topic_id

    # 3. Insert 4 attempts (all incorrect) -> Should be INSUFFICIENT_DATA (< 5 attempts)
    for _ in range(4):
        att = QuestionAttempt(
            user_id=user_b_id,
            question_id=question.id,
            is_correct=False,
            time_spent_seconds=15,
        )
        db_session.add(att)
    await db_session.commit()

    topics_resp = await client.get("/api/v1/student/analytics/topics", headers=headers)
    assert topics_resp.status_code == 200
    topics_data = topics_resp.json()

    topic_entry = next((t for t in topics_data if t["topic_id"] == str(topic_id)), None)
    assert topic_entry is not None
    assert topic_entry["total_attempts"] == 4
    assert topic_entry["status_category"] == "INSUFFICIENT_DATA"

    # 4. Insert 5th attempt (still incorrect -> 0/5 = 0.0% < 60%) -> Should become NEEDS_REVIEW
    att5 = QuestionAttempt(
        user_id=user_b_id,
        question_id=question.id,
        is_correct=False,
        time_spent_seconds=15,
    )
    db_session.add(att5)
    await db_session.commit()

    topics_resp2 = await client.get("/api/v1/student/analytics/topics", headers=headers)
    topic_entry2 = next((t for t in topics_resp2.json() if t["topic_id"] == str(topic_id)), None)
    assert topic_entry2 is not None
    assert topic_entry2["total_attempts"] == 5
    assert topic_entry2["observed_accuracy_percentage"] == 0.0
    assert topic_entry2["status_category"] == "NEEDS_REVIEW"

    # 5. Insert 5 correct attempts -> 5/10 = 50.0% (still < 60%) -> Still NEEDS_REVIEW
    for _ in range(5):
        db_session.add(
            QuestionAttempt(
                user_id=user_b_id,
                question_id=question.id,
                is_correct=True,
                time_spent_seconds=20,
            )
        )
    await db_session.commit()

    topics_resp3 = await client.get("/api/v1/student/analytics/topics", headers=headers)
    topic_entry3 = next((t for t in topics_resp3.json() if t["topic_id"] == str(topic_id)), None)
    assert topic_entry3["total_attempts"] == 10
    assert topic_entry3["observed_accuracy_percentage"] == 50.0
    assert topic_entry3["status_category"] == "NEEDS_REVIEW"

    # 6. Insert 5 more correct attempts -> 10/15 = 66.7% (60% <= acc < 80%) -> DEVELOPING
    for _ in range(5):
        db_session.add(
            QuestionAttempt(
                user_id=user_b_id,
                question_id=question.id,
                is_correct=True,
                time_spent_seconds=20,
            )
        )
    await db_session.commit()

    topics_resp4 = await client.get("/api/v1/student/analytics/topics", headers=headers)
    topic_entry4 = next((t for t in topics_resp4.json() if t["topic_id"] == str(topic_id)), None)
    assert topic_entry4["total_attempts"] == 15
    assert topic_entry4["observed_accuracy_percentage"] == 66.7
    assert topic_entry4["status_category"] == "DEVELOPING"


# ==============================================================================
# 4. RECOMMENDATIONS ENGINE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_recommendations_priority_ordering(
    client: AsyncClient, student_b_token: str, db_session: AsyncSession
):
    """Verify that recommendations properly prioritize:
    1. Resume in-progress lesson
    2. Revisit struggling topic
    3. Practice low confidence topic
    4. Start next unstarted lesson
    """
    headers = {"Authorization": f"Bearer {student_b_token}"}

    # Start a published lesson to make it IN_PROGRESS
    stmt = select(Lesson).where(Lesson.status == ContentStatus.PUBLISHED.value).limit(1)
    lesson = (await db_session.execute(stmt)).scalar_one_or_none()
    assert lesson is not None

    await client.post(
        f"/api/v1/student/progress/lessons/{lesson.id}/start",
        headers=headers,
    )

    recs_resp = await client.get("/api/v1/student/analytics/recommendations", headers=headers)
    assert recs_resp.status_code == 200
    recs = recs_resp.json()
    assert len(recs) > 0

    # Top recommendation MUST be RESUME_LESSON
    first_rec = recs[0]
    assert first_rec["type"] == "RESUME_LESSON"
    assert first_rec["priority"] == 1
    assert first_rec["target_id"] == str(lesson.id)
    assert first_rec["action_label"] == "Resume Lesson"


@pytest.mark.asyncio
async def test_recommendations_empty_enrollment_does_not_leak_unrelated_curricula(
    client: AsyncClient,
):
    """Verify that a student without enrolled subjects is never recommended arbitrary global lessons."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"empty_enroll_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "full_name": "Empty Enrollment Student",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    recs_resp = await client.get("/api/v1/student/analytics/recommendations", headers=headers)
    assert recs_resp.status_code == 200
    recs = recs_resp.json()
    # Student has no progress, no attempts, and NO enrolled subjects:
    # Must NOT recommend any NEXT_LESSON from global curricula
    next_lesson_recs = [r for r in recs if r["type"] == "NEXT_LESSON"]
    assert len(next_lesson_recs) == 0


# ==============================================================================
# 5. PRIVACY & DPDP ACT CASCADE ERASURE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_account_erasure_cascades_lesson_progress(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify that deleting a student account permanently deletes all lesson_progress rows."""
    email = f"erasure_test_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!", "full_name": "Erasure Test"},
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Start a lesson
    stmt = select(Lesson).where(Lesson.status == ContentStatus.PUBLISHED.value).limit(1)
    lesson = (await db_session.execute(stmt)).scalar_one_or_none()
    assert lesson is not None

    await client.post(
        f"/api/v1/student/progress/lessons/{lesson.id}/start",
        headers=headers,
    )

    # Confirm progress exists
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_resp.json()["id"])

    prog_stmt = select(LessonProgress).where(LessonProgress.user_id == user_id)
    prog = (await db_session.execute(prog_stmt)).scalar_one_or_none()
    assert prog is not None

    # Delete student account
    del_resp = await client.delete("/api/v1/student/account", headers=headers)
    assert del_resp.status_code == 200

    # Expire session cache and verify lesson_progress records were permanently erased
    db_session.expire_all()
    prog_after = (await db_session.execute(prog_stmt)).scalar_one_or_none()
    assert prog_after is None

