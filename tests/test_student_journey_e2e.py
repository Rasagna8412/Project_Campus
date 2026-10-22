"""Comprehensive End-to-End Student Journey Integration Tests.

Validates the complete chronological student lifecycle from initial registration
through academic onboarding, curriculum discovery, lesson study, deliberate practice,
analytics, goal setting, daily planning, roadmap tracking, and DPDP account erasure.
Also verifies security boundaries, IDOR ownership isolation, token lifecycle,
and empty/invalid edge cases.
"""

from datetime import date, timedelta
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.content import LessonProgressStatus
from app.models.identity import User
from app.models.planner import TaskStatus


@pytest.mark.asyncio
async def test_complete_student_lifecycle_e2e(client: AsyncClient, db_session):
    """Verify all 10 stages of the student learning journey in a continuous session."""
    
    # -------------------------------------------------------------------------
    # STAGE 1: Registration and Authentication
    # -------------------------------------------------------------------------
    student_email = f"e2e_student_{uuid.uuid4().hex[:8]}@example.com"
    student_password = "SecureStudentPass2026!"
    student_name = "Ananya Patel"

    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": student_email,
            "password": student_password,
            "full_name": student_name,
        },
    )
    assert reg_resp.status_code == 201, reg_resp.text
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == student_email
    assert reg_data["user"]["roles"] == ["STUDENT"]
    token = reg_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Verify /auth/me returns student identity
    me_resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == student_email

    # -------------------------------------------------------------------------
    # STAGE 2: Curriculum Exploration and Academic Onboarding
    # -------------------------------------------------------------------------
    # Query available curricula taxonomy
    curricula_resp = await client.get("/api/v1/curricula/")
    assert curricula_resp.status_code == 200
    curricula = curricula_resp.json()
    assert len(curricula) > 0

    cbse = next((c for c in curricula if c["code"] == "CBSE"), curricula[0])
    grade_12 = next(
        (g for g in cbse["grades"] if g["code"] == "CLASS_12"),
        cbse["grades"][0],
    )
    assert len(grade_12["subjects"]) > 0
    enrolled_subject_ids = [s["id"] for s in grade_12["subjects"][:2]]

    # Complete academic onboarding
    onboard_payload = {
        "target_curriculum_id": cbse["id"],
        "grade_stage_id": grade_12["id"],
        "target_exam_year": 2027,
        "selected_subject_ids": enrolled_subject_ids,
        "daily_study_goal_minutes": 90,
        "preferred_language": "en",
        "complete": True,
    }
    onboard_resp = await client.put(
        "/api/v1/student/onboarding",
        json=onboard_payload,
        headers=auth_headers,
    )
    assert onboard_resp.status_code == 200, onboard_resp.text
    profile_data = onboard_resp.json()
    assert profile_data["onboarding_completed"] is True
    assert len(profile_data["selected_subjects"]) == 2

    # -------------------------------------------------------------------------
    # STAGE 3: Access Published Lessons and Sections
    # -------------------------------------------------------------------------
    target_subject_id = enrolled_subject_ids[0]
    chapters_resp = await client.get(
        f"/api/v1/curricula/subjects/{target_subject_id}/chapters",
        headers=auth_headers,
    )
    assert chapters_resp.status_code == 200
    chapters = chapters_resp.json()
    assert len(chapters) > 0

    target_chapter = chapters[0]
    assert len(target_chapter["topics"]) > 0
    target_topic = target_chapter["topics"][0]

    # Fetch published topic lessons (drafts must never be exposed)
    lessons_resp = await client.get(
        f"/api/v1/curricula/topics/{target_topic['id']}/lessons",
        headers=auth_headers,
    )
    assert lessons_resp.status_code == 200
    lessons = lessons_resp.json()
    assert len(lessons) > 0
    target_lesson = lessons[0]

    # Fetch full lesson detail with structured sections
    lesson_detail_resp = await client.get(
        f"/api/v1/curricula/lessons/{target_lesson['id']}",
        headers=auth_headers,
    )
    assert lesson_detail_resp.status_code == 200
    lesson_detail = lesson_detail_resp.json()
    assert lesson_detail["id"] == target_lesson["id"]
    assert "sections" in lesson_detail
    assert len(lesson_detail["sections"]) > 0

    # -------------------------------------------------------------------------
    # STAGE 4: Lesson Progress Tracking (Start & Complete)
    # -------------------------------------------------------------------------
    # Start lesson
    start_resp = await client.post(
        f"/api/v1/student/progress/lessons/{target_lesson['id']}/start",
        headers=auth_headers,
    )
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "IN_PROGRESS"

    # Mark lesson completed
    complete_resp = await client.post(
        f"/api/v1/student/progress/lessons/{target_lesson['id']}/complete",
        headers=auth_headers,
    )
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "COMPLETED"

    # -------------------------------------------------------------------------
    # STAGE 5: Practice Session, Question Submission & Errata Reporting
    # -------------------------------------------------------------------------
    # Start a practice session for target topic
    session_resp = await client.post(
        "/api/v1/practice/sessions",
        json={"topic_id": target_topic["id"]},
        headers=auth_headers,
    )
    assert session_resp.status_code in (200, 201), session_resp.text
    session_data = session_resp.json()
    assert "id" in session_data
    assert len(session_data["questions"]) > 0
    session_id = session_data["id"]

    target_q = session_data["questions"][0]
    q_id = target_q["id"]

    # Submit an answer attempt
    submit_payload = {
        "question_id": q_id,
        "session_id": session_id,
        "time_spent_seconds": 45,
    }
    if target_q["question_type"] in ("SINGLE_CHOICE", "MULTIPLE_CHOICE"):
        submit_payload["selected_options"] = [target_q["options"][0]["option_key"]]
    elif target_q["question_type"] == "NUMERICAL":
        submit_payload["numerical_value"] = 5.0
    else:
        submit_payload["integer_value"] = 10

    eval_resp = await client.post(
        "/api/v1/practice/submit",
        json=submit_payload,
        headers=auth_headers,
    )
    assert eval_resp.status_code == 200
    eval_result = eval_resp.json()
    assert "is_correct" in eval_result
    assert "explanation_latex" in eval_result

    # Submit errata report on question
    errata_resp = await client.post(
        f"/api/v1/practice/questions/{q_id}/report-errata",
        json={
            "question_id": q_id,
            "issue_type": "TYPO_OR_GRAMMAR",
            "description": "Minor phrasing review suggested for clarity in formula context.",
        },
        headers=auth_headers,
    )
    assert errata_resp.status_code == 201

    # -------------------------------------------------------------------------
    # STAGE 6: Student Analytics & Diagnostic Dashboard
    # -------------------------------------------------------------------------
    dash_resp = await client.get(
        "/api/v1/student/analytics/dashboard",
        headers=auth_headers,
    )
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert "lessons_completed_count" in dash_data
    assert dash_data["lessons_completed_count"] >= 1
    assert "total_questions_answered" in dash_data
    assert dash_data["total_questions_answered"] >= 1

    # Topic performance breakdown
    topics_resp = await client.get(
        "/api/v1/student/analytics/topics",
        headers=auth_headers,
    )
    assert topics_resp.status_code == 200
    topics_breakdown = topics_resp.json()
    assert isinstance(topics_breakdown, list)

    # Recommendations
    recs_resp = await client.get(
        "/api/v1/student/analytics/recommendations",
        headers=auth_headers,
    )
    assert recs_resp.status_code == 200
    recs = recs_resp.json()
    assert isinstance(recs, list)

    # -------------------------------------------------------------------------
    # STAGE 7: Study Goal Management
    # -------------------------------------------------------------------------
    goal_resp = await client.get("/api/v1/planner/goal", headers=auth_headers)
    assert goal_resp.status_code == 200
    active_goal = goal_resp.json()
    assert active_goal["daily_study_minutes"] >= 15

    # Update study goal parameters
    update_goal_resp = await client.post(
        "/api/v1/planner/goal",
        json={
            "title": "Intensive Board & JEE Preparation",
            "daily_study_minutes": 150,
            "target_date": (date.today() + timedelta(days=180)).isoformat(),
            "preferred_days": ["MON", "TUE", "WED", "THU", "FRI", "SAT"],
        },
        headers=auth_headers,
    )
    assert update_goal_resp.status_code == 200
    assert update_goal_resp.json()["daily_study_minutes"] == 150

    # -------------------------------------------------------------------------
    # STAGE 8: Planner Task Generation, Completion & Rescheduling
    # -------------------------------------------------------------------------
    # Generate daily tasks
    gen_resp = await client.post(
        "/api/v1/planner/daily/generate",
        headers=auth_headers,
    )
    assert gen_resp.status_code == 200
    daily_plan = gen_resp.json()
    assert "tasks" in daily_plan
    assert len(daily_plan["tasks"]) <= 4  # Strict 4-task ceiling

    if daily_plan["tasks"]:
        first_task = daily_plan["tasks"][0]
        # Complete first task
        comp_task_resp = await client.patch(
            f"/api/v1/planner/tasks/{first_task['id']}/complete",
            json={"is_completed": True},
            headers=auth_headers,
        )
        assert comp_task_resp.status_code == 200
        assert comp_task_resp.json()["status"] == "COMPLETED"

        # If a second task exists, reschedule it to tomorrow
        if len(daily_plan["tasks"]) > 1:
            second_task = daily_plan["tasks"][1]
            tomorrow = (date.today() + timedelta(days=1)).isoformat()
            resched_resp = await client.patch(
                f"/api/v1/planner/tasks/{second_task['id']}/reschedule",
                json={"new_date": tomorrow},
                headers=auth_headers,
            )
            assert resched_resp.status_code == 200
            assert resched_resp.json()["scheduled_date"] == tomorrow

    # -------------------------------------------------------------------------
    # STAGE 9: Curriculum Roadmap Navigation
    # -------------------------------------------------------------------------
    roadmap_resp = await client.get("/api/v1/planner/roadmap", headers=auth_headers)
    assert roadmap_resp.status_code == 200
    roadmap_data = roadmap_resp.json()
    assert "subjects" in roadmap_data
    assert len(roadmap_data["subjects"]) >= 1

    # -------------------------------------------------------------------------
    # STAGE 10: DPDP Account Deletion
    # -------------------------------------------------------------------------
    delete_resp = await client.delete(
        "/api/v1/student/account",
        headers=auth_headers,
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "success"

    # Verify user token is rejected following deletion
    revoked_resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert revoked_resp.status_code == 401


@pytest.mark.asyncio
async def test_student_journey_ownership_and_security_boundaries(client: AsyncClient):
    """Verify IDOR ownership isolation, invalid tokens, and cross-student boundaries."""
    
    # Register Student A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"owner_a_{uuid.uuid4().hex[:8]}@example.com",
            "password": "PasswordA123!",
            "full_name": "Student A",
        },
    )
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register Student B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"owner_b_{uuid.uuid4().hex[:8]}@example.com",
            "password": "PasswordB123!",
            "full_name": "Student B",
        },
    )
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Student A onboards and creates a practice session
    curricula = (await client.get("/api/v1/curricula/")).json()
    cbse = next((c for c in curricula if c["code"] == "CBSE"), curricula[0])
    grade = next((g for g in cbse["grades"] if g["code"] == "CLASS_12"), cbse["grades"][0])
    subject = grade["subjects"][0]
    
    await client.put(
        "/api/v1/student/onboarding",
        json={
            "target_curriculum_id": cbse["id"],
            "grade_stage_id": grade["id"],
            "selected_subject_ids": [subject["id"]],
            "complete": True,
        },
        headers=headers_a,
    )

    chapters = (await client.get(f"/api/v1/curricula/subjects/{subject['id']}/chapters")).json()
    topic = chapters[0]["topics"][0]
    session_a = (await client.post(
        "/api/v1/practice/sessions",
        json={"topic_id": topic["id"]},
        headers=headers_a,
    )).json()
    session_id_a = session_a["id"]

    # Student B attempts to access Student A's practice session -> must 404
    cross_session_resp = await client.get(
        f"/api/v1/practice/sessions/{session_id_a}",
        headers=headers_b,
    )
    assert cross_session_resp.status_code == 404

    # Student B attempts to submit answer to Student A's practice session -> must 404
    cross_submit_resp = await client.post(
        "/api/v1/practice/submit",
        json={
            "question_id": session_a["questions"][0]["id"],
            "session_id": session_id_a,
            "selected_options": ["dummy-opt"],
            "time_spent_seconds": 10,
        },
        headers=headers_b,
    )
    assert cross_submit_resp.status_code == 404

    # Invalid / Malformed / Expired Tokens
    client.cookies.clear()
    bad_token_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer malformed.invalid.token"},
    )
    assert bad_token_resp.status_code == 401

    empty_bearer_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer "},
    )
    assert empty_bearer_resp.status_code == 401


@pytest.mark.asyncio
async def test_student_journey_empty_and_invalid_states(client: AsyncClient):
    """Verify empty state recommendations, invalid task reschedules, and validation errors."""
    
    # Register student without onboarding
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"empty_state_{uuid.uuid4().hex[:8]}@example.com",
            "password": "PasswordEmpty123!",
            "full_name": "Empty Student",
        },
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify recommendations for unenrolled student return empty list without error
    recs_resp = await client.get(
        "/api/v1/student/analytics/recommendations",
        headers=headers,
    )
    assert recs_resp.status_code == 200
    assert recs_resp.json() == []

    # Onboard student and generate tasks to test reschedule validation
    curricula = (await client.get("/api/v1/curricula/")).json()
    cbse = next((c for c in curricula if c["code"] == "CBSE"), curricula[0])
    grade = next((g for g in cbse["grades"] if g["code"] == "CLASS_12"), cbse["grades"][0])
    subject = grade["subjects"][0]
    
    await client.put(
        "/api/v1/student/onboarding",
        json={
            "target_curriculum_id": cbse["id"],
            "grade_stage_id": grade["id"],
            "selected_subject_ids": [subject["id"]],
            "complete": True,
        },
        headers=headers,
    )

    plan = (await client.post("/api/v1/planner/daily/generate", headers=headers)).json()
    if plan.get("tasks"):
        task = plan["tasks"][0]
        # Attempt to reschedule to the past -> must return 400
        past_date = (date.today() - timedelta(days=2)).isoformat()
        resched_past_resp = await client.patch(
            f"/api/v1/planner/tasks/{task['id']}/reschedule",
            json={"new_date": past_date},
            headers=headers,
        )
        assert resched_past_resp.status_code == 400
        assert "past" in resched_past_resp.json()["detail"].lower()

        # Complete task and then attempt to reschedule completed task -> must return 400
        await client.patch(
            f"/api/v1/planner/tasks/{task['id']}/complete",
            json={"is_completed": True},
            headers=headers,
        )
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        resched_completed_resp = await client.patch(
            f"/api/v1/planner/tasks/{task['id']}/reschedule",
            json={"new_date": tomorrow},
            headers=headers,
        )
        assert resched_completed_resp.status_code == 400
        assert "completed" in resched_completed_resp.json()["detail"].lower()
