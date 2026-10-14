"""Curriculum and Academic Taxonomy Schemas."""

import uuid
from typing import List, Optional
from pydantic import BaseModel


class SubjectResponse(BaseModel):
    """Subject discipline schema."""

    id: uuid.UUID
    grade_stage_id: uuid.UUID
    code: str
    name: str
    icon_url: Optional[str] = None
    display_order: int


class GradeStageResponse(BaseModel):
    """Grade level schema including associated subjects."""

    id: uuid.UUID
    board_id: uuid.UUID
    code: str
    name: str
    display_order: int
    subjects: List[SubjectResponse] = []


class BoardCurriculumResponse(BaseModel):
    """Educational board schema including supported grade levels."""

    id: uuid.UUID
    code: str
    name: str
    country_code: str
    description: Optional[str] = None
    is_active: bool
    grades: List[GradeStageResponse] = []
