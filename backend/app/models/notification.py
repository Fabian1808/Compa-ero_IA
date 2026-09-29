from sqlalchemy import String, DateTime, Text, Enum as SQLEnum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from enum import Enum as PyEnum
from app.database import Base


class NotificationSeverity(str, PyEnum):
    INFO = "info"
    REMINDER = "reminder"
    IMPORTANT = "important"
    CRITICAL = "critical"


class NotificationType(str, PyEnum):
    DEADLINE_APPROACHING = "deadline_approaching"
    MEETING_APPROACHING = "meeting_approaching"
    FOLLOWUP_DUE = "followup_due"
    TASK_BLOCKED = "task_blocked"
    NEW_TASK_DETECTED = "new_task_detected"
    COMMITMENT_DUE = "commitment_due"
    DAILY_BRIEFING = "daily_briefing"
    END_OF_DAY = "end_of_day"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType), nullable=False)
    severity: Mapped[NotificationSeverity] = mapped_column(SQLEnum(NotificationSeverity), default=NotificationSeverity.INFO, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    related_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read"),
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )