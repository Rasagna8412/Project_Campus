"""Database Configuration and Async Session Management."""

import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure engine arguments dynamically based on database dialect
connect_args = {}
engine_kwargs = {
    "echo": settings.DEBUG and settings.ENVIRONMENT == "development",
    "future": True,
}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
    engine_kwargs["pool_pre_ping"] = settings.DB_POOL_PRE_PING
else:
    # PostgreSQL asynchronous connection pooling
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT
    engine_kwargs["pool_recycle"] = settings.DB_POOL_RECYCLE
    engine_kwargs["pool_pre_ping"] = settings.DB_POOL_PRE_PING
    engine_kwargs["connect_args"] = connect_args

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing database sessions per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connectivity() -> bool:
    """Verify live database connectivity by executing a lightweight query."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        # If the connection pool holds a connection from a previous/different event loop
        # (common during multi-test execution or worker recycle), dispose pool and retry once.
        if "different loop" in str(exc) or "Event loop is closed" in str(exc):
            try:
                await engine.dispose()
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                return True
            except Exception:
                pass
        try:
            masked_url = engine.url.render_as_string(hide_password=True)
            logger.error(f"Database connectivity check failed for {masked_url}: {exc}")
        except Exception:
            logger.error(f"Database connectivity check failed: {exc}")
        return False

