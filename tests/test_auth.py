"""Comprehensive Tests for Student Registration, Login, Logout, and Token Verification."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.identity import User


@pytest.mark.asyncio
async def test_student_registration_success(client: AsyncClient, db_session: AsyncSession):
    """Test valid student registration returning JWT token and safe user payload."""
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "SecurePassword123",
        "full_name": "Rohan Gupta",
    }

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Verify token response
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in_minutes"] > 0

    # Verify user object
    user = data["user"]
    assert user["email"] == email.lower()
    assert user["full_name"] == "Rohan Gupta"
    assert "STUDENT" in user["roles"]
    assert user["onboarding_completed"] is False

    # Security check: Password or hash must NEVER be exposed in the response
    assert "password" not in user
    assert "hashed_password" not in user
    assert "SecurePassword123" not in response.text

    # Verify database persistence & bcrypt hashing (never plaintext)
    stmt = select(User).where(User.email == email.lower())
    db_user = (await db_session.execute(stmt)).scalar_one()
    assert db_user.hashed_password != "SecurePassword123"
    assert verify_password("SecurePassword123", db_user.hashed_password) is True


@pytest.mark.asyncio
async def test_registration_duplicate_normalized_email_rejected(client: AsyncClient):
    """Verify that registering with duplicate email (even with different case) is rejected."""
    base_email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": base_email.upper(),
        "password": "SecurePassword123",
        "full_name": "First User",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt duplicate with lowercase
    payload_dup = {
        "email": base_email.lower(),
        "password": "AnotherPassword456",
        "full_name": "Second User",
    }
    res2 = await client.post("/api/v1/auth/register", json=payload_dup)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_registration_validation_errors(client: AsyncClient):
    """Test validation rejection for invalid emails and weak passwords."""
    # Invalid email
    res_email = await client.post(
        "/api/v1/auth/register",
        json={"email": "invalid-email-string", "password": "Pass1234Password", "full_name": "Test"},
    )
    assert res_email.status_code == 422

    # Weak password (missing numbers)
    res_pwd1 = await client.post(
        "/api/v1/auth/register",
        json={"email": "valid1@example.com", "password": "onlylettershere", "full_name": "Test"},
    )
    assert res_pwd1.status_code == 422

    # Short password (< 8 chars)
    res_pwd2 = await client.post(
        "/api/v1/auth/register",
        json={"email": "valid2@example.com", "password": "P123", "full_name": "Test"},
    )
    assert res_pwd2.status_code == 422


@pytest.mark.asyncio
async def test_login_successful(client: AsyncClient):
    """Verify successful login with valid credentials."""
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "ValidPassword99", "full_name": "Login Tester"},
    )

    # Login with case insensitivity
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email.upper(), "password": "ValidPassword99"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == email.lower()


@pytest.mark.asyncio
async def test_login_invalid_credentials_rejected(client: AsyncClient):
    """Verify login failure for incorrect password and unknown account."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "CorrectPassword1", "full_name": "Tester"},
    )

    # Wrong password
    res_bad_pwd = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword2"},
    )
    assert res_bad_pwd.status_code == 401
    assert "invalid email or password" in res_bad_pwd.json()["detail"].lower()

    # Non-existent account
    res_unknown = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody_exists_here_999@example.com", "password": "AnyPassword123"},
    )
    assert res_unknown.status_code == 401


@pytest.mark.asyncio
async def test_authenticated_me_endpoint(client: AsyncClient):
    """Verify GET /api/v1/auth/me returns current user when authenticated, rejects when unauthenticated."""
    # 1. Unauthenticated request rejected with 401
    unauth_res = await client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401

    # 2. Register and test with Bearer header
    email = f"me_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password12345", "full_name": "Priya Patel"},
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    auth_res = await client.get("/api/v1/auth/me", headers=headers)
    assert auth_res.status_code == 200
    user_data = auth_res.json()
    assert user_data["email"] == email.lower()
    assert user_data["full_name"] == "Priya Patel"

    # 3. Request with invalid token rejected with 401
    bad_token_res = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer completely-invalid-fake-token"}
    )
    assert bad_token_res.status_code == 401


@pytest.mark.asyncio
async def test_logout_endpoint(client: AsyncClient):
    """Verify POST /api/v1/auth/logout clears session cookies."""
    res = await client.post("/api/v1/auth/logout")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
