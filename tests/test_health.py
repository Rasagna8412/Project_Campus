"""Tests for Backend Health Check Endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health_endpoint(client: AsyncClient):
    """Verify that root GET /health returns HTTP 200 and documented payload."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert "database" in data


@pytest.mark.asyncio
async def test_api_v1_health_endpoint(client: AsyncClient):
    """Verify that GET /api/v1/health functions with status 200."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_api_v1_health_with_database_check(client: AsyncClient):
    """Verify that GET /api/v1/health?check_db=true performs genuine DB verification."""
    response = await client.get("/api/v1/health?check_db=true")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
