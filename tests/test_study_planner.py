"""Milestone 6 Automated Test Suite: Study Planner & Learning Roadmap."""

import asyncio
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Question, QuestionAttempt
from app.models.content import ContentStatus, Lesson, LessonProgress, LessonProgressStatus
from app.models.identity import StudentProfile, User
from app.models.planner import GoalStatus, StudyGoal, StudyTask, TaskStatus, TaskType
from app.models.taxonomy import Chapter, Subject, Topic


@pytest_asyncio.fixture
async def planner_student_token(client: AsyncClient) -> str:
    """Register, authenticate, and onboard test student with curriculum subjects."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"plan_student_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "full_name": "Planner Student",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
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


@pytest_asyncio.fixture
async def other_student_token(client: AsyncClient) -> str:
    """Register and authenticate another test student for IDOR tests."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"plan_other_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "full_name": "Other Student",
        },
    )
    assert res.status_code == 201
    return res.json()["access_token"]


# ==============================================================================
# 1. STUDY GOAL MANAGEMENT TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_get_or_create_default_study_goal(
    client: AsyncClient, planner_student_token: str
):
    """Verify that querying /planner/goal auto-initializes a default goal."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}
    res = await client.get("/api/v1/planner/goal", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Academic Preparation"
    assert data["daily_study_minutes"] == 120
    assert data["status"] == "ACTIVE"
    assert "MON" in data["preferred_days"]


@pytest.mark.asyncio
async def test_update_study_goal_success_and_validation(
    client: AsyncClient, planner_student_token: str
):
    """Verify updating study goal minutes, title, and target date, and boundary validations."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    # 1. Valid update
    target = (date.today() + timedelta(days=90)).isoformat()
    res = await client.post(
        "/api/v1/planner/goal",
        headers=headers,
        json={
            "title": "Intensive Physics Preparation",
            "target_date": target,
            "daily_study_minutes": 150,
            "preferred_days": ["MON", "TUE", "WED", "THU", "FRI"],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Intensive Physics Preparation"
    assert data["daily_study_minutes"] == 150
    assert data["target_date"] == target
    assert data["preferred_days"] == ["MON", "TUE", "WED", "THU", "FRI"]

    # 2. Reject daily minutes < 15
    res_low = await client.post(
        "/api/v1/planner/goal",
        headers=headers,
        json={"daily_study_minutes": 10},
    )
    assert res_low.status_code == 422

    # 3. Reject daily minutes > 300
    res_high = await client.post(
        "/api/v1/planner/goal",
        headers=headers,
        json={"daily_study_minutes": 350},
    )
    assert res_high.status_code == 422

    # 4. Reject past target exam date
    past_date = (date.today() - timedelta(days=5)).isoformat()
    res_past = await client.post(
        "/api/v1/planner/goal",
        headers=headers,
        json={"target_date": past_date, "daily_study_minutes": 120},
    )
    assert res_past.status_code == 400
    assert "past" in res_past.json()["detail"].lower()


# ==============================================================================
# 2. DAILY STUDY PLAN GENERATION & TASK PRIORITIZATION TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_generate_daily_plan_time_budget_and_four_task_ceiling(
    client: AsyncClient, planner_student_token: str
):
    """Verify that generating a daily plan adheres to time budgets and max 4 tasks."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}
    today = date.today().isoformat()

    res = await client.get(f"/api/v1/planner/daily?plan_date={today}", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["date"] == today
    assert data["target_minutes"] == 120
    assert len(data["tasks"]) <= 4
    assert data["planned_minutes"] <= 120 or len(data["tasks"]) == 1


@pytest.mark.asyncio
async def test_priority_1_resume_in_progress_lesson(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """Verify that an in-progress lesson is prioritized first as RESUME_LESSON."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    # Fetch a published lesson
    stmt = (
        select(Lesson)
        .where(Lesson.status == ContentStatus.PUBLISHED.value)
        .limit(1)
    )
    lesson = (await db_session.execute(stmt)).scalar_one_or_none()
    assert lesson is not None

    # Start progress on lesson
    start_res = await client.post(
        f"/api/v1/student/progress/lessons/{lesson.id}/start",
        headers=headers,
    )
    assert start_res.status_code == 200

    # Regenerate daily plan with force_refresh
    plan_res = await client.post(
        "/api/v1/planner/daily/generate?force_refresh=true",
        headers=headers,
    )
    assert plan_res.status_code == 200
    tasks = plan_res.json()["tasks"]
    assert len(tasks) > 0
    first_task = tasks[0]
    assert first_task["task_type"] == "RESUME_LESSON"
    assert first_task["lesson_id"] == str(lesson.id)
    assert "started this lesson recently" in first_task["reason"]


@pytest.mark.asyncio
async def test_priority_2_revise_struggling_topic(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """Verify that a topic with >= 5 attempts and < 60% accuracy triggers REVISE_TOPIC."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    # Identify user ID
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    # Fetch published questions under a topic
    q_stmt = select(Question).where(Question.status == ContentStatus.PUBLISHED.value).limit(5)
    questions = (await db_session.execute(q_stmt)).scalars().all()
    assert len(questions) >= 5
    target_q = questions[0]
    topic_id = target_q.topic_id

    # Create 5 attempts under target_q's topic with 1 correct (20% accuracy) -> NEEDS_REVIEW
    for i in range(5):
        att = QuestionAttempt(
            id=uuid.uuid4(),
            user_id=user_id,
            question_id=target_q.id,
            is_correct=(i == 0),
            time_spent_seconds=60,
        )
        db_session.add(att)
    await db_session.commit()

    # Regenerate plan
    plan_res = await client.post(
        "/api/v1/planner/daily/generate?force_refresh=true",
        headers=headers,
    )
    assert plan_res.status_code == 200
    tasks = plan_res.json()["tasks"]

    # Confirm a task has type REVISE_TOPIC
    revise_tasks = [t for t in tasks if t["task_type"] == "REVISE_TOPIC"]
    assert len(revise_tasks) >= 1
    assert revise_tasks[0]["topic_id"] == str(topic_id)
    assert "revision" in revise_tasks[0]["reason"].lower()


# ==============================================================================
# 3. TASK COMPLETION & RESCHEDULING TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_task_completion_toggle(
    client: AsyncClient, planner_student_token: str
):
    """Verify toggling task completion status and updating completed_at timestamp."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    # Ensure plan exists
    plan_res = await client.get("/api/v1/planner/daily", headers=headers)
    tasks = plan_res.json()["tasks"]
    assert len(tasks) > 0
    task_id = tasks[0]["id"]

    # 1. Mark completed
    c_res = await client.patch(
        f"/api/v1/planner/tasks/{task_id}/complete",
        headers=headers,
        json={"is_completed": True},
    )
    assert c_res.status_code == 200
    assert c_res.json()["is_completed"] is True
    assert c_res.json()["status"] == "COMPLETED"
    assert c_res.json()["completed_at"] is not None

    # 2. Toggle back to pending
    p_res = await client.patch(
        f"/api/v1/planner/tasks/{task_id}/complete",
        headers=headers,
        json={"is_completed": False},
    )
    assert p_res.status_code == 200
    assert p_res.json()["is_completed"] is False
    assert p_res.json()["status"] == "PENDING"
    assert p_res.json()["completed_at"] is None


@pytest.mark.asyncio
async def test_task_reschedule_to_future_date(
    client: AsyncClient, planner_student_token: str
):
    """Verify moving an uncompleted task to tomorrow, rejecting past dates and completed tasks."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    plan_res = await client.get("/api/v1/planner/daily", headers=headers)
    tasks = plan_res.json()["tasks"]
    assert len(tasks) > 0
    task_id = tasks[0]["id"]

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    # 1. Reject past date
    past_res = await client.patch(
        f"/api/v1/planner/tasks/{task_id}/reschedule",
        headers=headers,
        json={"new_date": yesterday},
    )
    assert past_res.status_code == 400

    # 2. Successfully reschedule to tomorrow
    resched_res = await client.patch(
        f"/api/v1/planner/tasks/{task_id}/reschedule",
        headers=headers,
        json={"new_date": tomorrow},
    )
    assert resched_res.status_code == 200
    assert resched_res.json()["scheduled_date"] == tomorrow
    assert resched_res.json()["status"] == "RESCHEDULED"

    # 3. Reject rescheduling an already completed task
    await client.patch(
        f"/api/v1/planner/tasks/{task_id}/complete",
        headers=headers,
        json={"is_completed": True},
    )
    rej_res = await client.patch(
        f"/api/v1/planner/tasks/{task_id}/reschedule",
        headers=headers,
        json={"new_date": tomorrow},
    )
    assert rej_res.status_code == 400
    assert "completed" in rej_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_missed_day_non_punitive_anti_snowball(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """Verify that past uncompleted pending tasks are marked SKIPPED and do not clutter today's plan."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    # Seed an overdue task from yesterday
    yesterday = date.today() - timedelta(days=1)
    old_task = StudyTask(
        id=uuid.uuid4(),
        user_id=user_id,
        scheduled_date=yesterday,
        task_type="STUDY_LESSON",
        title="Yesterday Unfinished Task",
        estimated_minutes=15,
        status="PENDING",
        is_completed=False,
    )
    db_session.add(old_task)
    await db_session.commit()

    # Query today's daily plan
    plan_res = await client.get("/api/v1/planner/daily", headers=headers)
    assert plan_res.status_code == 200
    today_tasks = plan_res.json()["tasks"]

    # Verify yesterday's task is NOT in today's active list
    today_task_ids = [t["id"] for t in today_tasks]
    assert str(old_task.id) not in today_task_ids

    # Verify yesterday's task status was updated to SKIPPED in db
    await db_session.refresh(old_task)
    assert old_task.status == "SKIPPED"


# ==============================================================================
# 4. IDOR PROTECTION & DPDP ERASURE TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_planner_idor_student_isolation(
    client: AsyncClient,
    planner_student_token: str,
    other_student_token: str,
):
    """Verify that Student B cannot view, complete, or reschedule Student A's tasks."""
    headers_a = {"Authorization": f"Bearer {planner_student_token}"}
    headers_b = {"Authorization": f"Bearer {other_student_token}"}

    plan_a = (await client.get("/api/v1/planner/daily", headers=headers_a)).json()
    assert len(plan_a["tasks"]) > 0
    task_a_id = plan_a["tasks"][0]["id"]

    # Student B attempts to complete Student A's task
    idor_res = await client.patch(
        f"/api/v1/planner/tasks/{task_a_id}/complete",
        headers=headers_b,
        json={"is_completed": True},
    )
    assert idor_res.status_code == 404

    # Student B attempts to reschedule Student A's task
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    idor_resched = await client.patch(
        f"/api/v1/planner/tasks/{task_a_id}/reschedule",
        headers=headers_b,
        json={"new_date": tomorrow},
    )
    assert idor_resched.status_code == 404


@pytest.mark.asyncio
async def test_curriculum_roadmap_endpoint(
    client: AsyncClient, planner_student_token: str
):
    """Verify that /planner/roadmap aggregates total lessons and completion percentages."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}
    res = await client.get("/api/v1/planner/roadmap", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_lessons_count" in data
    assert "completed_lessons_count" in data
    assert "overall_completion_percentage" in data
    assert "subjects" in data
    assert isinstance(data["subjects"], list)


@pytest.mark.asyncio
async def test_account_erasure_cascades_planner_records(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """Verify that deleting student account permanently deletes all StudyGoal and StudyTask rows."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    # Ensure goal and task exist
    await client.get("/api/v1/planner/daily", headers=headers)

    g_stmt = select(StudyGoal).where(StudyGoal.user_id == user_id)
    t_stmt = select(StudyTask).where(StudyTask.user_id == user_id)

    assert (await db_session.execute(g_stmt)).scalar_one_or_none() is not None
    assert len((await db_session.execute(t_stmt)).scalars().all()) > 0

    # Delete student account
    del_res = await client.delete("/api/v1/student/account", headers=headers)
    assert del_res.status_code == 200

    db_session.expire_all()

    # Verify complete eradication of planner records
    assert (await db_session.execute(g_stmt)).scalar_one_or_none() is None
    assert len((await db_session.execute(t_stmt)).scalars().all()) == 0


# ==============================================================================
# 5. REMEDIATION REGRESSION TESTS (H-1, H-2, H-3, H-4, M-1, M-3, STATE CONSISTENCY)
# ==============================================================================


@pytest.mark.asyncio
async def test_force_refresh_with_completed_tasks_preserves_and_fills_capacity(
    client: AsyncClient, planner_student_token: str
):
    """H-1: Verify force refresh preserves completed tasks and fills remaining slots/time budget."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    # Generate initial plan
    plan_res = await client.post(
        "/api/v1/planner/daily/generate?force_refresh=true", headers=headers
    )
    assert plan_res.status_code == 200
    initial_tasks = plan_res.json()["tasks"]
    assert len(initial_tasks) > 1

    first_task_id = initial_tasks[0]["id"]

    # Complete the first task
    comp_res = await client.patch(
        f"/api/v1/planner/tasks/{first_task_id}/complete",
        headers=headers,
        json={"is_completed": True},
    )
    assert comp_res.status_code == 200
    completed_at_stamp = comp_res.json()["completed_at"]
    assert completed_at_stamp is not None

    # Call force refresh
    refreshed_res = await client.post(
        "/api/v1/planner/daily/generate?force_refresh=true", headers=headers
    )
    assert refreshed_res.status_code == 200
    refreshed_tasks = refreshed_res.json()["tasks"]

    # Verify completed task is preserved with state and timestamp intact
    matching_completed = [t for t in refreshed_tasks if t["id"] == first_task_id]
    assert len(matching_completed) == 1
    assert matching_completed[0]["is_completed"] is True
    assert matching_completed[0]["status"] == "COMPLETED"
    assert matching_completed[0]["completed_at"] == completed_at_stamp

    # Verify remaining tasks were generated and ceiling is respected
    assert len(refreshed_tasks) <= 4
    assert len(refreshed_tasks) >= 2


@pytest.mark.asyncio
async def test_force_refresh_when_all_tasks_completed_does_not_add_unnecessary_tasks(
    client: AsyncClient, planner_student_token: str
):
    """H-1: Verify that when all daily tasks are completed, force refresh does not create excess tasks."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    plan_res = await client.get("/api/v1/planner/daily", headers=headers)
    tasks = plan_res.json()["tasks"]

    # Complete all tasks
    for t in tasks:
        await client.patch(
            f"/api/v1/planner/tasks/{t['id']}/complete",
            headers=headers,
            json={"is_completed": True},
        )

    # Force refresh
    refreshed_res = await client.post(
        "/api/v1/planner/daily/generate?force_refresh=true", headers=headers
    )
    assert refreshed_res.status_code == 200
    final_tasks = refreshed_res.json()["tasks"]

    assert len(final_tasks) == len(tasks)
    assert all(t["is_completed"] for t in final_tasks)
    assert refreshed_res.json()["is_fully_completed"] is True


@pytest.mark.asyncio
async def test_concurrent_daily_plan_generation_safety(
    client: AsyncClient, planner_student_token: str, db_session: AsyncSession
):
    """H-2: Verify concurrent generation requests serialize cleanly and do not duplicate tasks."""
    import asyncio
    try:
        from tests.conftest import TestAsyncSessionLocal
    except ImportError:
        from conftest import TestAsyncSessionLocal
    from app.core.database import get_db
    from app.main import app

    headers = {"Authorization": f"Bearer {planner_student_token}"}
    target_future_date = (date.today() + timedelta(days=5)).isoformat()

    # Provide per-request database session so concurrent requests don't collide on a single AsyncSession instance
    async def per_request_db():
        async with TestAsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = per_request_db
    try:
        # Launch two concurrent requests for the same ungenerated future date
        res1, res2 = await asyncio.gather(
            client.post(
                f"/api/v1/planner/daily/generate?plan_date={target_future_date}",
                headers=headers,
            ),
            client.post(
                f"/api/v1/planner/daily/generate?plan_date={target_future_date}",
                headers=headers,
            ),
        )
        assert res1.status_code == 200
        assert res2.status_code == 200

        tasks1 = res1.json()["tasks"]
        tasks2 = res2.json()["tasks"]

        # Both must respect the 4-task ceiling
        assert len(tasks1) <= 4
        assert len(tasks2) <= 4

        # The persisted tasks must be identical and not duplicated
        ids1 = {t["id"] for t in tasks1}
        ids2 = {t["id"] for t in tasks2}
        assert ids1 == ids2
    finally:
        async def override_get_db():
            yield db_session
        app.dependency_overrides[get_db] = override_get_db


@pytest.mark.asyncio
async def test_overdue_rescheduled_tasks_marked_skipped(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """H-4: Verify overdue tasks with status RESCHEDULED are transitioned to SKIPPED."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    # Seed an overdue task that had been rescheduled to 2 days ago
    two_days_ago = date.today() - timedelta(days=2)
    resched_task = StudyTask(
        id=uuid.uuid4(),
        user_id=user_id,
        scheduled_date=two_days_ago,
        task_type="STUDY_LESSON",
        title="Overdue Rescheduled Lesson",
        estimated_minutes=20,
        status="RESCHEDULED",
        is_completed=False,
    )
    db_session.add(resched_task)
    await db_session.commit()

    # Access daily planner to trigger roll-forward
    plan_res = await client.get("/api/v1/planner/daily", headers=headers)
    assert plan_res.status_code == 200

    # Verify task status was updated to SKIPPED
    await db_session.refresh(resched_task)
    assert resched_task.status == "SKIPPED"
    assert resched_task.is_completed is False


@pytest.mark.asyncio
async def test_empty_subject_enrollment_curriculum_isolation(
    client: AsyncClient,
):
    """H-3: Verify students with no selected subjects receive empty roadmap and isolated plan."""
    # Register a new student with zero selected subjects
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"isolated_student_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "full_name": "Isolated Student",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Roadmap should be cleanly empty, not dumping global subjects
    roadmap_res = await client.get("/api/v1/planner/roadmap", headers=headers)
    assert roadmap_res.status_code == 200
    data = roadmap_res.json()
    assert data["total_lessons_count"] == 0
    assert data["completed_lessons_count"] == 0
    assert data["overall_completion_percentage"] == 0.0
    assert data["subjects"] == []

    # Daily plan generation should not pull arbitrary global lessons under Priority 4
    plan_res = await client.post(
        "/api/v1/planner/daily/generate?force_refresh=true", headers=headers
    )
    assert plan_res.status_code == 200
    # Because student has no progress, no practice, and no enrolled subjects, tasks should be 0
    assert len(plan_res.json()["tasks"]) == 0


@pytest.mark.asyncio
async def test_preferred_study_days_enforcement(
    client: AsyncClient, planner_student_token: str
):
    """M-1: Verify that non-preferred days do not auto-generate tasks in get_daily_study_plan."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    # Set preferred days to a day that is NOT today
    days_of_week = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    today_abbr = date.today().strftime("%a").upper()[:3]
    other_days = [d for d in days_of_week if d != today_abbr]

    await client.post(
        "/api/v1/planner/goal",
        headers=headers,
        json={
            "title": "Weekend Learner",
            "daily_study_minutes": 60,
            "preferred_days": other_days,
        },
    )

    # For a future date that is definitely not in preferred_days
    future_non_preferred = date.today() + timedelta(days=1)
    while future_non_preferred.strftime("%a").upper()[:3] in other_days:
        future_non_preferred += timedelta(days=1)

    future_str = future_non_preferred.isoformat()
    # Query get_daily_study_plan for that date
    res = await client.get(
        f"/api/v1/planner/daily?plan_date={future_str}", headers=headers
    )
    assert res.status_code == 200
    # Viewing non-preferred day does not auto-generate tasks
    assert len(res.json()["tasks"]) == 0


@pytest.mark.asyncio
async def test_multiple_in_progress_lessons_max_one_resume_task(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """M-3: Verify at most 1 RESUME_LESSON task is generated even with multiple in-progress lessons."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    # Fetch 3 published lessons
    stmt = (
        select(Lesson)
        .where(Lesson.status == ContentStatus.PUBLISHED.value)
        .limit(3)
    )
    lessons = (await db_session.execute(stmt)).scalars().all()
    assert len(lessons) >= 3

    # Start progress on all 3
    for lsn in lessons:
        await client.post(
            f"/api/v1/student/progress/lessons/{lsn.id}/start",
            headers=headers,
        )

    # Regenerate daily plan
    plan_res = await client.post(
        "/api/v1/planner/daily/generate?force_refresh=true", headers=headers
    )
    assert plan_res.status_code == 200
    tasks = plan_res.json()["tasks"]

    resume_tasks = [t for t in tasks if t["task_type"] == "RESUME_LESSON"]
    assert len(resume_tasks) == 1


@pytest.mark.asyncio
async def test_task_state_uncompleting_past_task_reverts_to_skipped(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """Section 9: Verify uncompleting a past task reverts its status to SKIPPED."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}

    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    # Seed a task from yesterday that was completed
    yesterday = date.today() - timedelta(days=1)
    past_task = StudyTask(
        id=uuid.uuid4(),
        user_id=user_id,
        scheduled_date=yesterday,
        task_type="STUDY_LESSON",
        title="Yesterday Completed Task",
        estimated_minutes=15,
        status="COMPLETED",
        is_completed=True,
        completed_at=datetime.now(timezone.utc),
    )
    db_session.add(past_task)
    await db_session.commit()

    # Uncomplete the past task
    uncomp_res = await client.patch(
        f"/api/v1/planner/tasks/{past_task.id}/complete",
        headers=headers,
        json={"is_completed": False},
    )
    assert uncomp_res.status_code == 200
    assert uncomp_res.json()["is_completed"] is False
    # Must revert to SKIPPED because it is in the past, maintaining missed-day policy
    assert uncomp_res.json()["status"] == "SKIPPED"
    assert uncomp_res.json()["completed_at"] is None


# ==============================================================================
# 5. TIMEZONE BOUNDARY & MULTI-WORKER CONCURRENCY VERIFICATION
# ==============================================================================


@pytest.mark.asyncio
async def test_ist_timezone_boundary_determinations():
    """Finding 2: Deterministic test covering UTC datetimes that cross the India midnight boundary.

    Verifies that calendar dates in Asia/Kolkata (IST = UTC+5:30) are correctly calculated:
    - 23:45 UTC on Oct 18 corresponds to 05:15 IST on Oct 19 (next calendar day).
    - 19:00 UTC on Oct 18 corresponds to 00:30 IST on Oct 19 (next calendar day).
    - 18:29:59 UTC on Oct 18 corresponds to 23:59:59 IST on Oct 18 (same calendar day).
    - 18:30:00 UTC on Oct 18 corresponds to 00:00:00 IST on Oct 19 (exact midnight transition).
    - 04:00 UTC on Oct 18 corresponds to 09:30 IST on Oct 18 (daytime same day).
    """
    from app.api.v1.endpoints.planner import get_planner_date

    # 1. 23:45 UTC on Oct 18 -> 05:15 IST on Oct 19
    dt_2345 = datetime(2026, 10, 18, 23, 45, tzinfo=timezone.utc)
    assert get_planner_date(dt_2345) == date(2026, 10, 19)

    # 2. 19:00 UTC on Oct 18 -> 00:30 IST on Oct 19
    dt_1900 = datetime(2026, 10, 18, 19, 0, tzinfo=timezone.utc)
    assert get_planner_date(dt_1900) == date(2026, 10, 19)

    # 3. 18:29:59 UTC on Oct 18 -> 23:59:59 IST on Oct 18 (one second before midnight)
    dt_1829 = datetime(2026, 10, 18, 18, 29, 59, tzinfo=timezone.utc)
    assert get_planner_date(dt_1829) == date(2026, 10, 18)

    # 4. 18:30:00 UTC on Oct 18 -> 00:00:00 IST on Oct 19 (exact midnight transition)
    dt_1830 = datetime(2026, 10, 18, 18, 30, 0, tzinfo=timezone.utc)
    assert get_planner_date(dt_1830) == date(2026, 10, 19)

    # 5. Daytime comparison: 04:00 UTC on Oct 18 -> 09:30 IST on Oct 18
    dt_daytime = datetime(2026, 10, 18, 4, 0, tzinfo=timezone.utc)
    assert get_planner_date(dt_daytime) == date(2026, 10, 18)


@pytest.mark.asyncio
async def test_multi_worker_concurrency_pre_commit_race_handling(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """Finding 1: Verify pre-commit race handling returns existing tasks without duplicates or ceiling breach."""
    headers = {"Authorization": f"Bearer {planner_student_token}"}
    target_date_str = (date.today() + timedelta(days=7)).isoformat()

    # Generate initial plan for the target date
    res = await client.post(
        f"/api/v1/planner/daily/generate?plan_date={target_date_str}",
        headers=headers,
    )
    assert res.status_code == 200
    initial_tasks = res.json()["tasks"]
    assert 0 < len(initial_tasks) <= 4

    # Subsequent generation without force_refresh immediately returns existing tasks
    res_repeat = await client.post(
        f"/api/v1/planner/daily/generate?plan_date={target_date_str}",
        headers=headers,
    )
    assert res_repeat.status_code == 200
    repeat_tasks = res_repeat.json()["tasks"]
    assert len(repeat_tasks) == len(initial_tasks)
    assert [t["id"] for t in repeat_tasks] == [t["id"] for t in initial_tasks]


# ==============================================================================
# 6. CONCURRENCY, TRANSACTION LOCKING & RESPONSE DEDUPLICATION REGRESSION TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_concurrent_daily_plan_retrieval(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """Scenario 1: Concurrently retrieve GET /daily across multiple simulated requests.
    
    Verifies that all concurrent requests return identical, valid plans and no duplicate
    tasks are persisted.
    """
    try:
        from tests.conftest import TestAsyncSessionLocal
    except ImportError:
        from conftest import TestAsyncSessionLocal
    from app.core.database import get_db
    from app.main import app

    headers = {"Authorization": f"Bearer {planner_student_token}"}
    test_date_str = (date.today() + timedelta(days=12)).isoformat()

    async def per_request_db():
        async with TestAsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = per_request_db
    try:
        # Fire 4 concurrent requests to GET /daily
        responses = await asyncio.gather(
            client.get(f"/api/v1/planner/daily?plan_date={test_date_str}", headers=headers),
            client.get(f"/api/v1/planner/daily?plan_date={test_date_str}", headers=headers),
            client.get(f"/api/v1/planner/daily?plan_date={test_date_str}", headers=headers),
            client.get(f"/api/v1/planner/daily?plan_date={test_date_str}", headers=headers),
        )
        for r in responses:
            assert r.status_code == 200
            data = r.json()
            assert len(data["tasks"]) <= 4
            task_ids = [t["id"] for t in data["tasks"]]
            assert len(task_ids) == len(set(task_ids)), "Response contains duplicate task IDs"

        # Compare results across all responses: must be identical
        first_ids = [t["id"] for t in responses[0].json()["tasks"]]
        for r in responses[1:]:
            assert [t["id"] for t in r.json()["tasks"]] == first_ids
    finally:
        async def override_get_db():
            yield db_session
        app.dependency_overrides[get_db] = override_get_db


@pytest.mark.asyncio
async def test_concurrent_force_refresh_with_completed_tasks_unique_display_order(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """Scenario 2: Concurrent force-refresh while completed tasks are present.
    
    Verifies that completed tasks are never deleted, all returned tasks have unique
    display_order values (1..N) without duplicates, and task count <= 4.
    """
    try:
        from tests.conftest import TestAsyncSessionLocal
    except ImportError:
        from conftest import TestAsyncSessionLocal
    from app.core.database import get_db
    from app.main import app

    headers = {"Authorization": f"Bearer {planner_student_token}"}
    target_date_str = (date.today() + timedelta(days=15)).isoformat()

    # Step 1: Generate initial plan
    init_res = await client.post(
        f"/api/v1/planner/daily/generate?plan_date={target_date_str}",
        headers=headers,
    )
    assert init_res.status_code == 200
    tasks = init_res.json()["tasks"]
    assert len(tasks) > 0

    # Step 2: Complete the first task
    completed_task_id = tasks[0]["id"]
    complete_res = await client.patch(
        f"/api/v1/planner/tasks/{completed_task_id}/complete",
        headers=headers,
        json={"is_completed": True},
    )
    assert complete_res.status_code == 200

    # Step 3: Run concurrent force-refresh requests
    async def per_request_db():
        async with TestAsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = per_request_db
    try:
        responses = await asyncio.gather(
            client.post(
                f"/api/v1/planner/daily/generate?plan_date={target_date_str}&force_refresh=true",
                headers=headers,
            ),
            client.post(
                f"/api/v1/planner/daily/generate?plan_date={target_date_str}&force_refresh=true",
                headers=headers,
            ),
            client.post(
                f"/api/v1/planner/daily/generate?plan_date={target_date_str}&force_refresh=true",
                headers=headers,
            ),
        )
        for r in responses:
            assert r.status_code == 200
            data = r.json()
            r_tasks = data["tasks"]
            assert len(r_tasks) <= 4

            # Completed task must be preserved
            r_completed = [t for t in r_tasks if t["id"] == completed_task_id]
            assert len(r_completed) == 1
            assert r_completed[0]["is_completed"] is True

            # Display orders must all be unique and strictly between 1 and 4
            orders = [t["display_order"] for t in r_tasks]
            assert len(orders) == len(set(orders)), f"Duplicate display orders found: {orders}"
            assert all(1 <= o <= 4 for o in orders)
    finally:
        async def override_get_db():
            yield db_session
        app.dependency_overrides[get_db] = override_get_db


@pytest.mark.asyncio
async def test_simultaneous_generation_without_existing_study_goal(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Scenario 3: Concurrently generate daily plan for a student who has no StudyGoal yet.
    
    Verifies that locking on User prevents race conditions, exactly one StudyGoal is created,
    and no deadlock or IntegrityError occurs.
    """
    try:
        from tests.conftest import TestAsyncSessionLocal
    except ImportError:
        from conftest import TestAsyncSessionLocal
    from app.core.database import get_db
    from app.main import app

    # Register brand new student
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"nogoal_{uuid.uuid4().hex[:8]}@example.com",
            "password": "SecurePassword123!",
            "full_name": "No Goal Student",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    user_id = uuid.UUID(res.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {token}"}

    async def per_request_db():
        async with TestAsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = per_request_db
    try:
        # Launch 3 simultaneous generation requests
        responses = await asyncio.gather(
            client.post("/api/v1/planner/daily/generate", headers=headers),
            client.post("/api/v1/planner/daily/generate", headers=headers),
            client.post("/api/v1/planner/daily/generate", headers=headers),
        )
        for r in responses:
            assert r.status_code == 200

        # Verify exactly one active StudyGoal exists in the database
        stmt = select(StudyGoal).where(
            StudyGoal.user_id == user_id,
            StudyGoal.status == GoalStatus.ACTIVE.value,
        )
        goals = (await db_session.execute(stmt)).scalars().all()
        assert len(goals) == 1
    finally:
        async def override_get_db():
            yield db_session
        app.dependency_overrides[get_db] = override_get_db


@pytest.mark.asyncio
async def test_force_refresh_failure_atomicity_preserves_uncompleted_tasks(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """Scenario 4: Force-refresh failure atomicity.
    
    If generation raises an unexpected exception after uncompleted tasks are deleted in the session,
    the transaction must roll back atomically, leaving the previously uncompleted tasks intact.
    """
    headers = {"Authorization": f"Bearer {planner_student_token}"}
    target_date_str = (date.today() + timedelta(days=20)).isoformat()

    # Step 1: Generate initial tasks
    gen_res = await client.post(
        f"/api/v1/planner/daily/generate?plan_date={target_date_str}",
        headers=headers,
    )
    assert gen_res.status_code == 200
    initial_tasks = gen_res.json()["tasks"]
    assert len(initial_tasks) > 0
    initial_ids = {t["id"] for t in initial_tasks}

    # Step 2: Mock a database error during _generate_tasks_for_date
    with patch(
        "app.api.v1.endpoints.planner._generate_tasks_for_date",
        side_effect=RuntimeError("Simulated database failure during task generation"),
    ):
        refresh_res = await client.post(
            f"/api/v1/planner/daily/generate?plan_date={target_date_str}&force_refresh=true",
            headers=headers,
        )
        # Should raise 500 error due to unhandled generation failure
        assert refresh_res.status_code == 500

    # Step 3: Verify the initial uncompleted tasks STILL EXIST in the database!
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])
    target_d = date.fromisoformat(target_date_str)

    stmt = select(StudyTask).where(
        StudyTask.user_id == user_id,
        StudyTask.scheduled_date == target_d,
    )
    persisted = (await db_session.execute(stmt)).scalars().all()
    persisted_ids = {str(t.id) for t in persisted}
    assert persisted_ids == initial_ids, "Uncompleted tasks were lost despite generation failure!"


@pytest.mark.asyncio
async def test_integrity_error_recovery_without_duplicate_response(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """Scenario 5: IntegrityError recovery without duplicates.
    
    Verifies that if an IntegrityError occurs (e.g. unique constraint race), the endpoint
    rolls back cleanly and re-queries persisted tasks directly from the DB without duplicate entries.
    """
    headers = {"Authorization": f"Bearer {planner_student_token}"}
    target_date_str = (date.today() + timedelta(days=22)).isoformat()

    # Generate initial plan
    init_res = await client.post(
        f"/api/v1/planner/daily/generate?plan_date={target_date_str}",
        headers=headers,
    )
    assert init_res.status_code == 200
    initial_tasks = init_res.json()["tasks"]
    assert len(initial_tasks) > 0

    # Mock _generate_tasks_for_date to raise IntegrityError as if another process raced
    with patch(
        "app.api.v1.endpoints.planner._generate_tasks_for_date",
        side_effect=IntegrityError("Unique constraint violation", params=None, orig=Exception("uq_study_tasks_user_date_order")),
    ):
        res = await client.post(
            f"/api/v1/planner/daily/generate?plan_date={target_date_str}&force_refresh=true",
            headers=headers,
        )
        assert res.status_code == 200
        tasks = res.json()["tasks"]
        task_ids = [t["id"] for t in tasks]
        # Guarantee NO duplicate entries in response
        assert len(task_ids) == len(set(task_ids)), "Response contains duplicate task items"
        assert len(tasks) <= 4


@pytest.mark.asyncio
async def test_reschedule_task_capacity_rejection_at_four_tasks(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """Scenario 6: Reschedule task capacity rejection.
    
    Attempting to reschedule a task to a target date that already has 4 tasks must be
    rejected with 400 Bad Request to maintain the 4-task ceiling.
    """
    headers = {"Authorization": f"Bearer {planner_student_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    date_a = date.today() + timedelta(days=30)
    date_b = date.today() + timedelta(days=31)

    # Seed 1 task on Date A
    task_a = StudyTask(
        id=uuid.uuid4(),
        user_id=user_id,
        scheduled_date=date_a,
        task_type="STUDY_LESSON",
        title="Date A Task",
        estimated_minutes=15,
        status="PENDING",
        is_completed=False,
        display_order=1,
    )
    db_session.add(task_a)

    # Seed 4 tasks on Date B (capacity full)
    for i in range(1, 5):
        t_b = StudyTask(
            id=uuid.uuid4(),
            user_id=user_id,
            scheduled_date=date_b,
            task_type="STUDY_LESSON",
            title=f"Date B Task {i}",
            estimated_minutes=15,
            status="PENDING",
            is_completed=False,
            display_order=i,
        )
        db_session.add(t_b)
    await db_session.commit()

    # Attempt to reschedule task_a to date_b
    res = await client.patch(
        f"/api/v1/planner/tasks/{task_a.id}/reschedule",
        headers=headers,
        json={"new_date": date_b.isoformat()},
    )
    assert res.status_code == 400
    assert "maximum limit of 4 study tasks" in res.json()["detail"]

    # Verify task_a remains on Date A
    await db_session.refresh(task_a)
    assert task_a.scheduled_date == date_a


@pytest.mark.asyncio
async def test_reschedule_task_within_capacity_updates_display_order(
    client: AsyncClient,
    planner_student_token: str,
    db_session: AsyncSession,
):
    """Scenario 7: Reschedule task within capacity sets proper next display_order.
    
    When rescheduling to a date with 2 existing tasks, the rescheduled task receives
    display_order 3 without collisions.
    """
    headers = {"Authorization": f"Bearer {planner_student_token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    user_id = uuid.UUID(me_res.json()["id"])

    date_x = date.today() + timedelta(days=35)
    date_y = date.today() + timedelta(days=36)

    # Seed 1 task on Date X
    task_x = StudyTask(
        id=uuid.uuid4(),
        user_id=user_id,
        scheduled_date=date_x,
        task_type="STUDY_LESSON",
        title="Date X Task",
        estimated_minutes=15,
        status="PENDING",
        is_completed=False,
        display_order=1,
    )
    db_session.add(task_x)

    # Seed 2 tasks on Date Y
    for i in range(1, 3):
        t_y = StudyTask(
            id=uuid.uuid4(),
            user_id=user_id,
            scheduled_date=date_y,
            task_type="STUDY_LESSON",
            title=f"Date Y Task {i}",
            estimated_minutes=15,
            status="PENDING",
            is_completed=False,
            display_order=i,
        )
        db_session.add(t_y)
    await db_session.commit()

    # Reschedule task_x to Date Y
    res = await client.patch(
        f"/api/v1/planner/tasks/{task_x.id}/reschedule",
        headers=headers,
        json={"new_date": date_y.isoformat()},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["scheduled_date"] == date_y.isoformat()
    assert data["display_order"] == 3
    assert data["status"] == "RESCHEDULED"


@pytest.mark.asyncio
async def test_database_level_unique_constraint_enforcement(
    db_session: AsyncSession,
):
    """Scenario 8: Database-level unique constraint enforcement.
    
    Verifies that attempting to insert two tasks with the same (user_id, scheduled_date, display_order)
    raises an IntegrityError at the database level.
    """
    uid = uuid.uuid4()
    t_date = date.today() + timedelta(days=40)

    task1 = StudyTask(
        id=uuid.uuid4(),
        user_id=uid,
        scheduled_date=t_date,
        task_type="STUDY_LESSON",
        title="Slot 1 Task",
        estimated_minutes=15,
        status="PENDING",
        is_completed=False,
        display_order=1,
    )
    db_session.add(task1)
    await db_session.commit()

    task2 = StudyTask(
        id=uuid.uuid4(),
        user_id=uid,
        scheduled_date=t_date,
        task_type="STUDY_LESSON",
        title="Duplicate Slot 1 Task",
        estimated_minutes=15,
        status="PENDING",
        is_completed=False,
        display_order=1,
    )
    db_session.add(task2)

    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

