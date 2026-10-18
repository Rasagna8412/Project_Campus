"""Pydantic v2 Schemas for Study Goals, Daily Tasks, and Curriculum Roadmap."""

from datetime import date, datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class StudyGoalCreateRequest(BaseModel):
    """Payload to create or update a student's active study goal."""

    title: Optional[str] = Field("Academic Preparation", max_length=150)
    target_date: Optional[date] = None
    daily_study_minutes: int = Field(120, ge=15, le=300)
    preferred_days: Optional[List[str]] = Field(
        default=["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    )


class StudyGoalResponse(BaseModel):
    """Serialized study goal metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    target_date: Optional[date] = None
    daily_study_minutes: int
    preferred_days: List[str]
    status: str
    created_at: datetime
    updated_at: datetime


class StudyTaskResponse(BaseModel):
    """Serialized daily scheduled study task item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    goal_id: Optional[uuid.UUID] = None
    scheduled_date: date
    task_type: str
    title: str
    subject_id: Optional[uuid.UUID] = None
    subject_name: Optional[str] = None
    chapter_id: Optional[uuid.UUID] = None
    topic_id: Optional[uuid.UUID] = None
    lesson_id: Optional[uuid.UUID] = None
    estimated_minutes: int
    status: str
    is_completed: bool
    completed_at: Optional[datetime] = None
    display_order: int
    reason: Optional[str] = None


class DailyStudyPlanResponse(BaseModel):
    """Aggregated daily study plan with task list and workload summary."""

    date: date
    target_minutes: int
    planned_minutes: int
    completed_minutes: int
    is_fully_completed: bool
    tasks: List[StudyTaskResponse]


class TaskCompleteRequest(BaseModel):
    """Payload to toggle a study task completion."""

    is_completed: bool


class TaskRescheduleRequest(BaseModel):
    """Payload to reschedule a study task to another calendar date."""

    new_date: date


class ChapterRoadmapItem(BaseModel):
    """Chapter-level curriculum progress item."""

    chapter_id: uuid.UUID
    chapter_number: int
    title: str
    total_lessons: int
    completed_lessons: int
    is_completed: bool


class SubjectRoadmapItem(BaseModel):
    """Subject-level curriculum progress item with nested chapter progression."""

    subject_id: uuid.UUID
    subject_name: str
    total_lessons: int
    completed_lessons: int
    in_progress_lessons: int
    completion_percentage: float
    chapters: List[ChapterRoadmapItem]


class CurriculumRoadmapResponse(BaseModel):
    """Macroscopic curriculum syllabus progression across all enrolled subjects."""

    total_lessons_count: int
    completed_lessons_count: int
    overall_completion_percentage: float
    subjects: List[SubjectRoadmapItem]
