"""Spaced Repetition Models: Review Items and Review History Logs."""

from datetime import date, datetime, timezone
import enum
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.identity import User
    from app.models.taxonomy import Subject, Topic


class ReviewStatus(str, enum.Enum):
    """Lifecycle status of a student's retention tracking for a topic."""

    LEARNING = "LEARNING"
    REVIEW = "REVIEW"
    MASTERED = "MASTERED"


class ReviewItem(Base, TimestampMixin):
    """Active spaced repetition tracking state for a student on an academic topic."""

    __tablename__ = "review_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repetition_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    ease_factor: Mapped[float] = mapped_column(
        Float, default=2.50, nullable=False
    )
    interval_days: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    due_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default=ReviewStatus.LEARNING.value, nullable=False, index=True
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_review_items_user_topic"),
        Index("idx_review_items_user_due", "user_id", "due_date", "status"),
        Index("idx_review_items_user_subject", "user_id", "subject_id"),
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    topic: Mapped["Topic"] = relationship("Topic")
    subject: Mapped["Subject"] = relationship("Subject")
    logs: Mapped[List["ReviewLog"]] = relationship(
        "ReviewLog",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="ReviewLog.reviewed_at.desc()",
    )


class ReviewLog(Base):
    """Immutable audit and analytics record of an individual recall review attempt."""

    __tablename__ = "review_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    review_item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("review_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    scheduled_interval_days: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    next_interval_days: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    ease_factor_before: Mapped[float] = mapped_column(Float, nullable=False)
    ease_factor_after: Mapped[float] = mapped_column(Float, nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_review_logs_user_reviewed", "user_id", "reviewed_at"),
    )

    # Relationships
    item: Mapped["ReviewItem"] = relationship("ReviewItem", back_populates="logs")
    user: Mapped["User"] = relationship("User")
