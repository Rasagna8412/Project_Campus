"""Pydantic Schemas for Learning Analytics, Dashboard KPIs, and Recommendations."""

from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict


class ActivityItem(BaseModel):
    """Unified recent learning activity item (practice session or completed lesson)."""

    activity_type: str  # "PRACTICE_SESSION" | "LESSON_COMPLETED"
    id: uuid.UUID
    title: str
    subject_name: Optional[str] = None
    subtitle: str
    timestamp: datetime
    is_completed: bool

    model_config = ConfigDict(from_attributes=True)


class DashboardAnalyticsResponse(BaseModel):
    """High-level student progress and analytics summary KPIs."""

    lessons_completed_count: int
    lessons_in_progress_count: int
    practice_sessions_completed_count: int
    total_questions_answered: int
    total_correct_answers: int
    overall_accuracy_percentage: Optional[float] = None
    total_practice_time_seconds: int
    daily_study_goal_minutes: int
    recent_activity: List[ActivityItem] = []

    model_config = ConfigDict(from_attributes=True)


class TopicPerformanceResponse(BaseModel):
    """Aggregated performance metrics and observed status for a curriculum topic."""

    topic_id: uuid.UUID
    topic_title: str
    topic_number: int
    chapter_title: str
    subject_name: str
    total_attempts: int
    correct_attempts: int
    incorrect_attempts: int
    observed_accuracy_percentage: Optional[float] = None
    completed_sessions_count: int
    last_practiced_at: Optional[datetime] = None
    status_category: str  # "STRONG" | "DEVELOPING" | "NEEDS_REVIEW" | "INSUFFICIENT_DATA"

    model_config = ConfigDict(from_attributes=True)


class LearningRecommendationResponse(BaseModel):
    """Actionable, explainable next-step learning recommendation."""

    type: str  # "RESUME_LESSON" | "REVISE_TOPIC" | "PRACTICE_TOPIC" | "NEXT_LESSON"
    priority: int
    title: str
    reason: str
    target_id: uuid.UUID
    target_title: str
    subject_name: Optional[str] = None
    action_label: str

    model_config = ConfigDict(from_attributes=True)
