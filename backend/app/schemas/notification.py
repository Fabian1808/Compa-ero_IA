from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class NotificationSeverity(str, Enum):
    INFO = "info"
    REMINDER = "reminder"
    IMPORTANT = "important"
    CRITICAL = "critical"


class NotificationType(str, Enum):
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


class NotificationBase(BaseModel):
    type: NotificationType
    severity: NotificationSeverity = NotificationSeverity.INFO
    title: str
    message: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id: str
    user_id: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationSettings(BaseModel):
    enabled: bool = True
    focus_mode_silence_non_critical: bool = True
    daily_briefing_enabled: bool = True
    daily_briefing_hour: int = Field(default=8, ge=0, le=23)
    end_of_day_enabled: bool = True
    end_of_day_hour: int = Field(default=18, ge=0, le=23)
    deadline_reminder_minutes_before: int = Field(default=60, ge=0)
    meeting_reminder_minutes_before: int = Field(default=15, ge=0)