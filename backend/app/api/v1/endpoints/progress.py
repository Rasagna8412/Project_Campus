"""Student Lesson Progress Tracking Endpoints."""

from datetime import datetime, timezone
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_role
from app.core.database import get_db
from app.models.content import ContentStatus, Lesson, LessonProgress, LessonProgressStatus
from app.models.identity import User
from app.schemas.progress import LessonProgressResponse

router = APIRouter()


@router.get(
    "/lessons",
    response_model=List[LessonProgressResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated Student's Lesson Progress List",
)
async def get_student_lesson_progress(
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> List[LessonProgressResponse]:
    """Retrieve all recorded lesson progress entries for the authenticated student.

    Strictly isolated to current_user.id. Excludes progress records on unpublished
    lessons if any exist.
    """
    stmt = (
        select(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .where(
            LessonProgress.user_id == current_user.id,
            Lesson.status == ContentStatus.PUBLISHED.value,
        )
        .options(selectinload(LessonProgress.lesson))
        .order_by(LessonProgress.last_accessed_at.desc())
    )
    res = await db.execute(stmt)
    records = res.scalars().all()

    return [
        LessonProgressResponse(
            id=r.id,
            user_id=r.user_id,
            lesson_id=r.lesson_id,
            topic_id=r.lesson.topic_id if r.lesson else None,
            lesson_title=r.lesson.title if r.lesson else None,
            status=r.status,
            started_at=r.started_at,
            completed_at=r.completed_at,
            last_accessed_at=r.last_accessed_at,
        )
        for r in records
    ]


@router.get(
    "/lessons/{lesson_id}",
    response_model=LessonProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Progress for a Specific Lesson",
)
async def get_lesson_progress_item(
    lesson_id: uuid.UUID,
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> LessonProgressResponse:
    """Retrieve the authenticated student's progress for a single lesson."""
    # Ensure lesson exists and is published
    lesson = await db.get(Lesson, lesson_id)
    if not lesson or lesson.status != ContentStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published lesson not found",
        )

    stmt = select(LessonProgress).where(
        LessonProgress.user_id == current_user.id,
        LessonProgress.lesson_id == lesson_id,
    )
    res = await db.execute(stmt)
    progress = res.scalar_one_or_none()

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No progress recorded for this lesson",
        )

    return LessonProgressResponse(
        id=progress.id,
        user_id=progress.user_id,
        lesson_id=progress.lesson_id,
        topic_id=lesson.topic_id,
        lesson_title=lesson.title,
        status=progress.status,
        started_at=progress.started_at,
        completed_at=progress.completed_at,
        last_accessed_at=progress.last_accessed_at,
    )


@router.post(
    "/lessons/{lesson_id}/start",
    response_model=LessonProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Start or Resume a Published Lesson",
)
async def start_or_resume_lesson(
    lesson_id: uuid.UUID,
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> LessonProgressResponse:
    """Record initial access or update last_accessed_at for a published lesson.

    Idempotent:
    - If no progress exists, creates an IN_PROGRESS record.
    - If already COMPLETED, updates last_accessed_at but preserves COMPLETED status and completed_at.
    - If already IN_PROGRESS, updates last_accessed_at.
    """
    lesson = await db.get(Lesson, lesson_id)
    if not lesson or lesson.status != ContentStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published lesson not found",
        )

    now = datetime.now(timezone.utc)
    stmt = select(LessonProgress).where(
        LessonProgress.user_id == current_user.id,
        LessonProgress.lesson_id == lesson_id,
    )
    res = await db.execute(stmt)
    progress = res.scalar_one_or_none()

    if not progress:
        progress = LessonProgress(
            user_id=current_user.id,
            lesson_id=lesson.id,
            status=LessonProgressStatus.IN_PROGRESS.value,
            started_at=now,
            last_accessed_at=now,
        )
        db.add(progress)
    else:
        progress.last_accessed_at = now

    await db.commit()
    await db.refresh(progress)

    return LessonProgressResponse(
        id=progress.id,
        user_id=progress.user_id,
        lesson_id=progress.lesson_id,
        topic_id=lesson.topic_id,
        lesson_title=lesson.title,
        status=progress.status,
        started_at=progress.started_at,
        completed_at=progress.completed_at,
        last_accessed_at=progress.last_accessed_at,
    )


@router.post(
    "/lessons/{lesson_id}/complete",
    response_model=LessonProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Explicitly Mark a Published Lesson as Completed",
)
async def mark_lesson_completed(
    lesson_id: uuid.UUID,
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> LessonProgressResponse:
    """Explicitly mark a published lesson as completed.

    Idempotent:
    - If no progress exists, creates a COMPLETED record.
    - If already completed, updates last_accessed_at while preserving the original completed_at.
    - If IN_PROGRESS, sets status to COMPLETED and records completed_at.
    """
    lesson = await db.get(Lesson, lesson_id)
    if not lesson or lesson.status != ContentStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published lesson not found",
        )

    now = datetime.now(timezone.utc)
    stmt = select(LessonProgress).where(
        LessonProgress.user_id == current_user.id,
        LessonProgress.lesson_id == lesson_id,
    )
    res = await db.execute(stmt)
    progress = res.scalar_one_or_none()

    if not progress:
        progress = LessonProgress(
            user_id=current_user.id,
            lesson_id=lesson.id,
            status=LessonProgressStatus.COMPLETED.value,
            started_at=now,
            completed_at=now,
            last_accessed_at=now,
        )
        db.add(progress)
    else:
        progress.status = LessonProgressStatus.COMPLETED.value
        if not progress.completed_at:
            progress.completed_at = now
        progress.last_accessed_at = now

    await db.commit()
    await db.refresh(progress)

    return LessonProgressResponse(
        id=progress.id,
        user_id=progress.user_id,
        lesson_id=progress.lesson_id,
        topic_id=lesson.topic_id,
        lesson_title=lesson.title,
        status=progress.status,
        started_at=progress.started_at,
        completed_at=progress.completed_at,
        last_accessed_at=progress.last_accessed_at,
    )
