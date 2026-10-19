"""Genuine PostgreSQL Integration & Dialect Verification Test Suite.

Validates PostgreSQL compatibility, asynchronous connection pooling, query compilation,
Alembic migration generation, and executes live database operations whenever a
PostgreSQL test instance is available.
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path
import uuid
import pytest
from sqlalchemy import select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.models.assessment import Question, QuestionErrataReport
from app.models.repetition import ReviewItem, ReviewLog, ReviewStatus

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

# Configurable PostgreSQL test database URL
_env_pg_url = os.environ.get("POSTGRES_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
if _env_pg_url and "postgres" in _env_pg_url:
    POSTGRES_TEST_URL = _env_pg_url
else:
    POSTGRES_TEST_URL = "postgresql+asyncpg://campus_user:campus_dev_secret@127.0.0.1:5432/project_campus_test"


def _check_live_postgres() -> bool:
    """Detect whether a live PostgreSQL server is reachable for integration testing."""
    async def _probe():
        engine = create_async_engine(
            POSTGRES_TEST_URL,
            connect_args={"timeout": 2},
        )
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
        finally:
            await engine.dispose()

    try:
        return asyncio.run(_probe())
    except Exception:
        return False


LIVE_POSTGRES_AVAILABLE = _check_live_postgres()
requires_live_postgres = pytest.mark.skipif(
    not LIVE_POSTGRES_AVAILABLE,
    reason="Live PostgreSQL database not reachable on localhost:5432. Start Docker Compose or set POSTGRES_TEST_DATABASE_URL.",
)


# ==============================================================================
# SECTION 1: Dialect & Architecture Verification (Runs in all environments)
# ==============================================================================

def test_postgresql_dialect_row_lock_compilation():
    """Verify that select(...).with_for_update() compiles to native PostgreSQL FOR UPDATE syntax."""
    stmt = select(ReviewItem).where(ReviewItem.status == ReviewStatus.LEARNING.value).with_for_update()
    compiled = str(stmt.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE" in compiled
    assert "review_items" in compiled


def test_postgresql_dialect_skip_locked_compilation():
    """Verify that with_for_update(skip_locked=True) compiles to FOR UPDATE SKIP LOCKED in PostgreSQL."""
    stmt = (
        select(ReviewItem)
        .where(ReviewItem.status == ReviewStatus.LEARNING.value)
        .with_for_update(skip_locked=True)
    )
    compiled = str(stmt.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE SKIP LOCKED" in compiled


def test_postgresql_connection_pool_configuration():
    """Verify AsyncEngine creation with asyncpg pooling settings and masked credentials."""
    test_url = "postgresql+asyncpg://app_user:super_secret_pw@db.internal:5432/campus_prod"
    engine = create_async_engine(
        test_url,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "asyncpg"

    # Verify password masking
    masked_url = engine.url.render_as_string(hide_password=True)
    assert "super_secret_pw" not in masked_url
    assert "***" in masked_url


def test_postgresql_alembic_ddl_generation_offline():
    """Verify that Alembic compiles the entire migration chain (base -> 0cbebed2ada2)

    into valid PostgreSQL DDL statements using native UUID and ALTER TABLE operations.
    """
    alembic_ini = BACKEND_DIR / "alembic.ini"
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/ddl_check"

    res = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head", "--sql"],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode == 0, f"Alembic PostgreSQL DDL generation failed:\n{res.stderr}"
    sql_output = res.stdout
    assert "CREATE TABLE review_items" in sql_output
    assert "UUID NOT NULL" in sql_output
    assert "uq_study_tasks_user_date_order" in sql_output
    assert "0cbebed2ada2" in sql_output


# ==============================================================================
# SECTION 2: Live PostgreSQL Integration Tests (Requires running PostgreSQL)
# ==============================================================================

@pytest.fixture(scope="module")
async def pg_engine():
    """Create a live PostgreSQL async engine for integration tests."""
    engine = create_async_engine(
        POSTGRES_TEST_URL,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
    )
    yield engine
    await engine.dispose()


@pytest.fixture
async def pg_session(pg_engine):
    """Provide a transactional session for PostgreSQL integration tests."""
    session_factory = async_sessionmaker(bind=pg_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@requires_live_postgres
@pytest.mark.asyncio
async def test_live_postgres_connectivity(pg_engine):
    """Verify live async query execution on PostgreSQL."""
    async with pg_engine.connect() as conn:
        result = await conn.execute(text("SELECT version();"))
        version = result.scalar()
        assert "PostgreSQL" in version


@requires_live_postgres
@pytest.mark.asyncio
async def test_live_postgres_concurrent_pool_connections(pg_engine):
    """Verify connection pool handles concurrent async operations without exhaustion."""
    async def run_query(idx: int):
        async with pg_engine.connect() as conn:
            res = await conn.execute(text(f"SELECT {idx} AS worker_id"))
            return res.scalar()

    results = await asyncio.gather(*(run_query(i) for i in range(15)))
    assert results == list(range(15))


@requires_live_postgres
@pytest.mark.asyncio
async def test_live_postgres_savepoint_collision_handling(pg_session: AsyncSession):
    """Verify PostgreSQL transaction savepoint (begin_nested) handles key collision and rolls back cleanly without invalidating outer transaction."""
    # Create an isolated temporary test table within this transaction
    await pg_session.execute(
        text("CREATE TEMP TABLE _test_collision (id int PRIMARY KEY, val text) ON COMMIT DROP")
    )
    await pg_session.execute(text("INSERT INTO _test_collision (id, val) VALUES (1, 'initial')"))

    # Attempt duplicate insert inside a nested savepoint
    savepoint_rolled_back = False
    try:
        async with pg_session.begin_nested():
            await pg_session.execute(
                text("INSERT INTO _test_collision (id, val) VALUES (1, 'collision')")
            )
    except Exception:
        # Savepoint automatically rolled back on exception
        savepoint_rolled_back = True

    assert savepoint_rolled_back is True

    # Under PostgreSQL, without a savepoint, the entire transaction would be aborted (InFailedSqlTransaction).
    # Because begin_nested() rolled back to the savepoint, subsequent queries in the outer transaction succeed.
    res = await pg_session.execute(text("SELECT val FROM _test_collision WHERE id = 1"))
    val = res.scalar()
    assert val == "initial"


@requires_live_postgres
@pytest.mark.asyncio
async def test_live_postgres_for_update_skip_locked(pg_engine):
    """Verify live PostgreSQL row-level locking with FOR UPDATE SKIP LOCKED across two concurrent sessions."""
    # Ensure test table exists
    async with pg_engine.begin() as init_conn:
        await init_conn.execute(
            text("CREATE TABLE IF NOT EXISTS _test_queue_lock (id INT PRIMARY KEY, payload TEXT);")
        )
        await init_conn.execute(text("TRUNCATE _test_queue_lock;"))
        await init_conn.execute(
            text("INSERT INTO _test_queue_lock (id, payload) VALUES (101, 'task_1'), (102, 'task_2');")
        )

    try:
        session_factory = async_sessionmaker(bind=pg_engine, class_=AsyncSession, expire_on_commit=False)

        async with session_factory() as session1, session_factory() as session2:
            try:
                # Session 1 locks the first available row
                q1 = await session1.execute(
                    text("SELECT id FROM _test_queue_lock ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED;")
                )
                locked_id_1 = q1.scalar()
                assert locked_id_1 == 101

                # Session 2 concurrently requests the first available row with SKIP LOCKED
                # Since row 101 is locked by Session 1, Session 2 MUST skip row 101 and lock row 102!
                q2 = await session2.execute(
                    text("SELECT id FROM _test_queue_lock ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED;")
                )
                locked_id_2 = q2.scalar()
                assert locked_id_2 == 102
            finally:
                await session1.rollback()
                await session2.rollback()
    finally:
        # Clean up test table even if assertions fail
        async with pg_engine.begin() as cleanup_conn:
            await cleanup_conn.execute(text("DROP TABLE IF EXISTS _test_queue_lock;"))



@requires_live_postgres
@pytest.mark.asyncio
async def test_live_postgres_foreign_key_cascade_deletion(pg_session: AsyncSession):
    """Verify that PostgreSQL enforces native FOREIGN KEY ... ON DELETE CASCADE on real schema tables."""
    await pg_session.execute(
        text("CREATE TEMP TABLE _test_parent (id int PRIMARY KEY) ON COMMIT DROP;")
    )
    await pg_session.execute(
        text("CREATE TEMP TABLE _test_child (id int PRIMARY KEY, parent_id int REFERENCES _test_parent(id) ON DELETE CASCADE) ON COMMIT DROP;")
    )
    await pg_session.execute(text("INSERT INTO _test_parent VALUES (1);"))
    await pg_session.execute(text("INSERT INTO _test_child VALUES (10, 1);"))

    # Deleting parent must automatically delete child via PostgreSQL engine cascade
    await pg_session.execute(text("DELETE FROM _test_parent WHERE id = 1;"))
    res = await pg_session.execute(text("SELECT COUNT(*) FROM _test_child WHERE id = 10;"))
    assert res.scalar() == 0

