from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    WAITING_RESPONSE = "waiting_response"
    REQUIRES_DECISION = "requires_decision"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_minutes: Optional[int] = Field(default=None, ge=0)
    deadline_at: Optional[datetime] = None
    project_id: Optional[str] = None
    source_email_id: Optional[str] = None
    metadata_json: str = "{}"


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    estimated_minutes: Optional[int] = Field(default=None, ge=0)
    actual_minutes: Optional[int] = Field(default=None, ge=0)
    deadline_at: Optional[datetime] = None
    project_id: Optional[str] = None
    dependencies_json: Optional[str] = None
    metadata_json: Optional[str] = None


class TaskResponse(TaskBase):
    id: str
    user_id: str
    account_id: Optional[str] = None
    status: TaskStatus
    confidence_score: int
    actual_minutes: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies_json: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskCompleteRequest(BaseModel):
    actual_minutes: Optional[int] = Field(default=None, ge=0)


class TaskStartFocusRequest(BaseModel):
    pass


class TaskRecommendationRequest(BaseModel):
    available_minutes: Optional[int] = None
    exclude_project_ids: list[str] = []


class TaskRecommendationResponse(BaseModel):
    task_id: Optional[str] = None
    title: str
    reasoning: str
    estimated_minutes: Optional[int] = None
    deadline_at: Optional[datetime] = None
    confidence: int