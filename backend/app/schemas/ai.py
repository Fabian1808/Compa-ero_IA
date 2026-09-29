from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class AIProviderType(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"


class ChatMessage(BaseModel):
    role: str  # system | user | assistant | tool
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str | Dict[str, Any]] = None
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)


class ChatCompletionResponse(BaseModel):
    message: ChatMessage
    finish_reason: str
    usage: Optional[Dict[str, int]] = None


class EmbeddingRequest(BaseModel):
    texts: List[str]


class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    usage: Optional[Dict[str, int]] = None


class AnalyzeEmailRequest(BaseModel):
    email_id: str


class AnalyzeEmailResponse(BaseModel):
    tasks_detected: int
    commitments_detected: int
    deadlines_detected: int
    followups_detected: int


class DailyBriefingRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD


class DailyBriefingResponse(BaseModel):
    commitments_important: int
    tasks_pending: int
    meetings_today: int
    tasks_blocked: int
    emails_require_response: int
    followups_pending: int
    summary: str


class EndOfDayRequest(BaseModel):
    date: Optional[str] = None  # YYYY-MM-DD


class EndOfDayResponse(BaseModel):
    tasks_completed: int
    emails_processed: int
    projects_advanced: int
    pending_open: int
    deadline_tomorrow: int
    followups_pending: int
    summary: str


class WhatAmIForgettingResponse(BaseModel):
    items: List[Dict[str, Any]]
    count: int


class AskAIRequest(BaseModel):
    question: str
    context: Optional[Dict[str, Any]] = None


class AskAIResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    tool_calls: List[Dict[str, Any]] = []


# Commitment schemas
class CommitmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class CommitmentBase(BaseModel):
    description: str
    due_date: Optional[datetime] = None
    confidence_score: int = Field(default=100, ge=0, le=100)
    source_email_id: Optional[str] = None
    related_task_id: Optional[str] = None


class CommitmentCreate(CommitmentBase):
    pass


class CommitmentUpdate(BaseModel):
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[CommitmentStatus] = None
    confidence_score: Optional[int] = Field(default=None, ge=0, le=100)


class CommitmentResponse(CommitmentBase):
    id: str
    user_id: str
    committed_at: datetime
    status: CommitmentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Deadline schemas
class DeadlineResponse(BaseModel):
    id: str
    type: str  # task | commitment
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: str
    status: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    hours_until: Optional[float] = None