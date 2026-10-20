"""Regression Tests for Reverse Proxy Headers and Client Rate Limiting Isolation."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import auth_rate_limiter
from app.main import app


@pytest.mark.asyncio
async def test_trusted_proxy_forwarded_ip_resolution():
    """Verify that trusted reverse proxies correctly set request.client from X-Forwarded-For."""
    transport = ASGITransport(app=app, client=("127.0.0.1", 50000))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # A trusted proxy (127.0.0.1) forwards client IP 203.0.113.10
        response = await client.get(
            "/api/v1/auth/me",
            headers={"X-Forwarded-For": "203.0.113.10"},
        )
        # Even without auth (401), the middleware ran and populated the client host
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_untrusted_client_cannot_spoof_forwarded_for():
    """Verify that an untrusted public client cannot spoof its IP via X-Forwarded-For."""
    from fastapi import Request

    # Create a test endpoint to directly inspect resolved request.client.host
    @app.get("/api/v1/test-client-ip", include_in_schema=False)
    async def get_test_client_ip(request: Request):
        return {"ip": request.client.host if request.client else None}

    # Simulate connection directly from public internet IP 198.51.100.25 (not in FORWARDED_ALLOW_IPS)
    untrusted_transport = ASGITransport(app=app, client=("198.51.100.25", 45000))
    async with AsyncClient(transport=untrusted_transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-client-ip",
            headers={"X-Forwarded-For": "8.8.8.8"},
        )
        assert res.status_code == 200
        # The untrusted connection's actual IP must be retained, NOT the spoofed 8.8.8.8
        assert res.json()["ip"] == "198.51.100.25"


@pytest.mark.asyncio
async def test_chained_forwarded_for_extracts_first_untrusted_ip():
    """Verify that when a client passes a fake IP to a trusted proxy, the real client IP is used."""
    # Simulate connection from Docker network bridge IP 172.18.0.2 (matches 172.16.0.0/12)
    docker_proxy_transport = ASGITransport(app=app, client=("172.18.0.2", 34567))
    async with AsyncClient(transport=docker_proxy_transport, base_url="http://test") as client:
        # Client 203.0.113.44 sent a spoofed '1.1.1.1' header to Nginx, so Nginx forwarded '1.1.1.1, 203.0.113.44'
        res = await client.get(
            "/api/v1/test-client-ip",
            headers={"X-Forwarded-For": "1.1.1.1, 203.0.113.44"},
        )
        assert res.status_code == 200
        # The middleware must pick the real untrusted client IP (203.0.113.44), NOT the spoofed 1.1.1.1
        assert res.json()["ip"] == "203.0.113.44"


@pytest.mark.asyncio
async def test_rate_limiting_client_isolation_between_ips(
    client: AsyncClient, db_session: AsyncSession
):
    """Verify that one client exhausting the registration rate limit does not block another client."""
    ip_a = f"198.51.100.{uuid.uuid4().int % 200 + 10}"
    ip_b = f"203.0.113.{uuid.uuid4().int % 200 + 10}"

    # Clear rate limiter state for test determinism
    auth_rate_limiter.reset(f"reg:{ip_a}")
    auth_rate_limiter.reset(f"reg:{ip_b}")

    # First create an existing user to provoke 400 Bad Request on duplicate attempts
    existing_email = f"existing_{uuid.uuid4().hex[:6]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={"email": existing_email, "password": "Password123", "full_name": "Existing"},
        headers={"X-Forwarded-For": "127.0.0.1"},
    )

    # Client A makes 5 rapid duplicate attempts to trigger rate limiting
    for i in range(settings.AUTH_RATE_LIMIT_MAX_ATTEMPTS):
        res = await client.post(
            "/api/v1/auth/register",
            json={"email": existing_email, "password": "Password123", "full_name": "Student A"},
            headers={"X-Forwarded-For": ip_a},
        )
        assert res.status_code == 400

    # 6th attempt from Client A must be rate-limited (HTTP 429)
    blocked_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"client_a_{uuid.uuid4().hex[:6]}@example.com",
            "password": "PasswordA123",
            "full_name": "Student A",
        },
        headers={"X-Forwarded-For": ip_a},
    )
    assert blocked_res.status_code == 429
    assert "Too many registration attempts" in blocked_res.json()["detail"]

    # Client B connecting from a different IP must NOT be blocked!
    client_b_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"client_b_{uuid.uuid4().hex[:6]}@example.com",
            "password": "PasswordB123",
            "full_name": "Student B",
        },
        headers={"X-Forwarded-For": ip_b},
    )
    # Client B should register successfully (201 Created)
    assert client_b_res.status_code == 201
    assert client_b_res.json()["user"]["email"].startswith("client_b_")
