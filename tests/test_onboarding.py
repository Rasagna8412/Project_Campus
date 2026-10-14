"""Tests for Student Onboarding, Curriculum Selection, and Profile Persistence."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_curricula_taxonomy(client: AsyncClient):
    """Verify that curricula, grades, and subjects are accessible."""
    response = await client.get("/api/v1/curricula/")
    assert response.status_code == 200
    curricula = response.json()
    assert len(curricula) >= 3

    cbse = next((c for c in curricula if c["code"] == "CBSE"), None)
    assert cbse is not None
    assert len(cbse["grades"]) >= 2

    class_11 = next((g for g in cbse["grades"] if g["code"] == "CLASS_11"), None)
    assert class_11 is not None
    assert len(class_11["subjects"]) >= 3


@pytest.mark.asyncio
async def test_student_onboarding_lifecycle_and_resumption(client: AsyncClient):
    """Test full student onboarding flow: draft save, resumption, and completion."""
    # 1. Register student
    email = f"onboard_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "OnboardPass123", "full_name": "Aarav Sharma"},
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch available curriculum data
    curricula = (await client.get("/api/v1/curricula/")).json()
    cbse = next(c for c in curricula if c["code"] == "CBSE")
    grade_12 = next(g for g in cbse["grades"] if g["code"] == "CLASS_12")
    subject_ids = [s["id"] for s in grade_12["subjects"][:3]]  # Pick first 3 subjects

    # 2. Save partial / draft onboarding (complete = False)
    draft_payload = {
        "target_curriculum_id": cbse["id"],
        "grade_stage_id": grade_12["id"],
        "target_exam_year": 2027,
        "selected_subject_ids": subject_ids,
        "daily_study_goal_minutes": 150,
        "preferred_language": "en",
        "complete": False,  # Saving draft progress
    }
    draft_res = await client.put(
        "/api/v1/student/onboarding", json=draft_payload, headers=headers
    )
    assert draft_res.status_code == 200
    draft_data = draft_res.json()
    assert draft_data["onboarding_completed"] is False
    assert draft_data["target_curriculum_name"] == cbse["name"]
    assert len(draft_data["selected_subjects"]) == 3

    # 3. Simulate resuming onboarding: fetch current profile
    profile_res = await client.get("/api/v1/student/profile", headers=headers)
    assert profile_res.status_code == 200
    resumed_data = profile_res.json()
    assert resumed_data["onboarding_completed"] is False
    assert resumed_data["target_exam_year"] == 2027
    assert resumed_data["daily_study_goal_minutes"] == 150

    # 4. Finalize onboarding (complete = True)
    final_payload = {**draft_payload, "complete": True}
    final_res = await client.put(
        "/api/v1/student/onboarding", json=final_payload, headers=headers
    )
    assert final_res.status_code == 200
    final_data = final_res.json()
    assert final_data["onboarding_completed"] is True


@pytest.mark.asyncio
async def test_onboarding_rejects_incompatible_selections(client: AsyncClient):
    """Verify validation when selecting invalid curriculum or mismatched grades."""
    email = f"invalid_onboard_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password12345", "full_name": "Test User"},
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    curricula = (await client.get("/api/v1/curricula/")).json()
    cbse = next(c for c in curricula if c["code"] == "CBSE")
    neet = next(c for c in curricula if c["code"] == "NEET")
    neet_grade = neet["grades"][0]

    # Attempting to assign a NEET grade to CBSE curriculum board
    mismatched_payload = {
        "target_curriculum_id": cbse["id"],
        "grade_stage_id": neet_grade["id"],  # Incompatible!
        "target_exam_year": 2026,
        "selected_subject_ids": [s["id"] for s in neet_grade["subjects"]],
        "daily_study_goal_minutes": 120,
        "complete": True,
    }
    res = await client.put(
        "/api/v1/student/onboarding", json=mismatched_payload, headers=headers
    )
    assert res.status_code == 400
    assert "does not belong to the chosen curriculum" in res.json()["detail"]


@pytest.mark.asyncio
async def test_partial_profile_update(client: AsyncClient):
    """Verify updating study goal minutes and exam year."""
    email = f"update_prof_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password12345", "full_name": "Kavita Rao"},
    )
    headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    # Partial update
    update_res = await client.put(
        "/api/v1/student/profile",
        json={"daily_study_goal_minutes": 180, "target_exam_year": 2028},
        headers=headers,
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["daily_study_goal_minutes"] == 180
    assert data["target_exam_year"] == 2028
