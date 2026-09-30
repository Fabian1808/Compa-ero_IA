from sqlalchemy import String, DateTime, Text, Enum as SQLEnum, ForeignKey, Index, func, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from enum import Enum as PyEnum
from app.database import Base


class TaskStatus(str, PyEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    WAITING_RESPONSE = "waiting_response"
    REQUIRES_DECISION = "requires_decision"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"



class DependencyType(str, PyEnum):
    BLOCKS = "blocks"
    BLOCKED_BY = "blocked_by"
    RELATES_TO = "relates_to"
    DUPLICATES = "duplicates"
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("accounts.id"), nullable=True, index=True)
    source_email_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("emails.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, nullable=False, index=True)
    priority: Mapped[TaskPriority] = mapped_column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    dependencies_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="tasks")
    account: Mapped["Account | None"] = relationship()
    source_email: Mapped["Email | None"] = relationship(back_populates="tasks")
    project: Mapped["Project | None"] = relationship(back_populates="tasks")
    dependencies: Mapped[list["TaskDependency"]] = relationship(
        back_populates="task",
        foreign_keys="TaskDependency.task_id",
        cascade="all, delete-orphan"
    )
    dependents: Mapped[list["TaskDependency"]] = relationship(
        back_populates="depends_on_task",
        foreign_keys="TaskDependency.depends_on_task_id"
    )

    __table_args__ = (
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_user_deadline", "user_id", "deadline_at"),
        Index("ix_tasks_project_status", "project_id", "status"),
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    depends_on_task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    dependency_type: Mapped[str] = mapped_column(String(50), default="blocks", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    task: Mapped["Task"] = relationship(back_populates="dependencies", foreign_keys=[task_id])
    depends_on_task: Mapped["Task"] = relationship(back_populates="dependents", foreign_keys=[depends_on_task_id])

    __table_args__ = (
        Index("ix_task_deps_task_depends", "task_id", "depends_on_task_id", unique=True),
    )
