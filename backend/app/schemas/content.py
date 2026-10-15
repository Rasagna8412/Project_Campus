"""Content and Lesson Schemas for Milestone 3."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class LessonSectionResponse(BaseModel):
    """Schema for individual structured lesson sections."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_id: uuid.UUID
    section_number: int
    title: str
    content_markdown: str
    section_type: str
    display_order: int


class LessonSummaryResponse(BaseModel):
    """Schema for topic lesson summary listing."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    topic_id: uuid.UUID
    title: str
    slug: str
    summary: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    estimated_read_time_minutes: int
    status: str
    display_order: int
    provenance: Optional[str] = None
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class LessonDetailResponse(LessonSummaryResponse):
    """Schema for full lesson content with ordered sections."""

    sections: List[LessonSectionResponse] = []


class TopicResponse(BaseModel):
    """Schema for curriculum topic."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    chapter_id: uuid.UUID
    topic_number: int
    title: str
    slug: str
    importance_weight: int
    display_order: int
    published_lessons_count: int = 0


class ChapterResponse(BaseModel):
    """Schema for subject chapter with nested topics."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_id: uuid.UUID
    chapter_number: int
    title: str
    slug: str
    summary: Optional[str] = None
    display_order: int
    topics: List[TopicResponse] = []
