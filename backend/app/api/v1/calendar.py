from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.meeting import Meeting
from app.models.account import Account
from app.schemas.ai import DailyBriefingResponse, EndOfDayResponse

router = APIRouter(prefix="/calendar", tags=["calendar"])


def get_user_id(db: AsyncSession) -> str:
    from app.models.user import User
    from sqlalchemy import select
    user_result = db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id


@router.get("/events")
async def list_events(
    start: Optional[str] = Query(None, description="ISO date string"),
    end: Optional[str] = Query(None, description="ISO date string"),
    account_id: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    user_id = get_user_id(db)
    
    # Default to next 30 days
    if start:
        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        except ValueError:
            start_dt = datetime.utcnow()
    else:
        start_dt = datetime.utcnow()
    
    if end:
        try:
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        except ValueError:
            end_dt = start_dt + timedelta(days=30)
    else:
        end_dt = start_dt + timedelta(days=30)
    
    stmt = select(Meeting).where(
        Meeting.account.has(user_id=user_id),
        Meeting.start_at >= start_dt,
        Meeting.end_at <= end_dt
    )
    
    if account_id:
        stmt = stmt.where(Meeting.account_id == account_id)
    
    stmt = stmt.order_by(Meeting.start_at).limit(limit)
    
    result = await db.execute(stmt)
    meetings = result.scalars().all()
    
    return {
        "events": [
            {
                "id": m.id,
                "subject": m.subject,
                "start_at": m.start_at.isoformat(),
                "end_at": m.end_at.isoformat(),
                "location": m.location,
                "is_online": m.is_online,
                "meeting_url": m.meeting_url,
                "attendees": m.attendees_json,
            }
            for m in meetings
        ],
        "count": len(meetings),
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
    }


@router.get("/events/today")
async def get_today_events(db: AsyncSession = Depends(get_db)):
    user_id = get_user_id(db)
    now = datetime.utcnow()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    
    stmt = select(Meeting).where(
        Meeting.account.has(user_id=user_id),
        Meeting.start_at >= day_start,
        Meeting.start_at < day_end
    ).order_by(Meeting.start_at)
    
    result = await db.execute(stmt)
    meetings = result.scalars().all()
    
    return {
        "date": now.strftime("%Y-%m-%d"),
        "events": [
            {
                "id": m.id,
                "subject": m.subject,
                "start_at": m.start_at.isoformat(),
                "end_at": m.end_at.isoformat(),
                "location": m.location,
                "is_online": m.is_online,
                "meeting_url": m.meeting_url,
                "time_until": _format_time_until(m.start_at, now),
            }
            for m in meetings
        ],
        "count": len(meetings),
    }


@router.get("/events/upcoming")
async def get_upcoming_events(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
):
    user_id = get_user_id(db)
    now = datetime.utcnow()
    end = now + timedelta(hours=hours)
    
    stmt = select(Meeting).where(
        Meeting.account.has(user_id=user_id),
        Meeting.start_at >= now,
        Meeting.start_at <= end
    ).order_by(Meeting.start_at).limit(limit)
    
    result = await db.execute(stmt)
    meetings = result.scalars().all()
    
    return {
        "events": [
            {
                "id": m.id,
                "subject": m.subject,
                "start_at": m.start_at.isoformat(),
                "end_at": m.end_at.isoformat(),
                "location": m.location,
                "is_online": m.is_online,
                "meeting_url": m.meeting_url,
                "time_until": _format_time_until(m.start_at, now),
            }
            for m in meetings
        ],
        "count": len(meetings),
    }


@router.get("/events/{event_id}")
async def get_event(event_id: str, db: AsyncSession = Depends(get_db)):
    user_id = get_user_id(db)
    
    stmt = select(Meeting).where(
        Meeting.id == event_id,
        Meeting.account.has(user_id=user_id)
    )
    
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {
        "id": meeting.id,
        "subject": meeting.subject,
        "start_at": meeting.start_at.isoformat(),
        "end_at": meeting.end_at.isoformat(),
        "location": meeting.location,
        "is_online": meeting.is_online,
        "meeting_url": meeting.meeting_url,
        "attendees": meeting.attendees_json,
    }


def _format_time_until(target: datetime, now: datetime) -> str:
    diff = target - now
    if diff.total_seconds() < 0:
        return "En curso"
    
    hours = int(diff.total_seconds() // 3600)
    minutes = int((diff.total_seconds() % 3600) // 60)
    
    if hours > 0:
        return f"En {hours}h {minutes}m"
    return f"En {minutes}m"