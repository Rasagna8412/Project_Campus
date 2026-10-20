"""Unit and Integration Tests for Safe Administrative Password Reset Utility."""

import uuid
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.identity import Role, User, UserRole
from scripts.reset_password import get_user_by_email, reset_user_password


@pytest.mark.asyncio
async def test_admin_password_reset_success(client: AsyncClient, db_session: AsyncSession):
    """Verify that an administrator can successfully reset a student's password."""
    # 1. Create a student account
    email = f"reset_student_{uuid.uuid4().hex[:8]}@example.com"
    old_password = "OriginalPassword123"
    new_password = "BrandNewSecurePassword2026!"

    user = User(
        email=email,
        hashed_password=get_password_hash(old_password),
        full_name="Reset Target Student",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    role_stmt = select(Role).where(Role.name == "STUDENT")
    student_role = (await db_session.execute(role_stmt)).scalar_one_or_none()
    if not student_role:
        student_role = Role(name="STUDENT", description="Student Learner")
        db_session.add(student_role)
        await db_session.flush()

    db_session.add(UserRole(user_id=user.id, role_id=student_role.id))
    await db_session.commit()

    # 2. Confirm old password works for login before reset
    login_old = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_password},
    )
    assert login_old.status_code == 200

    # 3. Execute password reset utility
    success, msg = await reset_user_password(email, new_password, session=db_session)
    assert success is True
    assert "successfully reset" in msg.lower()

    # 4. Confirm old password now fails with 401 Unauthorized
    login_old_after = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_password},
    )
    assert login_old_after.status_code == 401

    # 5. Confirm new password logs in successfully
    login_new = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": new_password},
    )
    assert login_new.status_code == 200
    assert login_new.json()["user"]["email"] == email


@pytest.mark.asyncio
async def test_admin_password_reset_nonexistent_user(db_session: AsyncSession):
    """Verify safe error response when attempting to reset a nonexistent user."""
    fake_email = f"ghost_{uuid.uuid4().hex[:8]}@example.com"
    success, msg = await reset_user_password(fake_email, "SomeValidPassword123", session=db_session)
    assert success is False
    assert "not found" in msg.lower()


@pytest.mark.asyncio
async def test_admin_password_reset_validation():
    """Verify input validation for minimum length and empty email."""
    # Short password
    success, msg = await reset_user_password("user@example.com", "short")
    assert success is False
    assert "at least 8 characters" in msg

    # Empty email
    success, msg = await reset_user_password("", "ValidPassword123")
    assert success is False
    assert "cannot be empty" in msg


@pytest.mark.asyncio
async def test_admin_password_reset_transaction_rollback(db_session: AsyncSession):
    """Verify that database transaction rolls back if an error occurs during commit."""
    email = f"rollback_{uuid.uuid4().hex[:8]}@example.com"
    original_password = "KeepThisPassword123"

    user = User(
        email=email,
        hashed_password=get_password_hash(original_password),
        full_name="Rollback Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Mock session.commit to simulate a database failure
    with patch.object(db_session, "commit", side_effect=Exception("Simulated DB connection failure")):
        success, msg = await reset_user_password(email, "NewAttemptedPassword123", session=db_session)
        assert success is False
        assert "Database transaction failed" in msg

    # Reload user and verify old password hash remained intact
    await db_session.rollback()
    reloaded_user = await get_user_by_email(email, db_session)
    assert reloaded_user is not None
    assert verify_password(original_password, reloaded_user.hashed_password) is True
