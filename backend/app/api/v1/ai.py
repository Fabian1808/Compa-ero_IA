from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.services.ai_service import AIService
from app.schemas.ai import (
    AnalyzeEmailRequest,
    AnalyzeEmailResponse,
    DailyBriefingRequest,
    DailyBriefingResponse,
    EndOfDayRequest,
    EndOfDayResponse,
    WhatAmIForgettingResponse,
    AskAIRequest,
    AskAIResponse,
)

router = APIRouter(prefix="/ai", tags=["ai"])


def get_user_id(db: AsyncSession) -> str:
    """Get first user ID - in production would come from auth."""
    from app.models.user import User
    from sqlalchemy import select
    user_result = db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id


@router.post("/analyze-email", response_model=AnalyzeEmailResponse)
async def analyze_email(request: AnalyzeEmailRequest, db: AsyncSession = Depends(get_db)):
    user_id = get_user_id(db)
    ai_service = AIService(db, user_id)
    result = await ai_service.analyze_email(request.email_id)

    return AnalyzeEmailResponse(
        tasks_detected=result.get("tasks_detected", 0),
        commitments_detected=result.get("commitments_detected", 0),
        deadlines_detected=result.get("deadlines_detected", 0),
        followups_detected=result.get("followups_detected", 0),
    )


@router.post("/daily-briefing", response_model=DailyBriefingResponse)
async def daily_briefing(request: DailyBriefingRequest, db: AsyncSession = Depends(get_db)):
    user_id = get_user_id(db)
    ai_service = AIService(db, user_id)
    
    date = None
    if request.date:
        try:
            date = datetime.fromisoformat(request.date)
        except ValueError:
            pass
    
    result = await ai_service.generate_daily_briefing(date)
    
    return DailyBriefingResponse(
        commitments_important=result.get("commitments_important", 0),
        tasks_pending=result.get("tasks_pending", 0),
        meetings_today=result.get("meetings_today", 0),
        tasks_blocked=result.get("tasks_blocked", 0),
        emails_require_response=result.get("emails_require_response", 0),
        followups_pending=result.get("followups_pending", 0),
        summary=result.get("summary", ""),
    )


@router.post("/end-of-day", response_model=EndOfDayResponse)
async def end_of_day(request: EndOfDayRequest, db: AsyncSession = Depends(get_db)):
    user_id = get_user_id(db)
    ai_service = AIService(db, user_id)
    
    date = None
    if request.date:
        try:
            date = datetime.fromisoformat(request.date)
        except ValueError:
            pass
    
    result = await ai_service.generate_end_of_day(date)
    
    return EndOfDayResponse(
        tasks_completed=result.get("tasks_completed", 0),
        emails_processed=result.get("emails_processed", 0),
        projects_advanced=result.get("projects_advanced", 0),
        pending_open=result.get("pending_open", 0),
        deadline_tomorrow=result.get("deadline_tomorrow", 0),
        followups_pending=result.get("followups_pending", 0),
        summary=result.get("summary", ""),
    )


@router.post("/what-am-i-forgetting", response_model=WhatAmIForgettingResponse)
async def what_am_i_forgetting(db: AsyncSession = Depends(get_db)):
    user_id = get_user_id(db)
    ai_service = AIService(db, user_id)
    result = await ai_service.what_am_i_forgetting()
    
    return WhatAmIForgettingResponse(
        items=result.get("items", []),
        count=result.get("count", 0),
    )


@router.post("/ask", response_model=AskAIResponse)
async def ask_ai(request: AskAIRequest, db: AsyncSession = Depends(get_db)):
    user_id = get_user_id(db)
    ai_service = AIService(db, user_id)
    result = await ai_service.chat_with_tools(request.question, request.context)
    
    return AskAIResponse(
        answer=result.get("answer", ""),
        sources=[],
        tool_calls=result.get("tool_calls", []),
    )


@router.get("/health")
async def ai_health_check(db: AsyncSession = Depends(get_db)):
    user_id = get_user_id(db)
    ai_service = AIService(db, user_id)
    healthy = await ai_service.health_check()
    return {"status": "healthy" if healthy else "unhealthy", "provider": "ollama"}