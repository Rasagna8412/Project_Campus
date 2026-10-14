"""Tests for Milestone 1 SQLAlchemy Models and Integrity Constraints."""

import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.identity import Role, StudentProfile, User, UserRole
from app.models.taxonomy import (
    BoardCurriculum,
    Chapter,
    GradeStage,
    Subject,
    Topic,
)


@pytest.mark.asyncio
async def test_create_curriculum_taxonomy(db_session: AsyncSession):
    """Test full hierarchical creation: Board -> Grade -> Subject -> Chapter -> Topic."""
    # 1. Create Board
    board = BoardCurriculum(
        code=f"CBSE_{uuid.uuid4().hex[:6]}",
        name="Central Board of Secondary Education",
        country_code="IND",
        description="Indian National Secondary Education Board",
    )
    db_session.add(board)
    await db_session.flush()
    assert board.id is not None
    assert isinstance(board.id, uuid.UUID)

    # 2. Create Grade
    grade = GradeStage(
        board_id=board.id,
        code="CLASS_11",
        name="Class XI Higher Secondary",
        display_order=1,
    )
    db_session.add(grade)
    await db_session.flush()

    # 3. Create Subject
    subject = Subject(
        grade_stage_id=grade.id,
        code="PHYSICS",
        name="Physics",
        display_order=1,
    )
    db_session.add(subject)
    await db_session.flush()

    # 4. Create Chapter
    chapter = Chapter(
        subject_id=subject.id,
        chapter_number=1,
        title="Units and Measurements",
        slug="units-and-measurements",
    )
    db_session.add(chapter)
    await db_session.flush()

    # 5. Create Topic
    topic = Topic(
        chapter_id=chapter.id,
        topic_number=1,
        title="SI Units & Dimensions",
        slug="si-units-and-dimensions",
        importance_weight=2,
    )
    db_session.add(topic)
    await db_session.flush()

    # Verify query through relationships
    stmt = (
        select(BoardCurriculum)
        .where(BoardCurriculum.id == board.id)
    )
    result = await db_session.execute(stmt)
    loaded_board = result.scalar_one()
    assert loaded_board.name == "Central Board of Secondary Education"


@pytest.mark.asyncio
async def test_duplicate_board_code_raises_integrity_error(db_session: AsyncSession):
    """Verify that uniqueness constraint on board code is enforced."""
    unique_code = f"TEST_CODE_{uuid.uuid4().hex[:6]}"
    b1 = BoardCurriculum(code=unique_code, name="Board One")
    db_session.add(b1)
    await db_session.flush()

    b2 = BoardCurriculum(code=unique_code, name="Board Duplicate")
    db_session.add(b2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_user_role_and_student_profile_association(db_session: AsyncSession):
    """Test User creation, role assignment, and student profile association."""
    unique_email = f"student_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        hashed_password="hashed_argon2_password_placeholder",
        full_name="Ananya Sharma",
    )
    db_session.add(user)
    await db_session.flush()
    assert user.id is not None

    role = Role(name=f"STUDENT_{uuid.uuid4().hex[:6]}", description="Student Learner")
    db_session.add(role)
    await db_session.flush()

    user_role = UserRole(user_id=user.id, role_id=role.id)
    db_session.add(user_role)

    profile = StudentProfile(
        user_id=user.id,
        daily_study_goal_minutes=150,
        preferred_language="en",
    )
    db_session.add(profile)
    await db_session.flush()

    # Query back
    stmt = select(User).where(User.id == user.id)
    result = await db_session.execute(stmt)
    loaded_user = result.scalar_one()
    assert loaded_user.full_name == "Ananya Sharma"
    assert loaded_user.is_active is True
