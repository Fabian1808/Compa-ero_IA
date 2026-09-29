from sqlalchemy import String, DateTime, Text, Enum as SQLEnum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from enum import Enum as PyEnum
from app.database import Base


class FollowUpStatus(str, PyEnum):
    PENDING = "pending"
    REMINDER_SENT = "reminder_sent"
    DRAFT_PREPARED = "draft_prepared"
    SENT = "sent"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


class FollowUp(Base):
    __tablename__ = "followups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_email_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("emails.id"), nullable=True, index=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expected_reply_by: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    status: Mapped[FollowUpStatus] = mapped_column(SQLEnum(FollowUpStatus), default=FollowUpStatus.PENDING, nullable=False)
    reminder_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    draft_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="followups")
    source_email: Mapped["Email | None"] = relationship()

    __table_args__ = (
        Index("ix_followups_user_status", "user_id", "status"),
        Index("ix_followups_expected_reply", "expected_reply_by"),
    )