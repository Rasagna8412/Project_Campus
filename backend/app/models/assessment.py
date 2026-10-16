"""Question Bank, Evaluation Engine, Practice Sessions, and Errata Models."""

import enum
import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import (
    Boolean,
    Float,
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
from app.models.content import ContentStatus

if TYPE_CHECKING:
    from app.models.taxonomy import Topic
    from app.models.content import Lesson
    from app.models.identity import User


class QuestionType(str, enum.Enum):
    """Categorization of supported assessment questions."""

    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    NUMERICAL = "NUMERICAL"
    INTEGER = "INTEGER"


class DifficultyLevel(str, enum.Enum):
    """Pedagogical difficulty rating."""

    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    EXPERT = "EXPERT"


class ErrataIssueType(str, enum.Enum):
    """Classification of student-reported question issues."""

    INCORRECT_ANSWER = "INCORRECT_ANSWER"
    TYPO = "TYPO"
    AMBIGUOUS_QUESTION = "AMBIGUOUS_QUESTION"
    MISSING_DIAGRAM = "MISSING_DIAGRAM"
    OTHER = "OTHER"


class Question(Base, TimestampMixin):
    """Authoritative question entity in the Question Bank."""

    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    question_type: Mapped[str] = mapped_column(
        String(30), default=QuestionType.SINGLE_CHOICE.value, nullable=False
    )
    difficulty: Mapped[str] = mapped_column(
        String(20), default=DifficultyLevel.MEDIUM.value, nullable=False, index=True
    )
    content_latex: Mapped[str] = mapped_column(Text, nullable=False)
    hints: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    diagram_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=ContentStatus.DRAFT.value, nullable=False, index=True
    )
    provenance: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    topic: Mapped["Topic"] = relationship("Topic", back_populates="questions")
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson", back_populates="questions")
    options: Mapped[List["QuestionOption"]] = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="QuestionOption.display_order",
        lazy="selectin",
    )
    answer_key: Mapped[Optional["QuestionAnswerKey"]] = relationship(
        "QuestionAnswerKey",
        back_populates="question",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )
    attempts: Mapped[List["QuestionAttempt"]] = relationship(
        "QuestionAttempt",
        back_populates="question",
        cascade="all, delete-orphan",
    )
    errata_reports: Mapped[List["QuestionErrataReport"]] = relationship(
        "QuestionErrataReport",
        back_populates="question",
        cascade="all, delete-orphan",
    )


class QuestionOption(Base, TimestampMixin):
    """Answer choice for Multiple Choice (Single/Multi-select) questions."""

    __tablename__ = "question_options"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    option_key: Mapped[str] = mapped_column(String(10), nullable=False)
    content_latex: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("question_id", "option_key", name="uq_question_option_key"),
    )

    # Relationships
    question: Mapped["Question"] = relationship("Question", back_populates="options")


class QuestionAnswerKey(Base, TimestampMixin):
    """Secure educator answer key and step-by-step verified derivation.

    CRITICAL: Never serialize directly on student question retrieval endpoints.
    Only queried server-side for answer evaluation and returned upon submission.
    """

    __tablename__ = "question_answer_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    correct_options: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # e.g., ["A"] or ["A", "C"]
    numerical_value: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    numerical_tolerance: Mapped[Optional[float]] = mapped_column(
        Float, default=0.01, nullable=True
    )
    integer_value: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    explanation_latex: Mapped[str] = mapped_column(Text, nullable=False)
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    question: Mapped["Question"] = relationship("Question", back_populates="answer_key")


class PracticeSession(Base, TimestampMixin):
    """Interactive topic practice session container."""

    __tablename__ = "practice_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    session_type: Mapped[str] = mapped_column(
        String(50), default="TOPIC_PRACTICE", nullable=False
    )
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    topic: Mapped[Optional["Topic"]] = relationship("Topic")
    attempts: Mapped[List["QuestionAttempt"]] = relationship(
        "QuestionAttempt",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="QuestionAttempt.attempted_at",
        lazy="selectin",
    )


class QuestionAttempt(Base):
    """Atomic record of an answer submission by a student."""

    __tablename__ = "question_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    selected_options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    submitted_numerical: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    submitted_integer: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    session: Mapped[Optional["PracticeSession"]] = relationship(
        "PracticeSession", back_populates="attempts"
    )
    user: Mapped["User"] = relationship("User")
    question: Mapped["Question"] = relationship("Question", back_populates="attempts")


class QuestionErrataReport(Base, TimestampMixin):
    """Student feedback and errata ticket for pedagogical review."""

    __tablename__ = "question_errata_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issue_type: Mapped[str] = mapped_column(
        String(50), default=ErrataIssueType.TYPO.value, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)

    # Relationships
    question: Mapped["Question"] = relationship("Question", back_populates="errata_reports")
    user: Mapped["User"] = relationship("User")
