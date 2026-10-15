"""Academic Curriculum Taxonomy Models."""

import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.content import Lesson
    from app.models.assessment import Question


class BoardCurriculum(Base, TimestampMixin):
    """Educational board or national examination system (e.g., CBSE, JEE Main, NEET)."""

    __tablename__ = "boards_curricula"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    country_code: Mapped[str] = mapped_column(
        String(3), default="IND", nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    # Relationships
    grades: Mapped[List["GradeStage"]] = relationship(
        "GradeStage", back_populates="board", cascade="all, delete-orphan"
    )


class GradeStage(Base, TimestampMixin):
    """Academic grade level or stage within a curriculum (e.g., Class 11, Class 12)."""

    __tablename__ = "grades_stages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    board_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("boards_curricula.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("board_id", "code", name="uq_grade_board_code"),
    )

    # Relationships
    board: Mapped["BoardCurriculum"] = relationship(
        "BoardCurriculum", back_populates="grades"
    )
    subjects: Mapped[List["Subject"]] = relationship(
        "Subject", back_populates="grade", cascade="all, delete-orphan"
    )


class Subject(Base, TimestampMixin):
    """Subject discipline (e.g., Physics, Chemistry, Mathematics, Biology)."""

    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    grade_stage_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("grades_stages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    icon_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("grade_stage_id", "code", name="uq_subject_grade_code"),
    )

    # Relationships
    grade: Mapped["GradeStage"] = relationship(
        "GradeStage", back_populates="subjects"
    )
    chapters: Mapped[List["Chapter"]] = relationship(
        "Chapter", back_populates="subject", cascade="all, delete-orphan"
    )


class Chapter(Base, TimestampMixin):
    """Curriculum chapter unit within a subject."""

    __tablename__ = "chapters"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "subject_id", "chapter_number", name="uq_chapter_subject_num"
        ),
    )

    # Relationships
    subject: Mapped["Subject"] = relationship(
        "Subject", back_populates="chapters"
    )
    topics: Mapped[List["Topic"]] = relationship(
        "Topic", back_populates="chapter", cascade="all, delete-orphan"
    )


class Topic(Base, TimestampMixin):
    """Granular learning topic or concept within a chapter."""

    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chapter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    importance_weight: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )
    display_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "chapter_id", "topic_number", name="uq_topic_chapter_num"
        ),
    )

    # Relationships
    chapter: Mapped["Chapter"] = relationship(
        "Chapter", back_populates="topics"
    )
    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson",
        back_populates="topic",
        cascade="all, delete-orphan",
        order_by="Lesson.display_order",
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="topic",
        cascade="all, delete-orphan",
    )
