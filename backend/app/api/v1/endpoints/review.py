"""Spaced Repetition Review Queue, Submission, History, and Statistics Endpoints."""

from datetime import datetime, timezone
import math
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_role
from app.core.database import get_db
from app.core.sm2 import calculate_sm2, get_ist_date, PLANNER_TZ
from app.models.assessment import Question
from app.models.content import ContentStatus
from app.models.identity import User
from app.models.planner import StudyTask, TaskStatus
from app.models.repetition import ReviewItem, ReviewLog, ReviewStatus
from app.models.taxonomy import Chapter, Subject, Topic
from app.schemas.repetition import (
    ReviewHistoryResponse,
    ReviewItemSummary,
    ReviewLogItem,
    ReviewQueueResponse,
    ReviewStatsResponse,
    ReviewSubmitRequest,
    ReviewSubmitResponse,
)

router = APIRouter()


@router.get(
    "/queue",
    response_model=ReviewQueueResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Active Due Review Items for Student",
)
async def get_review_queue(
    subject_id: Optional[uuid.UUID] = Query(default=None, description="Optional subject filter"),
    limit: int = Query(default=20, ge=1, le=50, description="Max items to return in page"),
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> ReviewQueueResponse:
    """Retrieve items due on or before today in IST, ordered by urgency and repetition count."""
    today_ist = get_ist_date()

    # Base query for active due items belonging to this student
    base_conditions = [
        ReviewItem.user_id == current_user.id,
        ReviewItem.due_date <= today_ist,
    ]
    if subject_id:
        base_conditions.append(ReviewItem.subject_id == subject_id)

    # 1. Total counts across entire queue
    tot_stmt = select(func.count(ReviewItem.id)).where(*base_conditions)
    total_due_count = (await db.execute(tot_stmt)).scalar() or 0

    overdue_stmt = select(func.count(ReviewItem.id)).where(
        *base_conditions,
        ReviewItem.due_date < today_ist,
    )
    overdue_count = (await db.execute(overdue_stmt)).scalar() or 0

    # 2. Paginated item query with relationships
    query = (
        select(ReviewItem)
        .where(*base_conditions)
        .options(
            selectinload(ReviewItem.topic).selectinload(Topic.chapter),
            selectinload(ReviewItem.subject),
        )
        .order_by(
            ReviewItem.due_date.asc(),
            ReviewItem.repetition_count.asc(),
        )
        .limit(limit)
    )
    items = (await db.execute(query)).scalars().all()

    # 3. Assemble summaries with question counts
    summaries: List[ReviewItemSummary] = []
    for item in items:
        # Count available published questions for this topic
        q_count_stmt = select(func.count(Question.id)).where(
            Question.topic_id == item.topic_id,
            Question.status == ContentStatus.PUBLISHED.value,
        )
        q_count = (await db.execute(q_count_stmt)).scalar() or 0

        topic_title = item.topic.title if item.topic else "General Topic"
        chapter_title = (
            item.topic.chapter.title
            if item.topic and item.topic.chapter
            else "General Chapter"
        )
        subject_name = item.subject.name if item.subject else "General Subject"

        summaries.append(
            ReviewItemSummary(
                id=item.id,
                topic_id=item.topic_id,
                topic_title=topic_title,
                subject_id=item.subject_id,
                subject_name=subject_name,
                chapter_title=chapter_title,
                due_date=item.due_date,
                repetition_count=item.repetition_count,
                interval_days=item.interval_days,
                ease_factor=item.ease_factor,
                status=item.status,
                is_overdue=item.due_date < today_ist,
                sample_question_count=q_count,
            )
        )

    return ReviewQueueResponse(
        date=today_ist,
        total_due_count=total_due_count,
        overdue_count=overdue_count,
        returned_count=len(summaries),
        items=summaries,
    )


@router.post(
    "/items/{item_id}/submit",
    response_model=ReviewSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Active Recall Review Rating for Topic",
)
async def submit_review_rating(
    item_id: uuid.UUID,
    payload: ReviewSubmitRequest,
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> ReviewSubmitResponse:
    """Submit an SM-2 rating (0-5) for a due review item.

    Guarantees:
    - Pessimistic row locking on User and ReviewItem to serialize parallel worker requests.
    - Idempotent rejection of same-IST-day duplicate reviews (HTTP 409 Conflict).
    - Atomic commit of ReviewItem state update and ReviewLog creation.
    - Optional synchronization with active daily planner task for this topic.
    """
    today_ist = get_ist_date()

    # Step 1: Pessimistic lock on User to serialize student transactions
    user_lock = select(User.id).where(User.id == current_user.id).with_for_update()
    await db.execute(user_lock)

    # Step 2: Pessimistic lock on target ReviewItem
    item_stmt = (
        select(ReviewItem)
        .where(
            ReviewItem.id == item_id,
            ReviewItem.user_id == current_user.id,
        )
        .with_for_update()
    )
    item = (await db.execute(item_stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review item not found.",
        )

    # Step 3: Same-IST-day duplicate review prevention
    if item.last_reviewed_at is not None:
        last_ist_date = item.last_reviewed_at.astimezone(PLANNER_TZ).date()
        if last_ist_date == today_ist:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"This item has already been reviewed today ({today_ist.isoformat()}). "
                    f"Next review is scheduled for {item.due_date.isoformat()}."
                ),
            )

    # Step 4: Execute pure SuperMemo SM-2 calculation
    old_interval = item.interval_days
    old_ef = item.ease_factor
    res = calculate_sm2(
        repetition_count=item.repetition_count,
        ease_factor=item.ease_factor,
        interval_days=item.interval_days,
        quality_score=payload.quality_score,
        review_date=today_ist,
    )

    now_utc = datetime.now(timezone.utc)

    # Step 5: Update ReviewItem state
    item.repetition_count = res.repetition_count
    item.ease_factor = res.ease_factor
    item.interval_days = res.interval_days
    item.due_date = res.due_date
    item.status = res.status
    item.last_reviewed_at = now_utc

    # Step 6: Insert immutable ReviewLog
    log = ReviewLog(
        review_item_id=item.id,
        user_id=current_user.id,
        quality_score=payload.quality_score,
        time_spent_seconds=payload.time_spent_seconds,
        scheduled_interval_days=old_interval,
        next_interval_days=res.interval_days,
        ease_factor_before=old_ef,
        ease_factor_after=res.ease_factor,
        reviewed_at=now_utc,
    )
    db.add(log)

    # Step 7: Complete matching StudyTask for today if scheduled
    planner_task_stmt = select(StudyTask).where(
        StudyTask.user_id == current_user.id,
        StudyTask.scheduled_date == today_ist,
        StudyTask.topic_id == item.topic_id,
        StudyTask.is_completed == False,
    )
    matched_tasks = (await db.execute(planner_task_stmt)).scalars().all()
    for pt in matched_tasks:
        pt.is_completed = True
        pt.status = TaskStatus.COMPLETED.value
        pt.completed_at = now_utc

    # Step 8: Single atomic commit
    await db.commit()
    await db.refresh(item)

    msg = (
        f"Review recorded successfully. Next review scheduled in {res.interval_days} "
        f"day(s) on {res.due_date.isoformat()}."
    )
    return ReviewSubmitResponse(
        review_item_id=item.id,
        repetition_count=item.repetition_count,
        ease_factor=item.ease_factor,
        interval_days=item.interval_days,
        next_due_date=item.due_date,
        quality_score=payload.quality_score,
        status=item.status,
        message=msg,
    )


@router.get(
    "/history",
    response_model=ReviewHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Paginated Student Review History",
)
async def get_review_history(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> ReviewHistoryResponse:
    """Retrieve historical review logs with pagination."""
    tot_stmt = select(func.count(ReviewLog.id)).where(ReviewLog.user_id == current_user.id)
    total_count = (await db.execute(tot_stmt)).scalar() or 0
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    offset = (page - 1) * page_size
    stmt = (
        select(ReviewLog)
        .where(ReviewLog.user_id == current_user.id)
        .options(selectinload(ReviewLog.item).selectinload(ReviewItem.topic))
        .order_by(ReviewLog.reviewed_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    logs = (await db.execute(stmt)).scalars().all()

    items: List[ReviewLogItem] = []
    for log in logs:
        topic_id = log.item.topic_id if log.item else uuid.UUID(int=0)
        topic_title = (
            log.item.topic.title
            if log.item and log.item.topic
            else "General Topic"
        )
        items.append(
            ReviewLogItem(
                id=log.id,
                review_item_id=log.review_item_id,
                topic_id=topic_id,
                topic_title=topic_title,
                quality_score=log.quality_score,
                time_spent_seconds=log.time_spent_seconds,
                scheduled_interval_days=log.scheduled_interval_days,
                next_interval_days=log.next_interval_days,
                ease_factor_before=log.ease_factor_before,
                ease_factor_after=log.ease_factor_after,
                reviewed_at=log.reviewed_at,
            )
        )

    return ReviewHistoryResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


@router.get(
    "/stats",
    response_model=ReviewStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Student Spaced Repetition KPI Statistics",
)
async def get_review_stats(
    current_user: User = Depends(require_role("STUDENT")),
    db: AsyncSession = Depends(get_db),
) -> ReviewStatsResponse:
    """Calculate aggregate retention statistics for student dashboard widgets."""
    today_ist = get_ist_date()

    # 1. Total tracked topics
    tot_stmt = select(func.count(ReviewItem.id)).where(ReviewItem.user_id == current_user.id)
    total_tracked_topics = (await db.execute(tot_stmt)).scalar() or 0

    # 2. Due today count
    due_stmt = select(func.count(ReviewItem.id)).where(
        ReviewItem.user_id == current_user.id,
        ReviewItem.due_date <= today_ist,
    )
    due_today_count = (await db.execute(due_stmt)).scalar() or 0

    # 3. Mastered topics count
    mast_stmt = select(func.count(ReviewItem.id)).where(
        ReviewItem.user_id == current_user.id,
        ReviewItem.status == ReviewStatus.MASTERED.value,
    )
    mastered_count = (await db.execute(mast_stmt)).scalar() or 0

    # 4. Average ease factor
    avg_ef_stmt = select(func.avg(ReviewItem.ease_factor)).where(
        ReviewItem.user_id == current_user.id
    )
    avg_ef_res = (await db.execute(avg_ef_stmt)).scalar()
    average_ease_factor = round(float(avg_ef_res), 2) if avg_ef_res is not None else 2.50

    # 5. Success rate percentage (reviews scoring q >= 3)
    tot_logs_stmt = select(func.count(ReviewLog.id)).where(ReviewLog.user_id == current_user.id)
    total_logs = (await db.execute(tot_logs_stmt)).scalar() or 0

    success_logs_stmt = select(func.count(ReviewLog.id)).where(
        ReviewLog.user_id == current_user.id,
        ReviewLog.quality_score >= 3,
    )
    successful_logs = (await db.execute(success_logs_stmt)).scalar() or 0

    success_rate: Optional[float] = None
    if total_logs > 0:
        success_rate = round((successful_logs / total_logs) * 100.0, 1)

    return ReviewStatsResponse(
        total_tracked_topics=total_tracked_topics,
        due_today_count=due_today_count,
        mastered_count=mastered_count,
        average_ease_factor=average_ease_factor,
        successful_review_rate_percentage=success_rate,
    )
