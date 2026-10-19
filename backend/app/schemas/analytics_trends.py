"""Pydantic v2 schemas for Student Analytics Trends, Adherence, and Diagnostics."""

from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class DailyPracticeTrendItem(BaseModel):
    """Practice volume and observed accuracy for a single IST calendar day."""

    model_config = ConfigDict(from_attributes=True)

    date: str = Field(..., description="IST calendar date (YYYY-MM-DD)")
    questions_answered: int = Field(default=0, ge=0)
    correct_count: int = Field(default=0, ge=0)
    accuracy_percentage: Optional[float] = Field(
        default=None, description="Null if 0 questions attempted"
    )
    practice_minutes: float = Field(default=0.0, ge=0.0)


class PracticeTrendsResponse(BaseModel):
    """Temporal practice metrics across a 7-day or 14-day window."""

    model_config = ConfigDict(from_attributes=True)

    days_count: int
    start_date: str
    end_date: str
    total_questions_answered: int
    total_correct_count: int
    overall_accuracy_percentage: Optional[float]
    total_practice_minutes: float
    daily_trends: List[DailyPracticeTrendItem]


class DailyPlannerTrendItem(BaseModel):
    """Daily study plan adherence and minute budget tracking."""

    model_config = ConfigDict(from_attributes=True)

    date: str
    day_of_week: str
    is_preferred_day: bool
    has_plan: bool
    planned_minutes: int
    completed_minutes: int
    tasks_count: int
    completed_tasks_count: int
    is_goal_met: bool


class PlannerTrendsResponse(BaseModel):
    """Multi-day study plan adherence and goal consistency summary."""

    model_config = ConfigDict(from_attributes=True)

    daily_study_goal_minutes: int
    days_count: int
    preferred_days_count: int
    goals_met_count: int
    adherence_rate_percentage: Optional[float]
    total_planned_minutes: int
    total_completed_minutes: int
    daily_trends: List[DailyPlannerTrendItem]


class RetentionForecastItem(BaseModel):
    """Count of spaced repetition items maturing on a future date."""

    model_config = ConfigDict(from_attributes=True)

    date: str
    due_count: int


class RetentionTrendsResponse(BaseModel):
    """Memory retention streak, overdue distribution, and 7-day forecast."""

    model_config = ConfigDict(from_attributes=True)

    active_streak_days: int
    last_reviewed_date: Optional[str]
    is_streak_active_today: bool
    due_today_count: int
    overdue_1_to_3_days: int
    overdue_4_plus_days: int
    total_overdue_count: int
    forecast_next_7_days: List[RetentionForecastItem]


class DiagnosticTopicItem(BaseModel):
    """Synthesized mastery diagnosis combining lessons, practice, and spaced recall."""

    model_config = ConfigDict(from_attributes=True)

    topic_id: uuid.UUID
    topic_title: str
    subject_id: uuid.UUID
    subject_name: str
    chapter_title: str
    lesson_status: str = Field(description="COMPLETED, IN_PROGRESS, or NOT_STARTED")
    total_attempts: int
    observed_accuracy_percentage: Optional[float]
    practice_category: str = Field(
        description="INSUFFICIENT_DATA, NEEDS_REVIEW, DEVELOPING, STRONG, or UNPRACTICED"
    )
    review_status: Optional[str] = Field(
        default=None, description="LEARNING, REVIEW, MASTERED, or None"
    )
    review_interval_days: Optional[int] = None
    is_review_overdue: bool = False
    diagnostic_state: str = Field(
        description="CRITICAL_GAP, UNPRACTICED_FOUNDATION, SOLIDIFYING, MASTERED, or NOT_STARTED"
    )
    action_recommendation: str


class DiagnosticMatrixResponse(BaseModel):
    """Aggregate learning gap diagnosis across enrolled topics."""

    model_config = ConfigDict(from_attributes=True)

    total_topics_analyzed: int
    critical_gaps_count: int
    unpracticed_foundations_count: int
    solidifying_count: int
    mastered_count: int
    topics: List[DiagnosticTopicItem]
