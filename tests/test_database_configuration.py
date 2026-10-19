"""Tests for Database Configuration, Asynchronous Engine Pooling, and Dialect Handling."""

import pytest
from app.core.config import Settings
from app.core.database import create_async_engine, check_database_connectivity


def test_database_url_normalization():
    """Verify that postgres:// and postgresql:// prefixes normalize to postgresql+asyncpg://."""
    s1 = Settings(DATABASE_URL="postgres://user:secret@localhost:5432/campus")
    assert s1.DATABASE_URL == "postgresql+asyncpg://user:secret@localhost:5432/campus"

    s2 = Settings(DATABASE_URL="postgresql://user:secret@localhost:5432/campus")
    assert s2.DATABASE_URL == "postgresql+asyncpg://user:secret@localhost:5432/campus"

    s3 = Settings(DATABASE_URL="postgresql+asyncpg://user:secret@localhost:5432/campus")
    assert s3.DATABASE_URL == "postgresql+asyncpg://user:secret@localhost:5432/campus"

    s4 = Settings(DATABASE_URL="sqlite+aiosqlite:///test.db")
    assert s4.DATABASE_URL == "sqlite+aiosqlite:///test.db"


def test_pool_configuration_defaults():
    """Verify pool size, overflow, timeout, and pre-ping defaults."""
    settings = Settings()
    assert settings.DB_POOL_SIZE == 10
    assert settings.DB_MAX_OVERFLOW == 20
    assert settings.DB_POOL_TIMEOUT == 30
    assert settings.DB_POOL_RECYCLE == 1800
    assert settings.DB_POOL_PRE_PING is True


def test_production_pool_validation():
    """Verify that invalid pool configurations in production raise ValueError."""
    # Invalid pool size
    with pytest.raises(ValueError, match="DB_POOL_SIZE must be at least 1 in production."):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="high-entropy-production-secret-key-2026-minimum-32-chars",
            DB_POOL_SIZE=0,
        )

    # Invalid max overflow
    with pytest.raises(ValueError, match="DB_MAX_OVERFLOW cannot be negative."):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="high-entropy-production-secret-key-2026-minimum-32-chars",
            DB_MAX_OVERFLOW=-1,
        )


def test_postgresql_async_engine_instantiation():
    """Verify that create_async_engine instantiates an AsyncEngine with asyncpg pooling without live network call."""
    pg_url = "postgresql+asyncpg://dummy_user:dummy_pass@127.0.0.1:5432/dummy_db"
    engine = create_async_engine(
        pg_url,
        pool_size=5,
        max_overflow=10,
        pool_timeout=15,
        pool_recycle=900,
        pool_pre_ping=True,
    )
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "asyncpg"

    # Verify password masking renders credentials safely as '***'
    masked = engine.url.render_as_string(hide_password=True)
    assert "dummy_pass" not in masked
    assert "***" in masked


@pytest.mark.asyncio
async def test_database_connectivity_check_sqlite():
    """Verify check_database_connectivity runs successfully on active database."""
    connected = await check_database_connectivity()
    assert connected is True
