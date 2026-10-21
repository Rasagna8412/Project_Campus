"""Regression tests for student account deletion integrity (DPDP Act compliance)."""

import uuid
from datetime import date
import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from app.models.assessment import (
    PracticeSession,
    Question,
    QuestionAttempt,
    QuestionErrataReport,
)
from app.models.content import LessonProgress, Lesson
from app.models.identity import StudentProfile, StudentProfileSubject, User, UserRole
from app.models.planner import StudyGoal, StudyTask
from app.models.repetition import ReviewItem, ReviewLog, ReviewStatus
from app.core.config import settings
from app.models.taxonomy import BoardCurriculum, GradeStage, Subject, Topic


@pytest.mark.asyncio
async def test_account_deletion_cleanses_all_personal_records(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify that deleting a student account permanently removes all personal records,

    including errata reports, profile associations, practice sessions, attempts, progress,
    goals, tasks, and review items, while keeping shared questions and curriculum intact.
    """
    # 1. Register Student A
    email_a = f"del_clean_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123!", "full_name": "Delete Target"},
    )
    assert reg_resp.status_code == 201
    token_a = reg_resp.json()["access_token"]
    user_id_a = uuid.UUID(reg_resp.json()["user"]["id"])
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Complete onboarding (creates StudentProfile & StudentProfileSubject)
    curricula = (await client.get("/api/v1/curricula/")).json()
    cbse = next(c for c in curricula if c["code"] == "CBSE")
    grade = cbse["grades"][0]
    subj_ids = [s["id"] for s in grade["subjects"][:2]]
    subj = (await db_session.execute(select(Subject).limit(1))).scalar_one()
    topic = (await db_session.execute(select(Topic).limit(1))).scalar_one()
    question = (await db_session.execute(select(Question).limit(1))).scalar_one()

    onboard_res = await client.put(
        "/api/v1/student/onboarding",
        json={
            "target_curriculum_id": cbse["id"],
            "grade_stage_id": grade["id"],
            "target_exam_year": 2027,
            "daily_study_goal_minutes": 90,
            "preferred_language": "en",
            "selected_subject_ids": subj_ids,
            "complete": True,
        },
        headers=headers_a,
    )
    assert onboard_res.status_code == 200

    # 3. Create Errata Report
    errata_res = await client.post(
        f"/api/v1/practice/questions/{question.id}/report-errata",
        json={
            "question_id": str(question.id),
            "issue_type": "TYPO",
            "description": "Found a typo in explanation.",
        },
        headers=headers_a,
    )
    assert errata_res.status_code == 201

    # 4. Create Practice Session & Attempt
    sess = PracticeSession(user_id=user_id_a, topic_id=topic.id, session_type="TOPIC_PRACTICE")
    db_session.add(sess)
    await db_session.flush()

    att = QuestionAttempt(
        session_id=sess.id,
        user_id=user_id_a,
        question_id=question.id,
        is_correct=True,
        time_spent_seconds=45,
    )
    db_session.add(att)

    # 5. Create LessonProgress
    lesson = (await db_session.execute(select(Lesson).limit(1))).scalar_one_or_none()
    if lesson:
        prog = LessonProgress(user_id=user_id_a, lesson_id=lesson.id, status="COMPLETED")
        db_session.add(prog)

    # 6. Create StudyGoal & StudyTask
    goal = StudyGoal(user_id=user_id_a, title="Board Prep", daily_study_minutes=120)
    db_session.add(goal)
    await db_session.flush()

    task = StudyTask(
        user_id=user_id_a,
        goal_id=goal.id,
        scheduled_date=date.today(),
        title="Account deletion test task",
        subject_id=subj.id,
        topic_id=topic.id,
        estimated_minutes=30,
    )
    db_session.add(task)

    # 7. Create ReviewItem & ReviewLog
    rev_item = ReviewItem(
        user_id=user_id_a,
        topic_id=topic.id,
        subject_id=subj.id,
        status=ReviewStatus.LEARNING.value,
        ease_factor=2.50,
        interval_days=1,
        due_date=date.today(),
    )
    db_session.add(rev_item)
    await db_session.flush()

    rev_log = ReviewLog(
        review_item_id=rev_item.id,
        user_id=user_id_a,
        quality_score=4,
        ease_factor_before=2.50,
        ease_factor_after=2.50,
        scheduled_interval_days=1,
        next_interval_days=6,
    )
    db_session.add(rev_log)
    await db_session.commit()

    # Record IDs before deletion
    profile_before = (
        await db_session.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id_a)
        )
    ).scalar_one_or_none()
    profile_id_a = profile_before.id if profile_before else None

    # Verify errata report exists before deletion
    errata_before = (
        await db_session.execute(
            select(func.count(QuestionErrataReport.id)).where(QuestionErrataReport.user_id == user_id_a)
        )
    ).scalar()
    assert errata_before == 1

    question_id = question.id
    topic_id = topic.id

    # 8. Execute Account Deletion
    del_res = await client.delete("/api/v1/student/account", headers=headers_a)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Expire cached session state to check database truth
    db_session.expire_all()

    # 9. Verify every single student-owned table has zero records remaining for user_id_a
    assert (await db_session.execute(select(func.count(User.id)).where(User.id == user_id_a))).scalar() == 0
    assert (await db_session.execute(select(func.count(UserRole.user_id)).where(UserRole.user_id == user_id_a))).scalar() == 0
    assert (await db_session.execute(select(func.count(StudentProfile.id)).where(StudentProfile.user_id == user_id_a))).scalar() == 0
    if profile_id_a:
        assert (
            await db_session.execute(
                select(func.count(StudentProfileSubject.profile_id)).where(StudentProfileSubject.profile_id == profile_id_a)
            )
        ).scalar() == 0
    assert (await db_session.execute(select(func.count(QuestionErrataReport.id)).where(QuestionErrataReport.user_id == user_id_a))).scalar() == 0
    assert (await db_session.execute(select(func.count(QuestionAttempt.id)).where(QuestionAttempt.user_id == user_id_a))).scalar() == 0
    assert (await db_session.execute(select(func.count(PracticeSession.id)).where(PracticeSession.user_id == user_id_a))).scalar() == 0
    assert (await db_session.execute(select(func.count(LessonProgress.id)).where(LessonProgress.user_id == user_id_a))).scalar() == 0
    assert (await db_session.execute(select(func.count(StudyGoal.id)).where(StudyGoal.user_id == user_id_a))).scalar() == 0
    assert (await db_session.execute(select(func.count(StudyTask.id)).where(StudyTask.user_id == user_id_a))).scalar() == 0
    assert (await db_session.execute(select(func.count(ReviewItem.id)).where(ReviewItem.user_id == user_id_a))).scalar() == 0
    assert (await db_session.execute(select(func.count(ReviewLog.id)).where(ReviewLog.user_id == user_id_a))).scalar() == 0

    # 10. Verify shared question bank and taxonomy items remain completely untouched
    assert (await db_session.execute(select(func.count(Question.id)).where(Question.id == question_id))).scalar() == 1
    assert (await db_session.execute(select(func.count(Topic.id)).where(Topic.id == topic_id))).scalar() == 1


@pytest.mark.asyncio
async def test_account_deletion_cross_student_isolation(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify that deleting Student A does NOT remove or corrupt Student B's records."""
    # Register Student A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": f"iso_a_{uuid.uuid4().hex[:8]}@example.com", "password": "PasswordA123!", "full_name": "Student A"},
    )
    token_a = res_a.json()["access_token"]
    user_id_a = uuid.UUID(res_a.json()["user"]["id"])

    # Register Student B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": f"iso_b_{uuid.uuid4().hex[:8]}@example.com", "password": "PasswordB123!", "full_name": "Student B"},
    )
    token_b = res_b.json()["access_token"]
    user_id_b = uuid.UUID(res_b.json()["user"]["id"])

    question = (await db_session.execute(select(Question).limit(1))).scalar_one()

    # Student A files errata report
    await client.post(
        f"/api/v1/practice/questions/{question.id}/report-errata",
        json={"question_id": str(question.id), "issue_type": "TYPO", "description": "Student A report"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # Student B files errata report
    errata_b_res = await client.post(
        f"/api/v1/practice/questions/{question.id}/report-errata",
        json={"question_id": str(question.id), "issue_type": "WRONG_ANSWER", "description": "Student B report"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    errata_b_id = uuid.UUID(errata_b_res.json()["id"])

    # Student A deletes account
    del_res = await client.delete("/api/v1/student/account", headers={"Authorization": f"Bearer {token_a}"})
    assert del_res.status_code == 200

    db_session.expire_all()

    # Student A records gone
    assert (await db_session.execute(select(func.count(User.id)).where(User.id == user_id_a))).scalar() == 0
    assert (await db_session.execute(select(func.count(QuestionErrataReport.id)).where(QuestionErrataReport.user_id == user_id_a))).scalar() == 0

    # Student B records completely intact
    assert (await db_session.execute(select(func.count(User.id)).where(User.id == user_id_b))).scalar() == 1
    errata_b = (
        await db_session.execute(select(QuestionErrataReport).where(QuestionErrataReport.id == errata_b_id))
    ).scalar_one_or_none()
    assert errata_b is not None
    assert errata_b.user_id == user_id_b
    assert errata_b.description == "Student B report"


@pytest.mark.asyncio
async def test_account_deletion_failure_atomicity_rolls_back(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify that if an unhandled error occurs during deletion, the entire transaction rolls back

    and no partial deletion occurs.
    """
    email = f"rollback_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Rollback Test"},
    )
    token = reg_res.json()["access_token"]
    user_id = uuid.UUID(reg_res.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {token}"}

    question = (await db_session.execute(select(Question).limit(1))).scalar_one()
    await client.post(
        f"/api/v1/practice/questions/{question.id}/report-errata",
        json={"question_id": str(question.id), "issue_type": "TYPO", "description": "Rollback errata"},
        headers=headers,
    )

    # Simulate unexpected database error during delete execution
    with patch("sqlalchemy.ext.asyncio.AsyncSession.delete", side_effect=RuntimeError("Simulated DB Disk Error")):
        del_res = await client.delete("/api/v1/student/account", headers=headers)
        assert del_res.status_code == 500

    db_session.expire_all()

    # Confirm user and errata are NOT partially deleted
    user_after = (await db_session.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    assert user_after is not None
    assert user_after.email == email.lower()

    errata_after = (
        await db_session.execute(select(QuestionErrataReport).where(QuestionErrataReport.user_id == user_id))
    ).scalar_one_or_none()
    assert errata_after is not None


@pytest.mark.asyncio
async def test_authorized_account_deletion_clears_auth_cookie(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify that successful student account deletion instructs the browser to expire the auth cookie."""
    email = f"cookie_del_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Cookie Deletion User"},
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    del_resp = await client.delete("/api/v1/student/account", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "success"

    set_cookie = del_resp.headers.get("set-cookie")
    assert set_cookie is not None
    assert settings.AUTH_COOKIE_NAME in set_cookie
    assert "max-age=0" in set_cookie.lower() or "expires=" in set_cookie.lower()
    assert "path=/" in set_cookie.lower()


@pytest.mark.asyncio
async def test_unauthorized_account_deletion_rejected(client: AsyncClient):
    """Verify that account deletion without valid credentials is rejected without touching cookies."""
    del_resp = await client.delete("/api/v1/student/account")
    assert del_resp.status_code == 401
    set_cookie = del_resp.headers.get("set-cookie")
    if set_cookie:
        assert "max-age=0" not in set_cookie.lower()


@pytest.mark.asyncio
async def test_account_deletion_failure_does_not_clear_auth_cookie(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify that if deletion fails before commit, the auth cookie is not expired."""
    email = f"fail_del_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Failed Deletion User"},
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=RuntimeError("Simulated Commit Failure")):
        del_resp = await client.delete("/api/v1/student/account", headers=headers)
        assert del_resp.status_code == 500

    set_cookie = del_resp.headers.get("set-cookie")
    if set_cookie:
        assert "max-age=0" not in set_cookie.lower()
