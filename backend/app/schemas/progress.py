"""Pydantic Schemas for Lesson Progress and Study Completion."""

from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


class LessonProgressResponse(BaseModel):
    """Schema for individual student lesson progress."""

    id: uuid.UUID
    user_id: uuid.UUID
    lesson_id: uuid.UUID
    topic_id: Optional[uuid.UUID] = None
    lesson_title: Optional[str] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    last_accessed_at: datetime

    model_config = ConfigDict(from_attributes=True)
