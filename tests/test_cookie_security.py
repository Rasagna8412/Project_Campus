"""Regression Tests for Production Cookie and Session Security."""

import uuid
import pytest
from httpx import AsyncClient

from app.core.config import Settings, settings


def test_production_settings_enforces_secure_cookie():
    """Verify that Settings validator enforces AUTH_COOKIE_SECURE=True in production."""
    prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a-very-long-and-secure-high-entropy-production-secret-key-12345",
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/campus_prod",
        AUTH_COOKIE_SECURE=False,  # Explicitly passed False
    )
    # The model validator must force it to True
    assert prod_settings.AUTH_COOKIE_SECURE is True


def test_production_settings_enforces_debug_false_when_omitted():
    """Verify that Settings validator enforces DEBUG=False in production when omitted."""
    prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a-very-long-and-secure-high-entropy-production-secret-key-12345",
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/campus_prod",
    )
    assert prod_settings.DEBUG is False


def test_production_settings_enforces_debug_false_when_explicitly_true():
    """Verify that Settings validator enforces DEBUG=False in production even if DEBUG=True is supplied."""
    prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a-very-long-and-secure-high-entropy-production-secret-key-12345",
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/campus_prod",
        DEBUG=True,
    )
    assert prod_settings.DEBUG is False


def test_development_settings_retains_debug_true():
    """Verify that development environment retains DEBUG=True by default."""
    dev_settings = Settings(ENVIRONMENT="development")
    assert dev_settings.DEBUG is True


def test_development_settings_retains_debug_false_when_explicitly_disabled():
    """Verify that development environment allows explicitly disabling DEBUG."""
    dev_settings = Settings(ENVIRONMENT="development", DEBUG=False)
    assert dev_settings.DEBUG is False


@pytest.mark.asyncio
async def test_production_documentation_routes_disabled():
    """Verify that in production (DEBUG=False), docs, redoc, and openapi routes are not exposed."""
    from fastapi import FastAPI
    from httpx import ASGITransport

    prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a-very-long-and-secure-high-entropy-production-secret-key-12345",
        DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/campus_prod",
        DEBUG=True,  # Will be forced False by validator
    )
    assert prod_settings.DEBUG is False

    prod_app = FastAPI(
        title=prod_settings.APP_NAME,
        docs_url="/docs" if prod_settings.DEBUG else None,
        redoc_url="/redoc" if prod_settings.DEBUG else None,
        openapi_url="/openapi.json" if prod_settings.DEBUG else None,
    )

    transport = ASGITransport(app=prod_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        docs_res = await client.get("/docs")
        redoc_res = await client.get("/redoc")
        openapi_res = await client.get("/openapi.json")

        assert docs_res.status_code == 404
        assert redoc_res.status_code == 404
        assert openapi_res.status_code == 404


def test_production_settings_rejects_insecure_default_secret_key():
    """Verify that Settings validator rejects default dev secret keys in production."""
    with pytest.raises(ValueError, match="Production environment requires a high-entropy SECRET_KEY"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="dev-insecure-secret-key-change-in-production-campus-2026-xyz",
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/campus_prod",
        )


@pytest.mark.asyncio
async def test_auth_cookie_attributes_on_register(client: AsyncClient, monkeypatch):
    """Verify registration cookie contains HttpOnly and SameSite attributes."""
    email = f"cookie_test_{uuid.uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password12345", "full_name": "Cookie Tester"},
    )
    assert response.status_code == 201

    # Inspect Set-Cookie header
    set_cookie = response.headers.get("set-cookie")
    assert set_cookie is not None
    assert settings.AUTH_COOKIE_NAME in set_cookie
    assert "httponly" in set_cookie.lower()
    assert "samesite=lax" in set_cookie.lower()


@pytest.mark.asyncio
async def test_auth_cookie_secure_flag_when_enabled(client: AsyncClient, monkeypatch):
    """Verify that Set-Cookie includes 'secure' flag when AUTH_COOKIE_SECURE is enabled."""
    # Temporarily enable AUTH_COOKIE_SECURE
    monkeypatch.setattr(settings, "AUTH_COOKIE_SECURE", True)

    email = f"secure_cookie_{uuid.uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password12345", "full_name": "Secure Tester"},
    )
    assert response.status_code == 201

    set_cookie = response.headers.get("set-cookie")
    assert set_cookie is not None
    assert "secure" in set_cookie.lower()


@pytest.mark.asyncio
async def test_auth_cookie_cleared_on_logout(client: AsyncClient):
    """Verify that logout instructs the browser to delete the authentication cookie."""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200

    set_cookie = response.headers.get("set-cookie")
    assert set_cookie is not None
    assert settings.AUTH_COOKIE_NAME in set_cookie
    # Deleting cookie sets Max-Age=0 or past expires date
    assert 'max-age=0' in set_cookie.lower() or 'expires=' in set_cookie.lower()
