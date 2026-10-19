"""Review item management and idempotent creation service."""

from datetime import timedelta
import logging
from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.sm2 import get_ist_date, INITIAL_EASE_FACTOR
from app.models.content import ContentStatus, Lesson
from app.models.repetition import ReviewItem, ReviewStatus
from app.models.taxonomy import Chapter, Topic

logger = logging.getLogger(__name__)


async def get_or_create_review_item(
    user_id: uuid.UUID,
    topic_id: uuid.UUID,
    subject_id: uuid.UUID,
    db: AsyncSession,
) -> Optional[ReviewItem]:
    """Retrieve existing review item or safely create one in LEARNING status.

    Guarantees idempotency via database savepoint and unique constraint handling.
    Does not swallow unrelated database errors.
    """
    stmt = select(ReviewItem).where(
        ReviewItem.user_id == user_id,
        ReviewItem.topic_id == topic_id,
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        return existing

    today_ist = get_ist_date()
    new_item = ReviewItem(
        user_id=user_id,
        topic_id=topic_id,
        subject_id=subject_id,
        repetition_count=0,
        ease_factor=INITIAL_EASE_FACTOR,
        interval_days=0,
        due_date=today_ist + timedelta(days=1),
        status=ReviewStatus.LEARNING.value,
    )

    try:
        async with db.begin_nested():
            db.add(new_item)
            await db.flush()
        return new_item
    except IntegrityError:
        # Concurrent creation race: savepoint rolled back, fetch existing record
        stmt = select(ReviewItem).where(
            ReviewItem.user_id == user_id,
            ReviewItem.topic_id == topic_id,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing
        raise


async def trigger_review_item_on_lesson_complete(
    user_id: uuid.UUID,
    lesson_id: uuid.UUID,
    db: AsyncSession,
) -> Optional[ReviewItem]:
    """Create a ReviewItem when a student explicitly completes a published lesson."""
    lesson_stmt = (
        select(Lesson)
        .where(
            Lesson.id == lesson_id,
            Lesson.status == ContentStatus.PUBLISHED.value,
        )
        .options(
            selectinload(Lesson.topic).selectinload(Topic.chapter)
        )
    )
    lesson = (await db.execute(lesson_stmt)).scalar_one_or_none()
    if not lesson or not lesson.topic or not lesson.topic.chapter:
        return None

    subject_id = lesson.topic.chapter.subject_id
    topic_id = lesson.topic_id
    return await get_or_create_review_item(user_id, topic_id, subject_id, db)


async def trigger_review_item_on_practice_complete(
    user_id: uuid.UUID,
    topic_id: Optional[uuid.UUID],
    correct_count: int,
    total_questions: int,
    db: AsyncSession,
) -> Optional[ReviewItem]:
    """Create a ReviewItem when a practice session finishes with >= 60% accuracy."""
    if not topic_id or total_questions < 3:
        return None
    accuracy = correct_count / total_questions
    if accuracy < 0.60:
        return None

    top_stmt = (
        select(Topic)
        .where(Topic.id == topic_id)
        .options(selectinload(Topic.chapter))
    )
    topic = (await db.execute(top_stmt)).scalar_one_or_none()
    if not topic or not topic.chapter:
        return None

    subject_id = topic.chapter.subject_id
    return await get_or_create_review_item(user_id, topic_id, subject_id, db)
