"""Pydantic Schemas for Question Bank, Practice Sessions, Answer Evaluation, and Errata."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QuestionOptionResponse(BaseModel):
    """Multiple choice option presented to students."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    option_key: str
    content_latex: str
    display_order: int


class QuestionStudentResponse(BaseModel):
    """Student-facing question representation.

    CRITICAL SECURITY INVARIANT:
    Excludes correct_options, numerical_value, integer_value, and explanation_latex.
    These fields must NEVER be leaked to clients prior to submission.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic_id: uuid.UUID
    lesson_id: Optional[uuid.UUID] = None
    question_type: str
    difficulty: str
    content_latex: str
    hints: Optional[List[str]] = None
    diagram_url: Optional[str] = None
    provenance: Optional[str] = None
    is_verified: bool
    options: List[QuestionOptionResponse] = []


class CreatePracticeSessionRequest(BaseModel):
    """Payload to initiate a new topic or lesson practice session."""

    topic_id: Optional[uuid.UUID] = None
    lesson_id: Optional[uuid.UUID] = None
    limit: int = Field(default=5, ge=1, le=20)
    difficulty: Optional[str] = None


class SubmitAnswerRequest(BaseModel):
    """Payload for submitting an answer to a question."""

    question_id: uuid.UUID
    session_id: Optional[uuid.UUID] = None
    selected_options: Optional[List[str]] = None
    submitted_numerical: Optional[float] = Field(default=None, allow_inf_nan=False)
    submitted_integer: Optional[int] = Field(default=None, strict=True)
    time_spent_seconds: int = Field(default=0, ge=0)


class QuestionEvaluationResponse(BaseModel):
    """Immediate post-submission evaluation and verified educator explanation."""

    model_config = ConfigDict(from_attributes=True)

    question_id: uuid.UUID
    is_correct: bool
    score: float
    correct_options: Optional[List[str]] = None
    correct_numerical: Optional[float] = None
    numerical_tolerance: Optional[float] = None
    correct_integer: Optional[int] = None
    explanation_latex: str
    time_spent_seconds: int


class PracticeSessionResponse(BaseModel):
    """Active practice session metadata and question batch."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    topic_id: Optional[uuid.UUID] = None
    session_type: str
    total_questions: int
    correct_count: int
    is_completed: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    questions: List[QuestionStudentResponse] = []


class PracticeSessionSummaryResponse(BaseModel):
    """Final assessment summary after session completion."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic_id: Optional[uuid.UUID] = None
    total_questions: int
    correct_count: int
    accuracy_percentage: float
    is_completed: bool
    started_at: datetime
    completed_at: Optional[datetime] = None


class CreateErrataRequest(BaseModel):
    """Student errata ticket submission."""

    question_id: uuid.UUID
    issue_type: str = Field(default="TYPO")
    description: str = Field(..., min_length=10, max_length=2000)


class ErrataResponse(BaseModel):
    """Acknowledged student errata ticket."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    issue_type: str
    description: str
    status: str
    created_at: datetime
