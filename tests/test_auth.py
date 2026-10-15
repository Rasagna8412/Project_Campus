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
    # Verify Set-Cookie header contains instructions to clear the auth cookie
    set_cookie = res.headers.get("set-cookie", "")
    assert "campus_access_token=" in set_cookie
    assert "max-age=0" in set_cookie.lower() or "expires=" in set_cookie.lower()


@pytest.mark.asyncio
async def test_expired_jwt_rejected(client: AsyncClient, db_session: AsyncSession):
    """Verify that an expired JWT is rejected with 401 Unauthorized."""
    from datetime import timedelta
    from app.core.security import create_access_token

    email = f"expired_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password12345", "full_name": "Expired Test"},
    )
    user_id = reg_res.json()["user"]["id"]

    # Create expired token (10 minutes in the past)
    expired_token = create_access_token(
        {"sub": str(user_id), "email": email, "roles": ["STUDENT"]},
        expires_delta=timedelta(minutes=-10),
    )

    res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401
    assert "could not validate credentials" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_tampered_jwt_rejected(client: AsyncClient):
    """Verify that a tampered JWT or invalid signature is rejected with 401."""
    import jwt

    email = f"tamper_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password12345", "full_name": "Tamper Test"},
    )
    valid_token = reg_res.json()["access_token"]

    # Tamper with the token signature
    parts = valid_token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.tampered_signature_value"

    res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert res.status_code == 401

    # Token signed with completely different secret key
    fake_token = jwt.encode(
        {"sub": str(uuid.uuid4()), "email": email, "roles": ["STUDENT"]},
        "wrong-unauthorized-secret-key-1234567890",
        algorithm="HS256",
    )
    res_fake = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {fake_token}"},
    )
    assert res_fake.status_code == 401


@pytest.mark.asyncio
async def test_inactive_user_login_rejected(client: AsyncClient, db_session: AsyncSession):
    """Verify that an inactive/deactivated user account cannot log in."""
    email = f"inactive_login_{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password12345", "full_name": "Inactive User"},
    )

    # Deactivate account in database
    stmt = select(User).where(User.email == email.lower())
    user = (await db_session.execute(stmt)).scalar_one()
    user.is_active = False
    await db_session.commit()

    # Attempt login
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password12345"},
    )
    assert res.status_code == 403
    assert "deactivated" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_inactive_user_token_access_rejected(client: AsyncClient, db_session: AsyncSession):
    """Verify that a token belonging to a deactivated user is rejected on protected routes."""
    email = f"inactive_token_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password12345", "full_name": "Active Then Inactive"},
    )
    token = reg_res.json()["access_token"]
    user_id = reg_res.json()["user"]["id"]

    # Verify active access works
    auth_res = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert auth_res.status_code == 200

    # Deactivate user in database
    stmt = select(User).where(User.id == uuid.UUID(user_id))
    user = (await db_session.execute(stmt)).scalar_one()
    user.is_active = False
    await db_session.commit()

    # Subsequent access with same token must be rejected with 403 Forbidden
    blocked_res = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert blocked_res.status_code == 403
    assert "inactive" in blocked_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_logout_cookie_clearing_and_token_reuse(client: AsyncClient):
    """Verify logout clears cookie, but verify that stateless bearer token remains valid until expiry."""
    email = f"reuse_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password12345", "full_name": "Reuse Tester"},
    )
    token = reg_res.json()["access_token"]

    # Call logout
    logout_res = await client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200

    # Cookie was instructed to clear
    set_cookie = logout_res.headers.get("set-cookie", "")
    assert "campus_access_token=" in set_cookie

    # Stateless JWT: The bearer token itself still passes signature verification
    # This documents the current architectural behavior: without a server-side denylist,
    # the client-side token discard is the primary revocation mechanism in development.
    reuse_res = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert reuse_res.status_code == 200


@pytest.mark.asyncio
async def test_registration_rate_limiting(client: AsyncClient):
    """Verify that exceeding maximum registration attempts from an IP triggers 429 Too Many Requests."""
    for i in range(5):
        unique_email = f"spam_reg_{i}_{uuid.uuid4().hex[:6]}@example.com"
        res = await client.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "password": "Password12345", "full_name": f"Spam {i}"},
        )
        assert res.status_code == 201

    # 6th attempt must be blocked by rate limiter
    blocked_res = await client.post(
        "/api/v1/auth/register",
        json={"email": f"blocked_{uuid.uuid4().hex[:6]}@example.com", "password": "Password12345", "full_name": "Blocked"},
    )
    assert blocked_res.status_code == 429
    assert "too many registration attempts" in blocked_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_rate_limiting(client: AsyncClient):
    """Verify that repeated failed logins for the same account/IP trigger 429 Too Many Requests."""
    target_email = f"target_{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": target_email, "password": "CorrectPassword1", "full_name": "Target User"},
    )

    # 5 failed login attempts
    for _ in range(5):
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": target_email, "password": "WrongPasswordX"},
        )
        assert res.status_code == 401

    # 6th attempt triggers 429 Too Many Requests
    blocked_res = await client.post(
        "/api/v1/auth/login",
        json={"email": target_email, "password": "WrongPasswordX"},
    )
    assert blocked_res.status_code == 429
    assert "too many failed login attempts" in blocked_res.json()["detail"].lower()

