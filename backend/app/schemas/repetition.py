"""Pydantic v2 Schemas for Spaced Repetition and Revision Queue APIs."""

from datetime import date, datetime
import math
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class ReviewItemSummary(BaseModel):
    """Serialized summary of an individual due or tracked review item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic_id: uuid.UUID
    topic_title: str
    subject_id: uuid.UUID
    subject_name: str
    chapter_title: str
    due_date: date
    repetition_count: int
    interval_days: int
    ease_factor: float
    status: str
    is_overdue: bool
    sample_question_count: int


class ReviewQueueResponse(BaseModel):
    """Review queue payload containing due items and summary counts."""

    date: date
    total_due_count: int
    overdue_count: int
    returned_count: int
    items: List[ReviewItemSummary]


class ReviewSubmitRequest(BaseModel):
    """Request payload to record an active recall review score."""

    quality_score: int = Field(
        ...,
        ge=0,
        le=5,
        description="SM-2 recall difficulty rating from 0 (Blackout) to 5 (Perfect recall).",
    )
    time_spent_seconds: int = Field(
        default=0,
        ge=0,
        le=1800,
        description="Duration of recall drill in seconds.",
    )


class ReviewSubmitResponse(BaseModel):
    """Response payload returned upon successfully recording an SM-2 review."""

    review_item_id: uuid.UUID
    repetition_count: int
    ease_factor: float
    interval_days: int
    next_due_date: date
    quality_score: int
    status: str
    message: str


class ReviewLogItem(BaseModel):
    """Historical audit entry for a single review attempt."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    review_item_id: uuid.UUID
    topic_id: uuid.UUID
    topic_title: str
    quality_score: int
    time_spent_seconds: int
    scheduled_interval_days: int
    next_interval_days: int
    ease_factor_before: float
    ease_factor_after: float
    reviewed_at: datetime


class ReviewHistoryResponse(BaseModel):
    """Paginated collection of historical review logs."""

    total_count: int
    page: int
    page_size: int
    total_pages: int
    items: List[ReviewLogItem]


class ReviewStatsResponse(BaseModel):
    """Aggregated memory retention statistics for dashboard presentation."""

    total_tracked_topics: int
    due_today_count: int
    mastered_count: int
    average_ease_factor: float
    successful_review_rate_percentage: Optional[float] = Field(
        default=None,
        description="Percentage of reviews scoring 3-5. None if no reviews have been recorded.",
    )
