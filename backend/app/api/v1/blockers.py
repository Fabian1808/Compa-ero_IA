
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.blocker_detection import BlockerDetector

router = APIRouter(prefix="/blockers", tags=["blockers"])


def get_user_id(db: AsyncSession) -> str:
    from app.models.user import User
    user_result = db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id


@router.get("")
async def get_blockers(db: AsyncSession = Depends(get_db)):
    """Get all detected blockers for current user."""
    user_id = get_user_id(db)
    detector = BlockerDetector(db, user_id)
    blockers = await detector.detect_all_blockers()
    return {"blockers": blockers, "count": len(blockers)}


@router.post("/check")
async def run_blocker_check(db: AsyncSession = Depends(get_db)):
    """Manually trigger blocker detection and create notifications."""
    user_id = get_user_id(db)
    detector = BlockerDetector(db, user_id)
    await detector.schedule_blocker_check()
    return {"success": True, "message": "Blocker check completed"}
