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


@pytest.mark.asyncio
async def test_student_cannot_modify_other_student_profile(client: AsyncClient):
    """Verify that Student A cannot modify Student B's profile through any endpoint."""
    # Register Student A
    email_a = f"mod_a_{uuid.uuid4().hex[:8]}@example.com"
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "PasswordA123", "full_name": "Student A"},
    )
    token_a = res_a.json()["access_token"]

    # Register Student B
    email_b = f"mod_b_{uuid.uuid4().hex[:8]}@example.com"
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "PasswordB123", "full_name": "Student B"},
    )
    token_b = res_b.json()["access_token"]
    user_id_b = res_b.json()["user"]["id"]

    # Student B sets goal to 180 minutes
    await client.put(
        "/api/v1/student/profile",
        json={"daily_study_goal_minutes": 180},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # Student A attempts to modify profile, passing Student B's user_id in payload or query
    await client.put(
        f"/api/v1/student/profile?user_id={user_id_b}",
        json={"daily_study_goal_minutes": 45, "user_id": user_id_b},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # Verify Student B's goal is still 180 (unmodified!)
    prof_b = await client.get(
        "/api/v1/student/profile",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert prof_b.json()["daily_study_goal_minutes"] == 180

    # Verify Student A's goal was the one updated to 45
    prof_a = await client.get(
        "/api/v1/student/profile",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert prof_a.json()["daily_study_goal_minutes"] == 45


@pytest.mark.asyncio
async def test_student_cannot_delete_other_student_account(client: AsyncClient):
    """Verify that Student A invoking account deletion cannot delete Student B's account."""
    # Register Student A
    email_a = f"del_a_{uuid.uuid4().hex[:8]}@example.com"
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "PasswordA123", "full_name": "Deleter A"},
    )
    token_a = res_a.json()["access_token"]

    # Register Student B
    email_b = f"del_b_{uuid.uuid4().hex[:8]}@example.com"
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "PasswordB123", "full_name": "Victim B"},
    )
    token_b = res_b.json()["access_token"]
    user_id_b = res_b.json()["user"]["id"]

    # Student A sends delete request with Student B's ID in query and headers
    del_res = await client.delete(
        f"/api/v1/student/account?user_id={user_id_b}",
        headers={"Authorization": f"Bearer {token_a}", "X-Target-User": user_id_b},
    )
    assert del_res.status_code == 200

    # Student A's account is deleted
    me_a = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert me_a.status_code == 401

    # Student B's account is completely intact
    me_b = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    assert me_b.status_code == 200
    assert me_b.json()["email"] == email_b.lower()


@pytest.mark.asyncio
async def test_role_guard_enforcement(client: AsyncClient, db_session: AsyncSession):
    """Verify role guards correctly reject unauthorized roles and permit matching roles."""
    from sqlalchemy import select
    from app.core.security import create_access_token, get_password_hash
    from app.models.identity import Role, User, UserRole

    # 1. Create a user with ONLY the EDUCATOR role
    role_stmt = select(Role).where(Role.name == "EDUCATOR")
    edu_role = (await db_session.execute(role_stmt)).scalar_one_or_none()
    if not edu_role:
        edu_role = Role(name="EDUCATOR", description="Educator")
        db_session.add(edu_role)
        await db_session.flush()

    edu_user = User(
        email=f"educator_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("Password12345"),
        full_name="Prof. Sharma",
        is_active=True,
    )
    db_session.add(edu_user)
    await db_session.flush()

    db_session.add(UserRole(user_id=edu_user.id, role_id=edu_role.id))
    await db_session.commit()

    edu_token = create_access_token(
        {"sub": str(edu_user.id), "email": edu_user.email, "roles": ["EDUCATOR"]}
    )

    # 2. Educator attempts to access student-restricted endpoints -> 403 Forbidden
    res_prof = await client.get(
        "/api/v1/student/profile",
        headers={"Authorization": f"Bearer {edu_token}"},
    )
    assert res_prof.status_code == 403
    assert "operation requires student privilege" in res_prof.json()["detail"].lower()

    # 3. Educator can access general authenticated endpoint /auth/me -> 200 OK
    res_me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {edu_token}"},
    )
    assert res_me.status_code == 200
    assert "EDUCATOR" in res_me.json()["roles"]


@pytest.mark.asyncio
async def test_account_deletion_cleanses_database(client: AsyncClient, db_session: AsyncSession):
    """Verify that account deletion removes all associated user and profile records from the database."""
    from sqlalchemy import select
    from app.models.identity import StudentProfile, StudentProfileSubject, User

    email = f"cleanse_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password12345", "full_name": "Cleanse Tester"},
    )
    token = reg_res.json()["access_token"]
    user_id = uuid.UUID(reg_res.json()["user"]["id"])

    # Verify user exists in database before deletion
    user_stmt = select(User).where(User.id == user_id)
    user_before = (await db_session.execute(user_stmt)).scalar_one_or_none()
    assert user_before is not None

    prof_stmt = select(StudentProfile).where(StudentProfile.user_id == user_id)
    prof_before = (await db_session.execute(prof_stmt)).scalar_one_or_none()
    assert prof_before is not None
    profile_id = prof_before.id

    # Execute deletion
    del_res = await client.delete(
        "/api/v1/student/account",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 200

    # Verify user, student_profile, and any subject records are completely removed
    user_after = (await db_session.execute(user_stmt)).scalar_one_or_none()
    assert user_after is None

    prof_after = (await db_session.execute(prof_stmt)).scalar_one_or_none()
    assert prof_after is None

    subj_stmt = select(StudentProfileSubject).where(StudentProfileSubject.profile_id == profile_id)
    subj_after = (await db_session.execute(subj_stmt)).scalars().all()
    assert len(subj_after) == 0

