from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class EmailImportance(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class EmailBase(BaseModel):
    graph_id: str
    subject: str
    body_preview: Optional[str] = None
    body_text: Optional[str] = None
    sender_email: EmailStr
    sender_name: Optional[str] = None
    recipients_json: str = "[]"
    received_at: datetime
    has_attachments: bool = False
    importance: EmailImportance = EmailImportance.NORMAL
    categories_json: str = "[]"
    is_read: bool = False


class EmailCreate(EmailBase):
    account_id: str
    thread_id: Optional[str] = None


class EmailUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_processed: Optional[bool] = None


class EmailResponse(EmailBase):
    id: str
    account_id: str
    thread_id: Optional[str] = None
    is_processed: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailSearchRequest(BaseModel):
    query: str
    limit: int = 10
    since_days: Optional[int] = None


class EmailProcessRequest(BaseModel):
    email_id: str