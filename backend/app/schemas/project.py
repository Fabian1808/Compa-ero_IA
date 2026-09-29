from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    status: Optional[ProjectStatus] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)


class ProjectResponse(ProjectBase):
    id: str
    user_id: str
    status: ProjectStatus
    progress: int
    detected_automatically: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectProgressResponse(BaseModel):
    project_id: str
    name: str
    progress: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    blocked_tasks: int