"""Milestone 8 Automated Test Suite: Student Learning Analytics, Diagnostic Trends & Progress Visualization."""

from datetime import date, datetime, timedelta, timezone
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.sm2 import get_ist_date, PLANNER_TZ
from app.models.assessment import PracticeSession, Question, QuestionAttempt, QuestionType
from app.models.content import ContentStatus, Lesson, LessonProgress, LessonProgressStatus
from app.models.identity import StudentProfile, User
from app.models.planner import GoalStatus, StudyGoal, StudyTask, TaskStatus, TaskType
from app.models.repetition import ReviewItem, ReviewLog, ReviewStatus
from app.models.taxonomy import Chapter, Subject, Topic


@pytest_asyncio.fixture
async def student_user_a(client: AsyncClient, db_session: AsyncSession):
    """Register Student A and return (token, user_id)."""
    email = f"trends_student_a_{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": "Trends Student A",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    user_row = (
        await db_session.execute(select(User).where(User.email == email))
    ).scalar_one()
    return token, user_row.id


@pytest_asyncio.fixture
async def student_user_b(client: AsyncClient, db_session: AsyncSession):
    """Register Student B and return (token, user_id)."""
    email = f"trends_student_b_{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": "Trends Student B",
        },
    )
    assert res.status_code == 201
    token = res.json()["access_token"]
    user_row = (
        await db_session.execute(select(User).where(User.email == email))
    ).scalar_one()
    return token, user_row.id


# ==============================================================================
# 1. PRACTICE TRENDS ENDPOINT TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_practice_trends_empty_state_null_safety(
    client: AsyncClient, student_user_a
):
    """Verify empty student returns complete 7-day range with 0 counts and null accuracy."""
    token, _ = student_user_a
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/student/analytics/trends/practice?days=7", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["days_count"] == 7
    assert len(data["daily_trends"]) == 7
    assert data["total_questions_answered"] == 0
    assert data["total_correct_count"] == 0
    assert data["overall_accuracy_percentage"] is None
    assert data["total_practice_minutes"] == 0.0

    today = get_ist_date()
    expected_start = (today - timedelta(days=6)).isoformat()
    assert data["start_date"] == expected_start
    assert data["end_date"] == today.isoformat()

    # Check that every single day has questions_answered=0 and accuracy_percentage=None
    for item in data["daily_trends"]:
        assert item["questions_answered"] == 0
        assert item["correct_count"] == 0
        assert item["accuracy_percentage"] is None
        assert item["practice_minutes"] == 0.0


@pytest.mark.asyncio
async def test_practice_trends_14_days_and_bucket_accuracy(
    client: AsyncClient, student_user_a, student_user_b, db_session: AsyncSession
):
    """Verify 14-day practice trends, accurate bucket placement, and cross-student isolation."""
    token_a, user_a_id = student_user_a
    token_b, user_b_id = student_user_b

    # Find a published question
    q_stmt = select(Question).limit(1)
    question = (await db_session.execute(q_stmt)).scalar_one_or_none()
    assert question is not None

    today_ist = get_ist_date()
    yesterday_ist = today_ist - timedelta(days=1)

    # Convert IST to UTC naive datetime for attempt
    yesterday_dt_utc = datetime.combine(
        yesterday_ist, datetime(2026, 1, 1, 12, 0).time(), tzinfo=PLANNER_TZ
    ).astimezone(timezone.utc).replace(tzinfo=None)

    # Insert attempts for Student A on yesterday: 4 total, 3 correct, 60s each
    for i in range(4):
        db_session.add(
            QuestionAttempt(
                user_id=user_a_id,
                question_id=question.id,
                is_correct=(i < 3),
                time_spent_seconds=60,
                attempted_at=yesterday_dt_utc,
            )
        )

    # Insert attempt for Student B (to test IDOR isolation)
    db_session.add(
        QuestionAttempt(
            user_id=user_b_id,
            question_id=question.id,
            is_correct=False,
            time_spent_seconds=120,
            attempted_at=yesterday_dt_utc,
        )
    )
    await db_session.commit()

    headers_a = {"Authorization": f"Bearer {token_a}"}
    resp = await client.get("/api/v1/student/analytics/trends/practice?days=14", headers=headers_a)
    assert resp.status_code == 200
    data = resp.json()

    assert data["days_count"] == 14
    assert len(data["daily_trends"]) == 14
    assert data["total_questions_answered"] == 4
    assert data["total_correct_count"] == 3
    assert data["overall_accuracy_percentage"] == 75.0
    assert data["total_practice_minutes"] == 4.0  # 4 * 60s = 4.0 mins

    # Find yesterday's trend item
    yesterday_str = yesterday_ist.isoformat()
    y_item = next(d for d in data["daily_trends"] if d["date"] == yesterday_str)
    assert y_item["questions_answered"] == 4
    assert y_item["correct_count"] == 3
    assert y_item["accuracy_percentage"] == 75.0
    assert y_item["practice_minutes"] == 4.0

    # Verify Student B has no attempts in their trends
    headers_b = {"Authorization": f"Bearer {token_b}"}
    resp_b = await client.get("/api/v1/student/analytics/trends/practice?days=14", headers=headers_b)
    data_b = resp_b.json()
    assert data_b["total_questions_answered"] == 1
    assert data_b["total_correct_count"] == 0
    assert data_b["overall_accuracy_percentage"] == 0.0


# ==============================================================================
# 2. STUDY PLANNER TRENDS & ADHERENCE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_planner_trends_adherence_and_rest_days(
    client: AsyncClient, student_user_a, db_session: AsyncSession
):
    """Verify study planner adherence tracks completed minutes, preferred days, and handles rest days non-punitively."""
    token, user_id = student_user_a
    headers = {"Authorization": f"Bearer {token}"}

    today_ist = get_ist_date()
    yesterday_ist = today_ist - timedelta(days=1)
    two_days_ago_ist = today_ist - timedelta(days=2)

    today_day = today_ist.strftime("%a").upper()
    yesterday_day = yesterday_ist.strftime("%a").upper()

    # Create active study goal with only today & yesterday as preferred days
    goal = StudyGoal(
        user_id=user_id,
        title="Focused Goal",
        daily_study_minutes=60,
        preferred_days=[today_day, yesterday_day],
        status=GoalStatus.ACTIVE.value,
    )
    db_session.add(goal)
    await db_session.flush()

    # Yesterday: scheduled 2 tasks (30m each) -> both completed -> Goal Met
    task_y1 = StudyTask(
        user_id=user_id,
        goal_id=goal.id,
        scheduled_date=yesterday_ist,
        task_type=TaskType.STUDY_LESSON.value,
        title="Yesterday Task 1",
        estimated_minutes=30,
        status=TaskStatus.COMPLETED.value,
        is_completed=True,
        display_order=1,
    )
    task_y2 = StudyTask(
        user_id=user_id,
        goal_id=goal.id,
        scheduled_date=yesterday_ist,
        task_type=TaskType.PRACTICE_TOPIC.value,
        title="Yesterday Task 2",
        estimated_minutes=30,
        status=TaskStatus.COMPLETED.value,
        is_completed=True,
        display_order=2,
    )
    # Today: scheduled 1 task (30m) -> pending -> Goal Not Met
    task_t1 = StudyTask(
        user_id=user_id,
        goal_id=goal.id,
        scheduled_date=today_ist,
        task_type=TaskType.STUDY_LESSON.value,
        title="Today Task 1",
        estimated_minutes=30,
        status=TaskStatus.PENDING.value,
        is_completed=False,
        display_order=1,
    )
    # Two days ago: rest day with a completed task (rest day non-punitive)
    task_r = StudyTask(
        user_id=user_id,
        goal_id=goal.id,
        scheduled_date=two_days_ago_ist,
        task_type=TaskType.REVISE_TOPIC.value,
        title="Rest Day Bonus Task",
        estimated_minutes=15,
        status=TaskStatus.COMPLETED.value,
        is_completed=True,
        display_order=1,
    )
    db_session.add_all([task_y1, task_y2, task_t1, task_r])
    await db_session.commit()

    resp = await client.get("/api/v1/student/analytics/trends/planner?days=7", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["daily_study_goal_minutes"] == 60
    assert data["days_count"] == 7
    # 7-day window contains exactly 2 preferred days (today and yesterday)
    assert data["preferred_days_count"] == 2
    assert data["goals_met_count"] == 1  # only yesterday met
    assert data["adherence_rate_percentage"] == 50.0  # 1/2 * 100 = 50.0%
    assert data["total_planned_minutes"] == 105
    assert data["total_completed_minutes"] == 75

    # Check yesterday's item
    y_item = next(d for d in data["daily_trends"] if d["date"] == yesterday_ist.isoformat())
    assert y_item["is_preferred_day"] is True
    assert y_item["has_plan"] is True
    assert y_item["planned_minutes"] == 60
    assert y_item["completed_minutes"] == 60
    assert y_item["is_goal_met"] is True


# ==============================================================================
# 3. SPICED REPETITION RETENTION TRENDS TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_retention_trends_streak_overdue_and_forecast(
    client: AsyncClient, student_user_a, db_session: AsyncSession
):
    """Verify active streak count, overdue aging breakdown (1-3d vs 4+d), and 7-day forecast."""
    token, user_id = student_user_a
    headers = {"Authorization": f"Bearer {token}"}

    today_ist = get_ist_date()
    yesterday_ist = today_ist - timedelta(days=1)
    two_days_ago_ist = today_ist - timedelta(days=2)

    # 1. Setup ReviewItem and ReviewLogs for a 3-day active streak (2 days ago, yesterday, today)
    subj_stmt = select(Subject).limit(1)
    subject = (await db_session.execute(subj_stmt)).scalar_one()
    top_stmt = select(Topic).limit(4)
    topics = list((await db_session.execute(top_stmt)).scalars().all())
    assert len(topics) >= 4

    rev_item = ReviewItem(
        user_id=user_id,
        topic_id=topics[0].id,
        subject_id=subject.id,
        repetition_count=3,
        ease_factor=2.5,
        interval_days=6,
        due_date=today_ist,
        status=ReviewStatus.REVIEW.value,
    )
    db_session.add(rev_item)
    await db_session.flush()

    # Add logs on two days ago, yesterday, and today
    for d in [two_days_ago_ist, yesterday_ist, today_ist]:
        rev_dt_utc = datetime.combine(d, datetime(2026, 1, 1, 10, 0).time(), tzinfo=PLANNER_TZ).astimezone(timezone.utc)
        db_session.add(
            ReviewLog(
                review_item_id=rev_item.id,
                user_id=user_id,
                quality_score=4,
                time_spent_seconds=45,
                scheduled_interval_days=6,
                next_interval_days=15,
                ease_factor_before=2.5,
                ease_factor_after=2.5,
                reviewed_at=rev_dt_utc,
            )
        )

    # 2. Add an overdue item (2 days overdue -> overdue_1_to_3_days)
    rev_overdue_1 = ReviewItem(
        user_id=user_id,
        topic_id=topics[1].id,
        subject_id=subject.id,
        repetition_count=1,
        ease_factor=2.5,
        interval_days=1,
        due_date=today_ist - timedelta(days=2),
        status=ReviewStatus.LEARNING.value,
    )
    # 3. Add an overdue item (5 days overdue -> overdue_4_plus_days)
    rev_overdue_2 = ReviewItem(
        user_id=user_id,
        topic_id=topics[2].id,
        subject_id=subject.id,
        repetition_count=1,
        ease_factor=2.5,
        interval_days=1,
        due_date=today_ist - timedelta(days=5),
        status=ReviewStatus.LEARNING.value,
    )
    # 4. Add item in 7-day forecast (tomorrow)
    rev_future_1 = ReviewItem(
        user_id=user_id,
        topic_id=topics[3].id,
        subject_id=subject.id,
        repetition_count=2,
        ease_factor=2.5,
        interval_days=6,
        due_date=today_ist + timedelta(days=1),
        status=ReviewStatus.REVIEW.value,
    )
    db_session.add_all([rev_overdue_1, rev_overdue_2, rev_future_1])
    await db_session.commit()

    resp = await client.get("/api/v1/student/analytics/trends/retention", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["active_streak_days"] == 3
    assert data["is_streak_active_today"] is True
    assert data["last_reviewed_date"] == today_ist.isoformat()

    assert data["due_today_count"] == 1
    assert data["overdue_1_to_3_days"] == 1
    assert data["overdue_4_plus_days"] == 1
    assert data["total_overdue_count"] == 2

    assert len(data["forecast_next_7_days"]) == 7
    tomorrow_str = (today_ist + timedelta(days=1)).isoformat()
    item_tom = next(f for f in data["forecast_next_7_days"] if f["date"] == tomorrow_str)
    assert item_tom["due_count"] == 1


# ==============================================================================
# 4. DIAGNOSTIC MATRIX TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_diagnostic_matrix_precedence_and_states(
    client: AsyncClient, student_user_a, db_session: AsyncSession
):
    """Verify diagnostic state hierarchy:
    - CRITICAL_GAP (attempts >= 5 with accuracy < 60%)
    - UNPRACTICED_FOUNDATION (lesson completed but attempts < 5)
    - MASTERED (attempts >= 5, accuracy >= 80%, review_status == MASTERED)
    - SOLIDIFYING (attempts >= 5, accuracy >= 60%)
    - NOT_STARTED
    """
    token, user_id = student_user_a
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch topics to assign states
    top_stmt = select(Topic).options(selectinload(Topic.chapter).selectinload(Chapter.subject), selectinload(Topic.lessons)).limit(4)
    topics = list((await db_session.execute(top_stmt)).scalars().all())
    assert len(topics) >= 1

    topic1 = topics[0]
    # Set up Topic 1 as CRITICAL_GAP: 5 attempts, 1 correct (20% accuracy)
    # Get or create questions for topic1
    q_stmt = select(Question).where(Question.topic_id == topic1.id).limit(1)
    q = (await db_session.execute(q_stmt)).scalar_one_or_none()
    if not q:
        q = Question(
            topic_id=topic1.id,
            question_text="Sample Q",
            question_type=QuestionType.SINGLE_CHOICE.value,
            difficulty="EASY",
            is_active=True,
        )
        db_session.add(q)
        await db_session.flush()

    for i in range(5):
        db_session.add(
            QuestionAttempt(
                user_id=user_id,
                question_id=q.id,
                is_correct=(i == 0),
                time_spent_seconds=30,
            )
        )
    await db_session.commit()

    resp = await client.get("/api/v1/student/analytics/diagnostic-matrix", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_topics_analyzed"] >= 1
    t1_diag = next(t for t in data["topics"] if t["topic_id"] == str(topic1.id))
    assert t1_diag["total_attempts"] == 5
    assert t1_diag["observed_accuracy_percentage"] == 20.0
    assert t1_diag["practice_category"] == "NEEDS_REVIEW"
    assert t1_diag["diagnostic_state"] == "CRITICAL_GAP"
    assert "Urgent review required" in t1_diag["action_recommendation"]
    assert data["critical_gaps_count"] >= 1
