"""Tests for Global Error Handling and Information Leakage Prevention."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from fastapi import APIRouter

error_test_router = APIRouter()


@error_test_router.get("/test-internal-error")
async def trigger_simulated_error():
    """Endpoint that raises an uncaught exception to test global handler."""
    raise RuntimeError("Simulated internal exception with sensitive SECRET_KEY_12345")


# Mount temporarily for error testing
app.include_router(error_test_router, prefix="/api/v1")


@pytest.mark.asyncio
async def test_non_existent_endpoint_returns_404(client: AsyncClient):
    """Verify that 404 is returned for undefined endpoints."""
    response = await client.get("/api/v1/non-existent-route")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_internal_error_does_not_leak_stack_trace_or_secrets():
    """Verify that unhandled exceptions return HTTP 500 and do not leak stack traces or secret variables."""
    # Using raise_app_exceptions=False allows verifying the actual HTTP 500 response payload received by clients
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/test-internal-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "InternalServerError"
        assert "SECRET_KEY_12345" not in response.text
        assert "Traceback" not in response.text
        assert "RuntimeError" not in response.text


def test_production_secret_key_validation():
    """Verify that development secrets are blocked when ENVIRONMENT=production."""
    from app.core.config import Settings

    # 1. Default dev key in production raises ValueError
    with pytest.raises(ValueError, match="Production environment requires a high-entropy SECRET_KEY"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="dev-insecure-secret-key-change-in-production-campus-2026-xyz",
        )

    # 2. Too short secret key raises ValueError
    with pytest.raises(ValueError, match="Production environment requires a high-entropy SECRET_KEY"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="short_key_123",
        )

    # 3. High-entropy key succeeds and automatically enforces secure cookies
    prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="high-entropy-production-secret-key-2026-minimum-32-chars",
        AUTH_COOKIE_SECURE=False,  # Should be forced to True
    )
    assert prod_settings.AUTH_COOKIE_SECURE is True

