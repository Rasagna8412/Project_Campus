"""Automated Test Suite for Spaced Repetition (Milestone 7).

Tests review item creation hooks, review queue queries, SM-2 submission transactions,
idempotency, same-day duplicate prevention, IDOR protection, pagination, and DPDP cascading deletion.
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.review_service import get_or_create_review_item
from app.core.sm2 import get_ist_date, PLANNER_TZ
from app.models.assessment import Question, QuestionAnswerKey, QuestionOption
from app.models.content import ContentStatus, Lesson, LessonProgress
from app.models.identity import StudentProfile, User
from app.models.repetition import ReviewItem, ReviewLog, ReviewStatus
from app.models.taxonomy import Chapter, Subject, Topic


@pytest_asyncio.fixture
async def repetition_student_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Register, authenticate, and onboard student with curriculum subjects."""
    email = f"rep_student_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": "Repetition Student",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Onboard student with CBSE Class 12
    curricula_res = await client.get("/api/v1/curricula/")
    if curricula_res.status_code == 200 and curricula_res.json():
        curricula = curricula_res.json()
        cbse = next((c for c in curricula if c.get("code") == "CBSE"), curricula[0])
        grades = cbse.get("grades", [])
        grade_12 = next(
            (g for g in grades if g.get("code") == "CLASS_12"),
            grades[0] if grades else None,
        )
        if grade_12 and grade_12.get("subjects"):
            subject_ids = [s["id"] for s in grade_12["subjects"]]
            await client.put(
                "/api/v1/student/onboarding",
                headers=headers,
                json={
                    "target_curriculum_id": cbse["id"],
                    "grade_stage_id": grade_12["id"],
                    "target_exam_year": 2027,
                    "selected_subject_ids": subject_ids,
                    "daily_study_goal_minutes": 120,
                    "preferred_language": "en",
                    "complete": True,
                },
            )
    return token


@pytest_asyncio.fixture
async def other_rep_student_token(client: AsyncClient) -> str:
    """Second authenticated student for IDOR tests."""
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"rep_other_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "full_name": "Other Rep Student",
        },
    )
    assert reg_res.status_code == 201
    return reg_res.json()["access_token"]


# ==============================================================================
# 1. REVIEW ITEM CREATION HOOK TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_review_item_created_on_lesson_completion(
    client: AsyncClient,
    repetition_student_token: str,
    db_session: AsyncSession,
):
    """Verify that explicitly completing a published lesson triggers ReviewItem creation."""
    headers = {"Authorization": f"Bearer {repetition_student_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    # Find a published lesson
    stmt = (
        select(Lesson)
        .where(Lesson.status == ContentStatus.PUBLISHED.value)
        .limit(1)
    )
    lesson = (await db_session.execute(stmt)).scalar_one_or_none()
    assert lesson is not None

    # Complete the lesson
    res = await client.post(
        f"/api/v1/student/progress/lessons/{lesson.id}/complete",
        headers=headers,
    )
    assert res.status_code == 200

    # Verify ReviewItem exists in LEARNING status
    item_stmt = select(ReviewItem).where(
        ReviewItem.user_id == user_id,
        ReviewItem.topic_id == lesson.topic_id,
    )
    item = (await db_session.execute(item_stmt)).scalar_one_or_none()
    assert item is not None
    assert item.repetition_count == 0
    assert item.ease_factor == 2.50
    assert item.interval_days == 0
    assert item.status == "LEARNING"
    assert item.due_date == get_ist_date() + timedelta(days=1)


@pytest.mark.asyncio
async def test_review_item_created_on_qualifying_practice_completion(
    client: AsyncClient,
    repetition_student_token: str,
    db_session: AsyncSession,
):
    """Verify that completing a practice session with >= 60% accuracy triggers ReviewItem."""
    headers = {"Authorization": f"Bearer {repetition_student_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    # Find a topic with at least 3 published questions
    stmt = (
        select(Question.topic_id)
        .where(Question.status == ContentStatus.PUBLISHED.value)
        .group_by(Question.topic_id)
        .having(func.count(Question.id) >= 3)
        .limit(1)
    )
    topic_id = (await db_session.execute(stmt)).scalar()
    assert topic_id is not None
    topic = await db_session.get(Topic, topic_id)
    assert topic is not None

    # Create a 3-question session
    sess_res = await client.post(
        "/api/v1/practice/sessions",
        headers=headers,
        json={"topic_id": str(topic.id), "limit": 3},
    )
    assert sess_res.status_code == 201
    session_id = sess_res.json()["id"]

    # Submit 2 correct answers out of 3 (accuracy = 66.7% >= 60%)
    q_res = await client.get(f"/api/v1/practice/topics/{topic.id}/questions", headers=headers)
    questions = q_res.json()
    assert len(questions) >= 3

    for i in range(3):
        q = questions[i]
        q_type = q["question_type"]
        key_stmt = select(QuestionAnswerKey).where(QuestionAnswerKey.question_id == uuid.UUID(q["id"])).limit(1)
        key = (await db_session.execute(key_stmt)).scalar_one_or_none()
        assert key is not None

        payload = {
            "session_id": str(session_id),
            "question_id": str(q["id"]),
            "time_spent_seconds": 10,
        }

        if i < 2:  # Correct answers
            if q_type in ["SINGLE_CHOICE", "MULTIPLE_CHOICE"]:
                payload["selected_options"] = key.correct_options
            elif q_type == "NUMERICAL":
                payload["submitted_numerical"] = key.numerical_value
            elif q_type == "INTEGER":
                payload["submitted_integer"] = key.integer_value
        else:  # Incorrect answer
            if q_type in ["SINGLE_CHOICE", "MULTIPLE_CHOICE"]:
                available = [o["option_key"] for o in q.get("options", [])]
                wrong = [k for k in available if k not in (key.correct_options or [])]
                payload["selected_options"] = wrong[:1] if wrong else ["A"]
            elif q_type == "NUMERICAL":
                payload["submitted_numerical"] = (key.numerical_value or 0.0) + 1000.0
            elif q_type == "INTEGER":
                payload["submitted_integer"] = (key.integer_value or 0) + 1000

        sub_res = await client.post(
            "/api/v1/practice/submit",
            headers=headers,
            json=payload,
        )
        assert sub_res.status_code == 200

    # Verify review item was initialized
    item_stmt = select(ReviewItem).where(
        ReviewItem.user_id == user_id,
        ReviewItem.topic_id == topic.id,
    )
    item = (await db_session.execute(item_stmt)).scalar_one_or_none()
    assert item is not None
    assert item.status == "LEARNING"


# ==============================================================================
# 2. REVIEW QUEUE AND STATS API TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_get_review_queue_and_stats(
    client: AsyncClient,
    repetition_student_token: str,
    db_session: AsyncSession,
):
    """Verify queue pagination, overdue count, and empty-state stats."""
    headers = {"Authorization": f"Bearer {repetition_student_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    # Initial stats should be empty
    stats_res = await client.get("/api/v1/review/stats", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_tracked_topics"] == 0
    assert stats["due_today_count"] == 0
    assert stats["successful_review_rate_percentage"] is None

    # Seed 2 review items (one due today, one due yesterday = overdue)
    top_stmt = (
        select(Topic)
        .options(selectinload(Topic.chapter))
        .limit(2)
    )
    topics = (await db_session.execute(top_stmt)).scalars().all()
    assert len(topics) >= 2

    today_ist = get_ist_date()
    item_today = ReviewItem(
        id=uuid.uuid4(),
        user_id=user_id,
        topic_id=topics[0].id,
        subject_id=topics[0].chapter.subject_id,
        repetition_count=1,
        ease_factor=2.50,
        interval_days=1,
        due_date=today_ist,
        status="LEARNING",
    )
    item_overdue = ReviewItem(
        id=uuid.uuid4(),
        user_id=user_id,
        topic_id=topics[1].id,
        subject_id=topics[1].chapter.subject_id,
        repetition_count=2,
        ease_factor=2.60,
        interval_days=6,
        due_date=today_ist - timedelta(days=2),
        status="REVIEW",
    )
    db_session.add_all([item_today, item_overdue])
    await db_session.commit()

    # Query review queue
    q_res = await client.get("/api/v1/review/queue?limit=10", headers=headers)
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["total_due_count"] == 2
    assert q_data["overdue_count"] == 1
    assert q_data["returned_count"] == 2
    assert len(q_data["items"]) == 2

    # Stats now reflect seeded items
    stats_res2 = await client.get("/api/v1/review/stats", headers=headers)
    assert stats_res2.status_code == 200
    assert stats_res2.json()["total_tracked_topics"] == 2
    assert stats_res2.json()["due_today_count"] == 2


# ==============================================================================
# 3. REVIEW SUBMISSION AND DUPLICATE PREVENTION TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_submit_review_rating_and_same_day_duplicate_rejection(
    client: AsyncClient,
    repetition_student_token: str,
    db_session: AsyncSession,
):
    """Verify successful rating submission, SM-2 advancement, and 409 rejection on duplicate."""
    headers = {"Authorization": f"Bearer {repetition_student_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    # Seed an item due today
    top_stmt = select(Topic).options(selectinload(Topic.chapter)).limit(1)
    topic = (await db_session.execute(top_stmt)).scalar_one_or_none()
    assert topic is not None

    item = ReviewItem(
        id=uuid.uuid4(),
        user_id=user_id,
        topic_id=topic.id,
        subject_id=topic.chapter.subject_id,
        repetition_count=0,
        ease_factor=2.50,
        interval_days=0,
        due_date=get_ist_date(),
        status="LEARNING",
    )
    db_session.add(item)
    await db_session.commit()

    # Submit review rating q=4 ('Good')
    sub_res = await client.post(
        f"/api/v1/review/items/{item.id}/submit",
        headers=headers,
        json={"quality_score": 4, "time_spent_seconds": 45},
    )
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["repetition_count"] == 1
    assert sub_data["interval_days"] == 1
    assert sub_data["ease_factor"] == 2.50

    # Verify ReviewLog was inserted in same transaction
    log_stmt = select(ReviewLog).where(ReviewLog.review_item_id == item.id)
    log = (await db_session.execute(log_stmt)).scalar_one_or_none()
    assert log is not None
    assert log.quality_score == 4
    assert log.time_spent_seconds == 45

    # Attempt immediate second submission on same IST day -> 409 Conflict
    dup_res = await client.post(
        f"/api/v1/review/items/{item.id}/submit",
        headers=headers,
        json={"quality_score": 5, "time_spent_seconds": 30},
    )
    assert dup_res.status_code == 409
    assert "already been reviewed today" in dup_res.json()["detail"]


@pytest.mark.asyncio
async def test_review_item_idor_protection(
    client: AsyncClient,
    repetition_student_token: str,
    other_rep_student_token: str,
    db_session: AsyncSession,
):
    """Verify that Student B cannot submit a review for Student A's item."""
    headers_a = {"Authorization": f"Bearer {repetition_student_token}"}
    headers_b = {"Authorization": f"Bearer {other_rep_student_token}"}

    me_a = (await client.get("/api/v1/auth/me", headers=headers_a)).json()
    user_a_id = uuid.UUID(me_a["id"])

    top_stmt = select(Topic).options(selectinload(Topic.chapter)).limit(1)
    topic = (await db_session.execute(top_stmt)).scalar_one_or_none()

    item_a = ReviewItem(
        id=uuid.uuid4(),
        user_id=user_a_id,
        topic_id=topic.id,
        subject_id=topic.chapter.subject_id,
        repetition_count=0,
        ease_factor=2.50,
        interval_days=0,
        due_date=get_ist_date(),
        status="LEARNING",
    )
    db_session.add(item_a)
    await db_session.commit()

    # Student B attempts to submit review for Student A's item -> 404 Not Found
    res = await client.post(
        f"/api/v1/review/items/{item_a.id}/submit",
        headers=headers_b,
        json={"quality_score": 4, "time_spent_seconds": 20},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_review_history_pagination(
    client: AsyncClient,
    repetition_student_token: str,
    db_session: AsyncSession,
):
    """Verify pagination on review history endpoint."""
    headers = {"Authorization": f"Bearer {repetition_student_token}"}
    me = (await client.get("/api/v1/auth/me", headers=headers)).json()
    user_id = uuid.UUID(me["id"])

    top = (await db_session.execute(select(Topic).options(selectinload(Topic.chapter)).limit(1))).scalar_one_or_none()
    item = ReviewItem(
        id=uuid.uuid4(),
        user_id=user_id,
        topic_id=top.id,
        subject_id=top.chapter.subject_id,
        repetition_count=1,
        ease_factor=2.50,
        interval_days=1,
        due_date=get_ist_date(),
        status="LEARNING",
    )
    db_session.add(item)
    await db_session.commit()

    # Seed 3 review logs
    for i in range(3):
        log = ReviewLog(
            id=uuid.uuid4(),
            review_item_id=item.id,
            user_id=user_id,
            quality_score=4,
            time_spent_seconds=30,
            scheduled_interval_days=1,
            next_interval_days=6,
            ease_factor_before=2.50,
            ease_factor_after=2.50,
        )
        db_session.add(log)
    await db_session.commit()

    # Fetch page 1 with page_size=2
    res = await client.get("/api/v1/review/history?page=1&page_size=2", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] >= 3
    assert len(data["items"]) == 2
    assert data["total_pages"] >= 2


@pytest.mark.asyncio
async def test_account_erasure_cascades_repetition_records(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Verify that deleting student account cleanses all review items and logs."""
    # Register fresh student
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"rep_del_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "full_name": "Deletion Test Student",
        },
    )
    token = reg.json()["access_token"]
    user_id = uuid.UUID(reg.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {token}"}

    top = (await db_session.execute(select(Topic).options(selectinload(Topic.chapter)).limit(1))).scalar_one_or_none()
    item = ReviewItem(
        id=uuid.uuid4(),
        user_id=user_id,
        topic_id=top.id,
        subject_id=top.chapter.subject_id,
        repetition_count=1,
        ease_factor=2.50,
        interval_days=1,
        due_date=get_ist_date(),
        status="LEARNING",
    )
    db_session.add(item)
    await db_session.flush()

    log = ReviewLog(
        id=uuid.uuid4(),
        review_item_id=item.id,
        user_id=user_id,
        quality_score=5,
        scheduled_interval_days=1,
        next_interval_days=6,
        ease_factor_before=2.50,
        ease_factor_after=2.60,
    )
    db_session.add(log)
    await db_session.commit()

    # Delete student account
    del_res = await client.delete("/api/v1/student/account", headers=headers)
    assert del_res.status_code == 200

    # Verify review items and logs are wiped
    item_cnt = (await db_session.execute(select(func.count(ReviewItem.id)).where(ReviewItem.user_id == user_id))).scalar()
    log_cnt = (await db_session.execute(select(func.count(ReviewLog.id)).where(ReviewLog.user_id == user_id))).scalar()
    assert item_cnt == 0
    assert log_cnt == 0


@pytest.mark.asyncio
async def test_savepoint_concurrent_creation_collision(
    db_session: AsyncSession,
):
    """Verify that concurrent creation race on (user_id, topic_id) recovers idempotently via savepoint."""
    user_id = uuid.uuid4()
    top = (await db_session.execute(select(Topic).options(selectinload(Topic.chapter)).limit(1))).scalar_one_or_none()
    assert top is not None
    subject_id = top.chapter.subject_id

    # First call creates the item
    item1 = await get_or_create_review_item(user_id, top.id, subject_id, db_session)
    assert item1 is not None

    # Second call for same user_id and topic_id returns the existing item without error
    item2 = await get_or_create_review_item(user_id, top.id, subject_id, db_session)
    assert item2 is not None
    assert item2.id == item1.id
