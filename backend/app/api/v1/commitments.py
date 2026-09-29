from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
import uuid

from app.database import get_db
from app.models.commitment import Commitment, CommitmentStatus
from app.models.email import Email
from app.schemas.ai import CommitmentResponse, CommitmentCreate, CommitmentUpdate

router = APIRouter(prefix="/commitments", tags=["commitments"])


def get_user_id(db: AsyncSession) -> str:
    from app.models.user import User
    from sqlalchemy import select
    user_result = db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id


@router.get("")
async def list_commitments(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_user_id(db)
    
    stmt = select(Commitment).where(Commitment.user_id == user_id)
    
    if status:
        stmt = stmt.where(Commitment.status == CommitmentStatus(status))
    
    stmt = stmt.order_by(Commitment.due_date.nulls_last(), Commitment.created_at.desc())
    
    result = await db.execute(stmt)
    commitments = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "description": c.description,
            "committed_at": c.committed_at.isoformat(),
            "due_date": c.due_date.isoformat() if c.due_date else None,
            "status": c.status.value,
            "confidence_score": c.confidence_score,
            "source_email_id": c.source_email_id,
            "related_task_id": c.related_task_id,
            "created_at": c.created_at.isoformat(),
        }
        for c in commitments
    ]


@router.post("")
async def create_commitment(
    data: CommitmentCreate,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_user_id(db)
    
    commitment = Commitment(
        id=str(uuid.uuid4()),
        user_id=user_id,
        description=data.description,
        committed_at=datetime.utcnow(),
        due_date=data.due_date,
        status=CommitmentStatus.PENDING,
        confidence_score=data.confidence_score or 100,
        source_email_id=data.source_email_id,
        related_task_id=data.related_task_id,
    )
    
    db.add(commitment)
    await db.flush()
    await db.refresh(commitment)
    
    return {
        "id": commitment.id,
        "description": commitment.description,
        "committed_at": commitment.committed_at.isoformat(),
        "due_date": commitment.due_date.isoformat() if commitment.due_date else None,
        "status": commitment.status.value,
        "confidence_score": commitment.confidence_score,
    }


@router.patch("/{commitment_id}")
async def update_commitment(
    commitment_id: str,
    data: CommitmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_user_id(db)
    
    stmt = select(Commitment).where(Commitment.id == commitment_id, Commitment.user_id == user_id)
    result = await db.execute(stmt)
    commitment = result.scalar_one_or_none()
    
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(commitment, key, value)
    
    await db.flush()
    await db.refresh(commitment)
    
    return {
        "id": commitment.id,
        "description": commitment.description,
        "due_date": commitment.due_date.isoformat() if commitment.due_date else None,
        "status": commitment.status.value,
    }


@router.post("/{commitment_id}/complete")
async def complete_commitment(commitment_id: str, db: AsyncSession = Depends(get_db)):
    user_id = get_user_id(db)
    
    stmt = select(Commitment).where(Commitment.id == commitment_id, Commitment.user_id == user_id)
    result = await db.execute(stmt)
    commitment = result.scalar_one_or_none()
    
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    commitment.status = CommitmentStatus.COMPLETED
    await db.flush()
    
    return {"success": True}


@router.delete("/{commitment_id}")
async def delete_commitment(commitment_id: str, db: AsyncSession = Depends(get_db)):
    user_id = get_user_id(db)
    
    stmt = select(Commitment).where(Commitment.id == commitment_id, Commitment.user_id == user_id)
    result = await db.execute(stmt)
    commitment = result.scalar_one_or_none()
    
    if not commitment:
        raise HTTPException(status_code=404, detail="Commitment not found")
    
    await db.delete(commitment)
    await db.flush()
    
    return {"success": True}