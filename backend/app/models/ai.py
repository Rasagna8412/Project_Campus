"""AI Tutor Interactions and Student Subscription Entitlements Models."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class AITutorInteraction(Base):
    """Logs individual conversational turns with the Campus AI Tutor."""

    __tablename__ = "ai_tutor_interactions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    mode: Mapped[str] = mapped_column(
        String(50), default="EXPLAIN", nullable=False
    )
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    tutor_response: Mapped[str] = mapped_column(Text, nullable=False)
    grounding_sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", backref="ai_interactions")
    lesson = relationship("Lesson", backref="ai_interactions")


class StudentSubscription(Base, TimestampMixin):
    """Student subscription tier and daily AI entitlement quota."""

    __tablename__ = "student_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    tier: Mapped[str] = mapped_column(
        String(20), default="FREE", nullable=False
    )  # FREE, PRO
    daily_tutor_quota: Mapped[int] = mapped_column(
        Integer, default=20, nullable=False
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user = relationship("User", backref="subscription", uselist=False)
