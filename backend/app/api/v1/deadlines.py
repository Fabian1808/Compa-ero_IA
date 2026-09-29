from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
import uuid

from app.database import get_db
from app.models.task import Task, TaskStatus
from app.models.commitment import Commitment, CommitmentStatus
from app.models.email import Email

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


def get_user_id(db: AsyncSession) -> str:
    from app.models.user import User
    from sqlalchemy import select
    user_result = db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id


@router.get("")
async def list_deadlines(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_user_id(db)
    now = datetime.utcnow()
    end = now + timedelta(days=days)
    
    deadlines = []
    
    # Task deadlines
    stmt = select(Task).where(
        Task.user_id == user_id,
        Task.deadline_at >= now,
        Task.deadline_at <= end,
        Task.status != TaskStatus.COMPLETED
    ).order_by(Task.deadline_at)
    
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    
    for t in tasks:
        deadlines.append({
            "id": f"task-{t.id}",
            "type": "task",
            "title": t.title,
            "description": t.description,
            "deadline": t.deadline_at.isoformat() if t.deadline_at else None,
            "priority": t.priority.value,
            "status": t.status.value,
            "project_id": t.project_id,
            "project_name": t.project.name if t.project else None,
            "source_email_id": t.source_email_id,
        })
    
    # Commitment deadlines
    stmt = select(Commitment).where(
        Commitment.user_id == user_id,
        Commitment.due_date >= now,
        Commitment.due_date <= end,
        Commitment.status.in_([CommitmentStatus.PENDING, CommitmentStatus.CONFIRMED])
    ).order_by(Commitment.due_date)
    
    result = await db.execute(stmt)
    commitments = result.scalars().all()
    
    for c in commitments:
        deadlines.append({
            "id": f"commitment-{c.id}",
            "type": "commitment",
            "title": c.description,
            "description": c.description,
            "deadline": c.due_date.isoformat() if c.due_date else None,
            "priority": "high",
            "status": c.status.value,
            "source_email_id": c.source_email_id,
        })
    
    # Email-detected deadlines (from metadata)
    stmt = select(Email).where(
        Email.account.has(user_id=user_id),
        Email.received_at >= now - timedelta(days=30)
    )
    
    result = await db.execute(stmt)
    emails = result.scalars().all()
    
    # Note: Email deadlines would be in metadata_json, but for now we rely on tasks/commitments
    
    # Sort by deadline
    deadlines.sort(key=lambda x: x["deadline"] or "9999-12-31")
    
    return {"deadlines": deadlines, "count": len(deadlines)}


@router.get("/upcoming")
async def get_upcoming_deadlines(
    hours: int = 48,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_user_id(db)
    now = datetime.utcnow()
    end = now + timedelta(hours=hours)
    
    # Task deadlines
    stmt = select(Task).where(
        Task.user_id == user_id,
        Task.deadline_at >= now,
        Task.deadline_at <= end,
        Task.status != TaskStatus.COMPLETED
    ).order_by(Task.deadline_at).limit(10)
    
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    
    # Commitment deadlines
    stmt = select(Commitment).where(
        Commitment.user_id == user_id,
        Commitment.due_date >= now,
        Commitment.due_date <= end,
        Commitment.status.in_([CommitmentStatus.PENDING, CommitmentStatus.CONFIRMED])
    ).order_by(Commitment.due_date).limit(10)
    
    result = await db.execute(stmt)
    commitments = result.scalars().all()
    
    all_deadlines = []
    
    for t in tasks:
        all_deadlines.append({
            "id": f"task-{t.id}",
            "type": "task",
            "title": t.title,
            "deadline": t.deadline_at.isoformat() if t.deadline_at else None,
            "priority": t.priority.value,
            "hours_until": (t.deadline_at - now).total_seconds() / 3600 if t.deadline_at else None,
        })
    
    for c in commitments:
        all_deadlines.append({
            "id": f"commitment-{c.id}",
            "type": "commitment",
            "title": c.description,
            "deadline": c.due_date.isoformat() if c.due_date else None,
            "priority": "high",
            "hours_until": (c.due_date - now).total_seconds() / 3600 if c.due_date else None,
        })
    
    all_deadlines.sort(key=lambda x: x["deadline"] or "9999-12-31")
    
    return {"deadlines": all_deadlines, "count": len(all_deadlines)}


from datetime import timedelta