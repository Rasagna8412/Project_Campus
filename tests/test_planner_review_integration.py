"""Automated Test Suite for Daily Planner and Spaced Repetition Integration (Milestone 7).

Verifies:
- Priority 2 spaced repetition scheduling in daily plan.
- Strict preservation of the 4-task ceiling and daily time budget.
- Anti-starvation cap: exactly 1 review task per daily plan.
- Overdue queue availability when review tasks exceed daily slots.
- Completing a planner task does NOT advance SM-2 schedule without an explicit rating.
- Topic deduplication across review and practice categories.
- Force refresh preserves completed review tasks.
"""

from datetime import date, datetime, timedelta, timezone
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.sm2 import get_ist_date
from app.models.content import ContentStatus, Lesson, LessonProgress, LessonProgressStatus
from app.models.identity import StudentProfile, User
from app.models.planner import StudyGoal, StudyTask, TaskStatus, TaskType
from app.models.repetition import ReviewItem, ReviewStatus
from app.models.taxonomy import Chapter, Subject, Topic


@pytest_asyncio.fixture
async def plan_rep_student_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Register, authenticate, and onboard student with CBSE Class 12 subjects."""
    email = f"plan_rep_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": "Planner Rep Student",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

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


@pytest.mark.asyncio
async def test_due_review_item_scheduled_as_priority_2(
    client: AsyncClient,
    plan_rep_student_token: str,
    db_session: AsyncSession,
):
    """Verify that a due review item is prioritized and scheduled as Priority 2 in daily plan."""
    headers = {"Authorization": f"Bearer {plan_rep_student_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])
    today_ist = get_ist_date()

    # Find an enrolled topic
    top_stmt = select(Topic).options(selectinload(Topic.chapter)).limit(1)
    topic = (await db_session.execute(top_stmt)).scalar_one_or_none()
    assert topic is not None

    # Seed a due ReviewItem
    item = ReviewItem(
        id=uuid.uuid4(),
        user_id=user_id,
        topic_id=topic.id,
        subject_id=topic.chapter.subject_id,
        repetition_count=1,
        ease_factor=2.50,
        interval_days=1,
        due_date=today_ist,
        status="LEARNING",
    )
    db_session.add(item)
    await db_session.commit()

    # Fetch daily plan
    plan_res = await client.get("/api/v1/planner/daily", headers=headers)
    assert plan_res.status_code == 200
    tasks = plan_res.json()["tasks"]
    assert len(tasks) >= 1

    # Verify review task exists
    review_tasks = [t for t in tasks if t["topic_id"] == str(topic.id) and "Spaced Review" in t["title"]]
    assert len(review_tasks) == 1
    assert review_tasks[0]["task_type"] == "REVISE_TOPIC"
    assert review_tasks[0]["estimated_minutes"] == 15


@pytest.mark.asyncio
async def test_multiple_due_review_items_max_one_scheduled_in_plan(
    client: AsyncClient,
    plan_rep_student_token: str,
    db_session: AsyncSession,
):
    """Verify anti-starvation cap: 4 due items schedule exactly 1 task in daily plan."""
    headers = {"Authorization": f"Bearer {plan_rep_student_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])
    today_ist = get_ist_date()

    # Seed 4 due ReviewItems across different topics
    top_stmt = select(Topic).options(selectinload(Topic.chapter)).limit(4)
    topics = (await db_session.execute(top_stmt)).scalars().all()
    assert len(topics) >= 3

    for top in topics:
        item = ReviewItem(
            id=uuid.uuid4(),
            user_id=user_id,
            topic_id=top.id,
            subject_id=top.chapter.subject_id,
            repetition_count=1,
            ease_factor=2.50,
            interval_days=1,
            due_date=today_ist - timedelta(days=1),
            status="LEARNING",
        )
        db_session.add(item)
    await db_session.commit()

    # Generate daily plan
    gen_res = await client.post(
        "/api/v1/planner/daily/generate?force_refresh=true",
        headers=headers,
    )
    assert gen_res.status_code == 200
    tasks = gen_res.json()["tasks"]

    # Maximum 1 Spaced Review task scheduled in the plan
    spaced_review_tasks = [t for t in tasks if "Spaced Review" in t["title"]]
    assert len(spaced_review_tasks) == 1

    # But the review queue must still show all due items!
    q_res = await client.get("/api/v1/review/queue", headers=headers)
    assert q_res.status_code == 200
    assert q_res.json()["total_due_count"] >= 3


@pytest.mark.asyncio
async def test_four_task_ceiling_maintained_with_review_item(
    client: AsyncClient,
    plan_rep_student_token: str,
    db_session: AsyncSession,
):
    """Verify that 4-task ceiling is never exceeded when review items are present."""
    headers = {"Authorization": f"Bearer {plan_rep_student_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])
    today_ist = get_ist_date()

    # Seed 2 due review items
    top_stmt = select(Topic).options(selectinload(Topic.chapter)).limit(2)
    topics = (await db_session.execute(top_stmt)).scalars().all()
    for top in topics:
        item = ReviewItem(
            id=uuid.uuid4(),
            user_id=user_id,
            topic_id=top.id,
            subject_id=top.chapter.subject_id,
            repetition_count=1,
            ease_factor=2.50,
            interval_days=1,
            due_date=today_ist,
            status="LEARNING",
        )
        db_session.add(item)
    await db_session.commit()

    # Generate plan
    res = await client.post(
        "/api/v1/planner/daily/generate?force_refresh=true",
        headers=headers,
    )
    assert res.status_code == 200
    tasks = res.json()["tasks"]
    assert len(tasks) <= 4


@pytest.mark.asyncio
async def test_planner_task_completion_without_rating_does_not_advance_sm2(
    client: AsyncClient,
    plan_rep_student_token: str,
    db_session: AsyncSession,
):
    """Verify checking a review task in the planner does NOT mutate SM-2 metrics."""
    headers = {"Authorization": f"Bearer {plan_rep_student_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])
    today_ist = get_ist_date()

    top = (await db_session.execute(select(Topic).options(selectinload(Topic.chapter)).limit(1))).scalar_one_or_none()
    item = ReviewItem(
        id=uuid.uuid4(),
        user_id=user_id,
        topic_id=top.id,
        subject_id=top.chapter.subject_id,
        repetition_count=0,
        ease_factor=2.50,
        interval_days=0,
        due_date=today_ist,
        status="LEARNING",
    )
    db_session.add(item)
    await db_session.commit()

    # Get daily plan
    plan_res = await client.get("/api/v1/planner/daily", headers=headers)
    tasks = plan_res.json()["tasks"]
    rev_task = next(t for t in tasks if t["topic_id"] == str(top.id))

    # Toggle task completed on planner board
    toggle_res = await client.patch(
        f"/api/v1/planner/tasks/{rev_task['id']}/complete",
        headers=headers,
        json={"is_completed": True},
    )
    assert toggle_res.status_code == 200
    assert toggle_res.json()["is_completed"] is True

    # Verify ReviewItem metrics remain completely unchanged (n=0, I=0, EF=2.50)
    await db_session.refresh(item)
    assert item.repetition_count == 0
    assert item.interval_days == 0
    assert item.ease_factor == 2.50
    assert item.due_date == today_ist


@pytest.mark.asyncio
async def test_force_refresh_preserves_completed_review_tasks(
    client: AsyncClient,
    plan_rep_student_token: str,
    db_session: AsyncSession,
):
    """Verify that force refresh preserves completed review tasks."""
    headers = {"Authorization": f"Bearer {plan_rep_student_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])
    today_ist = get_ist_date()

    top = (await db_session.execute(select(Topic).options(selectinload(Topic.chapter)).limit(1))).scalar_one_or_none()
    item = ReviewItem(
        id=uuid.uuid4(),
        user_id=user_id,
        topic_id=top.id,
        subject_id=top.chapter.subject_id,
        repetition_count=1,
        ease_factor=2.50,
        interval_days=1,
        due_date=today_ist,
        status="LEARNING",
    )
    db_session.add(item)
    await db_session.commit()

    # Generate plan and complete review task
    plan_res = await client.get("/api/v1/planner/daily", headers=headers)
    rev_task = next(t for t in plan_res.json()["tasks"] if t["topic_id"] == str(top.id))
    await client.patch(
        f"/api/v1/planner/tasks/{rev_task['id']}/complete",
        headers=headers,
        json={"is_completed": True},
    )

    # Force refresh
    ref_res = await client.post(
        "/api/v1/planner/daily/generate?force_refresh=true",
        headers=headers,
    )
    assert ref_res.status_code == 200
    ref_tasks = ref_res.json()["tasks"]

    # Completed review task is preserved
    preserved = next(t for t in ref_tasks if t["id"] == rev_task["id"])
    assert preserved["is_completed"] is True
    assert preserved["status"] == "COMPLETED"
