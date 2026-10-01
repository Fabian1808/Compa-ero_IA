from sqlalchemy import String, DateTime, Text, Enum as SQLEnum, ForeignKey, Index, func, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from enum import Enum as PyEnum
from app.database import Base


class CommitmentStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Commitment(Base):
    __tablename__ = "commitments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_email_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("emails.id"), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    committed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[CommitmentStatus] = mapped_column(SQLEnum(CommitmentStatus), default=CommitmentStatus.PENDING, nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    related_task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="commitments")
    source_email: Mapped["Email | None"] = relationship()
    related_task: Mapped["Task | None"] = relationship()

    __table_args__ = (
        Index("ix_commitments_user_status", "user_id", "status"),
        Index("ix_commitments_due_date", "due_date"),
    )