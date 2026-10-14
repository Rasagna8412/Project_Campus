"""Tests for Database Connectivity and Initialization."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import check_database_connectivity


@pytest.mark.asyncio
async def test_database_connectivity():
    """Verify that check_database_connectivity executes without error."""
    is_connected = await check_database_connectivity()
    assert is_connected is True


@pytest.mark.asyncio
async def test_database_table_presence(db_session: AsyncSession):
    """Verify that core Milestone 1 tables exist in the database."""
    result = await db_session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table'")
    )
    tables = [row[0] for row in result.fetchall()]

    expected_tables = [
        "users",
        "roles",
        "user_roles",
        "student_profiles",
        "boards_curricula",
        "grades_stages",
        "subjects",
        "chapters",
        "topics",
    ]

    for expected in expected_tables:
        assert expected in tables, f"Expected table '{expected}' not found in database"
