"""Tests for Student Data Isolation, IDOR Defense, and Account Erasure."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_student_data_isolation(client: AsyncClient):
    """Verify that each student accesses exclusively their own isolated profile."""
    # 1. Register Student A
    email_a = f"student_a_{uuid.uuid4().hex[:8]}@example.com"
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "PasswordA123", "full_name": "Student A"},
    )
    token_a = res_a.json()["access_token"]
    user_id_a = res_a.json()["user"]["id"]

    # 2. Register Student B
    email_b = f"student_b_{uuid.uuid4().hex[:8]}@example.com"
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "PasswordB123", "full_name": "Student B"},
    )
    token_b = res_b.json()["access_token"]
    user_id_b = res_b.json()["user"]["id"]

    # 3. Request profile with Token A
    prof_a = await client.get(
        "/api/v1/student/profile", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert prof_a.status_code == 200
    assert prof_a.json()["user_id"] == user_id_a
    assert prof_a.json()["full_name"] == "Student A"

    # 4. Request profile with Token B
    prof_b = await client.get(
        "/api/v1/student/profile", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert prof_b.status_code == 200
    assert prof_b.json()["user_id"] == user_id_b
    assert prof_b.json()["full_name"] == "Student B"

    # 5. IDOR Defense: Passing foreign user_id in query or header cannot leak Student B's data to Student A
    idor_attempt = await client.get(
        f"/api/v1/student/profile?user_id={user_id_b}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert idor_attempt.status_code == 200
    assert idor_attempt.json()["user_id"] == user_id_a  # Still resolves to Student A!


@pytest.mark.asyncio
async def test_unauthenticated_access_rejected(client: AsyncClient):
    """Verify that protected student endpoints reject requests without valid credentials."""
    # Profile
    res_prof = await client.get("/api/v1/student/profile")
    assert res_prof.status_code == 401

    # Onboarding
    res_onboard = await client.put(
        "/api/v1/student/onboarding",
        json={
            "target_curriculum_id": str(uuid.uuid4()),
            "grade_stage_id": str(uuid.uuid4()),
            "selected_subject_ids": [str(uuid.uuid4())],
        },
    )
    assert res_onboard.status_code == 401


@pytest.mark.asyncio
async def test_account_erasure_dpdp_compliance(client: AsyncClient):
    """Verify self-serve permanent account deletion (right to erasure)."""
    email = f"delete_me_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "DeleteMePassword1", "full_name": "Delete Tester"},
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Delete account
    del_res = await client.delete("/api/v1/student/account", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Subsequent access with same token is revoked/rejected
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 401
