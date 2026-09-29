from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from enum import Enum


class EventType(str, Enum):
    # Auth
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGGED_OUT = "user.logged_out"
    TOKEN_REFRESHED = "token.refreshed"

    # Sync
    SYNC_STARTED = "sync.started"
    SYNC_COMPLETED = "sync.completed"
    SYNC_FAILED = "sync.failed"
    EMAILS_SYNCED = "emails.synced"

    # Email processing
    EMAIL_RECEIVED = "email.received"
    EMAIL_PROCESSED = "email.processed"
    TASK_DETECTED = "task.detected"
    COMMITMENT_DETECTED = "commitment.detected"
    DEADLINE_DETECTED = "deadline.detected"
    FOLLOWUP_DETECTED = "followup.detected"
    BLOCKER_DETECTED = "blocker.detected"

    # Task lifecycle
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_BLOCKED = "task.blocked"
    TASK_UNBLOCKED = "task.unblocked"

    # Project
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_PROGRESS_CHANGED = "project.progress_changed"

    # Notifications
    NOTIFICATION_CREATED = "notification.created"
    DAILY_BRIEFING_DUE = "daily_briefing.due"
    END_OF_DAY_DUE = "end_of_day.due"
    DEADLINE_APPROACHING = "deadline.approaching"
    MEETING_APPROACHING = "meeting.approaching"
    FOLLOWUP_DUE = "followup.due"

    # Focus mode
    FOCUS_STARTED = "focus.started"
    FOCUS_PAUSED = "focus.paused"
    FOCUS_COMPLETED = "focus.completed"

    # AI
    AI_RECOMMENDATION_GENERATED = "ai.recommendation_generated"
    AI_CONFIDENCE_LOW = "ai.confidence_low"


@dataclass
class Event:
    type: EventType
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: str | None = None
    correlation_id: str | None = None