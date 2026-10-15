"""Structured Academic Lesson and Content Section Models."""

import enum
import uuid
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ContentStatus(str, enum.Enum):
    """Publication lifecycle status for educational content."""

    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class SectionType(str, enum.Enum):
    """Categorization of lesson sections for structured pedagogical rendering."""

    CONCEPT = "CONCEPT"
    WORKED_EXAMPLE = "WORKED_EXAMPLE"
    KEY_FORMULA = "KEY_FORMULA"
    NOTE = "NOTE"


class Lesson(Base, TimestampMixin):
    """Structured educational lesson attached to a specific curriculum topic."""

    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    learning_objectives: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True, default=list
    )
    estimated_read_time_minutes: Mapped[int] = mapped_column(
        Integer, default=10, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default=ContentStatus.DRAFT.value, nullable=False, index=True
    )
    display_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    provenance: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("topic_id", "slug", name="uq_lesson_topic_slug"),
    )

    # Relationships
    topic: Mapped["Topic"] = relationship(
        "Topic", back_populates="lessons"
    )
    sections: Mapped[List["LessonSection"]] = relationship(
        "LessonSection",
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="LessonSection.display_order",
        lazy="selectin",
    )


class LessonSection(Base, TimestampMixin):
    """Ordered content block or pedagogical section within a structured lesson."""

    __tablename__ = "lesson_sections"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    section_type: Mapped[str] = mapped_column(
        String(50), default=SectionType.CONCEPT.value, nullable=False
    )
    display_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "lesson_id", "section_number", name="uq_lesson_section_num"
        ),
    )

    # Relationships
    lesson: Mapped["Lesson"] = relationship(
        "Lesson", back_populates="sections"
    )
