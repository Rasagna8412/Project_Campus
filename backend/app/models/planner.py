"""Study Planner, Goals, Daily Study Tasks, and Learning Roadmap Models."""

import enum
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.identity import User
    from app.models.taxonomy import Subject, Chapter, Topic
    from app.models.content import Lesson


class GoalStatus(str, enum.Enum):
    """Lifecycle status for a student's study goal."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class TaskType(str, enum.Enum):
    """Categorization of supported daily study tasks."""

    STUDY_LESSON = "STUDY_LESSON"
    RESUME_LESSON = "RESUME_LESSON"
    PRACTICE_TOPIC = "PRACTICE_TOPIC"
    REVISE_TOPIC = "REVISE_TOPIC"


class TaskStatus(str, enum.Enum):
    """Lifecycle status for an individual daily scheduled study task."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    RESCHEDULED = "RESCHEDULED"


class StudyGoal(Base, TimestampMixin):
    """Target academic preparation goal and time commitment for a student."""

    __tablename__ = "study_goals"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(150), default="Academic Preparation", nullable=False
    )
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    daily_study_minutes: Mapped[int] = mapped_column(
        Integer, default=120, nullable=False
    )
    preferred_days: Mapped[list] = mapped_column(
        JSON,
        default=lambda: ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), default=GoalStatus.ACTIVE.value, nullable=False, index=True
    )

    __table_args__ = (
        Index("idx_study_goals_user_status", "user_id", "status"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    tasks: Mapped[List["StudyTask"]] = relationship(
        "StudyTask",
        back_populates="goal",
        cascade="all, delete-orphan",
    )


class StudyTask(Base, TimestampMixin):
    """Granular daily scheduled study activity."""

    __tablename__ = "study_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    goal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("study_goals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scheduled_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(
        String(30), default=TaskType.STUDY_LESSON.value, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
    )
    subject_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    chapter_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
    )
    lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
    )
    estimated_minutes: Mapped[int] = mapped_column(
        Integer, default=15, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default=TaskStatus.PENDING.value, nullable=False
    )
    is_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    display_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    __table_args__ = (
        Index("idx_study_tasks_user_date", "user_id", "scheduled_date"),
        Index("idx_study_tasks_user_status", "user_id", "is_completed"),
        Index(
            "idx_study_tasks_lookup",
            "user_id",
            "scheduled_date",
            "is_completed",
        ),
        UniqueConstraint(
            "user_id",
            "scheduled_date",
            "display_order",
            name="uq_study_tasks_user_date_order",
        ),
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    goal: Mapped[Optional["StudyGoal"]] = relationship(
        "StudyGoal", back_populates="tasks"
    )
    subject: Mapped[Optional["Subject"]] = relationship("Subject")
    chapter: Mapped[Optional["Chapter"]] = relationship("Chapter")
    topic: Mapped[Optional["Topic"]] = relationship("Topic")
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson")
