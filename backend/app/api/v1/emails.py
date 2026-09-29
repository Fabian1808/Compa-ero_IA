from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
import uuid

from app.database import get_db
from app.models.email import Email, EmailThread
from app.models.account import Account
from app.services.sync_service import SyncService
from app.schemas.email import EmailResponse, EmailSearchRequest

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("", response_model=list[EmailResponse])
async def list_emails(
    account_id: Optional[str] = Query(None),
    thread_id: Optional[str] = Query(None),
    is_processed: Optional[bool] = Query(None),
    is_read: Optional[bool] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Email).order_by(Email.received_at.desc()).limit(limit).offset(offset)

    if account_id:
        stmt = stmt.where(Email.account_id == account_id)
    if thread_id:
        stmt = stmt.where(Email.thread_id == thread_id)
    if is_processed is not None:
        stmt = stmt.where(Email.is_processed == is_processed)
    if is_read is not None:
        stmt = stmt.where(Email.is_read == is_read)

    result = await db.execute(stmt)
    emails = result.scalars().all()
    return emails


@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(email_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Email).where(Email.id == email_id))
    email = result.scalar_one_or_none()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    return email


@router.post("/search")
async def search_emails(request: EmailSearchRequest, db: AsyncSession = Depends(get_db)):
    # Simple text search for now - can be enhanced with vector search later
    stmt = select(Email).where(
        Email.subject.ilike(f"%{request.query}%") | Email.body_preview.ilike(f"%{request.query}%")
    ).order_by(Email.received_at.desc()).limit(request.limit)

    if request.since_days:
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=request.since_days)
        stmt = stmt.where(Email.received_at >= cutoff)

    result = await db.execute(stmt)
    emails = result.scalars().all()

    return {"emails": emails, "count": len(emails)}


@router.post("/{email_id}/process")
async def process_email(email_id: str, db: AsyncSession = Depends(get_db)):
    """Re-process an email with AI."""
    from app.services.ai_service import AIService
    from app.models.account import Account

    result = await db.execute(select(Email).where(Email.id == email_id))
    email = result.scalar_one_or_none()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Get user_id from account
    account_result = await db.execute(select(Account).where(Account.id == email.account_id))
    account = account_result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    ai_service = AIService(db, account.user_id)
    analysis = await ai_service.analyze_email(email_id)

    return analysis


@router.get("/threads/")
async def list_threads(
    account_id: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(EmailThread).order_by(EmailThread.last_message_at.desc()).limit(limit).offset(offset)

    if account_id:
        stmt = stmt.where(EmailThread.account_id == account_id)

    result = await db.execute(stmt)
    threads = result.scalars().all()
    return threads