"""Student Profile and Onboarding Schemas."""

from datetime import datetime
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class EnrolledSubjectResponse(BaseModel):
    """Enrolled subject representation."""

    id: uuid.UUID
    code: str
    name: str
    display_order: int


class StudentProfileResponse(BaseModel):
    """Authoritative student profile response contract."""

    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    email: str
    target_curriculum_id: Optional[uuid.UUID] = None
    target_curriculum_name: Optional[str] = None
    target_curriculum_code: Optional[str] = None
    grade_stage_id: Optional[uuid.UUID] = None
    grade_stage_name: Optional[str] = None
    grade_stage_code: Optional[str] = None
    target_exam_year: Optional[int] = None
    daily_study_goal_minutes: int
    preferred_language: str
    onboarding_completed: bool
    selected_subjects: List[EnrolledSubjectResponse] = []
    created_at: datetime
    updated_at: datetime


class StudentOnboardingRequest(BaseModel):
    """Payload submitted when a student completes or updates onboarding."""

    target_curriculum_id: uuid.UUID = Field(
        ..., description="Selected curriculum board ID"
    )
    grade_stage_id: uuid.UUID = Field(..., description="Selected grade stage ID")
    target_exam_year: Optional[int] = Field(
        None, ge=2026, le=2035, description="Target board/exam year"
    )
    selected_subject_ids: List[uuid.UUID] = Field(
        ..., min_length=1, max_length=8, description="List of chosen subject IDs"
    )
    daily_study_goal_minutes: int = Field(
        default=120, ge=15, le=720, description="Daily study goal in minutes"
    )
    preferred_language: str = Field(
        default="en", max_length=10, description="Preferred language code"
    )
    complete: bool = Field(
        default=True,
        description="Whether to finalize onboarding or save progress as draft",
    )


class StudentProfileUpdateRequest(BaseModel):
    """Payload for partial updates to study goals and preferences."""

    daily_study_goal_minutes: Optional[int] = Field(None, ge=15, le=720)
    target_exam_year: Optional[int] = Field(None, ge=2026, le=2035)
    preferred_language: Optional[str] = Field(None, max_length=10)
