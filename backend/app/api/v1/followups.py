from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

from app.database import get_db
from app.models.followup import FollowUp, FollowUpStatus
from app.models.email import Email
from app.services.ai_service import AIService

router = APIRouter(prefix="/followups", tags=["followups"])


@router.get("")
async def list_followups(
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import User
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        return []

    stmt = select(FollowUp).where(FollowUp.user_id == user.id)

    if status:
        stmt = stmt.where(FollowUp.status == FollowUpStatus(status))

    stmt = stmt.order_by(FollowUp.created_at.desc())

    result = await db.execute(stmt)
    followups = result.scalars().all()
    return followups


@router.post("/{followup_id}/prepare")
async def prepare_followup(followup_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FollowUp).where(FollowUp.id == followup_id))
    followup = result.scalar_one_or_none()

    if not followup:
        raise HTTPException(status_code=404, detail="Followup not found")

    # Get original email for context
    original_email = None
    if followup.source_email_id:
        email_result = await db.execute(select(Email).where(Email.id == followup.source_email_id))
        original_email = email_result.scalar_one_or_none()

    # Generate draft using AI
    from app.models.user import User
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ai_service = AIService(db, user.id)

    draft_prompt = f"""Escribe un correo de seguimiento amable y profesional.

Contexto:
- Correo original: {original_email.subject if original_email else 'No disponible'}
- Destinatario: {followup.contact_name or followup.contact_email}
- Asunto original: {followup.subject}
- Días sin respuesta: {(datetime.utcnow() - followup.sent_at).days}

El correo debe ser breve, cortés y recordar la solicitud original sin ser insistente."""

    messages = [
        {"role": "system", "content": "Eres un asistente que escribe correos de seguimiento profesionales."},
        {"role": "user", "content": draft_prompt},
    ]

    response = await ai_service.provider.chat_completion(
        [{"role": m["role"], "content": m["content"]} for m in messages]
    )

    draft_body = response.message.content or ""

    followup.draft_response = draft_body
    followup.status = FollowUpStatus.DRAFT_PREPARED
    await db.flush()

    return {
        "draft": {
            "to": followup.contact_email,
            "subject": f"Re: {followup.subject}",
            "body": draft_body,
        }
    }


@router.post("/{followup_id}/dismiss")
async def dismiss_followup(followup_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FollowUp).where(FollowUp.id == followup_id))
    followup = result.scalar_one_or_none()

    if not followup:
        raise HTTPException(status_code=404, detail="Followup not found")

    followup.status = FollowUpStatus.DISMISSED
    await db.flush()
    return {"success": True}


@router.post("/detect")
async def detect_followups(db: AsyncSession = Depends(get_db)):
    from app.models.user import User
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ai_service = AIService(db, user.id)
    result = await ai_service.detect_followups()

    return result


from app.models.user import User
from app.models.email import Email
from fastapi import HTTPException