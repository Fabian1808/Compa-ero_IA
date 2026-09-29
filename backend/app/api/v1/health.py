from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ai_service import AIService

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    return {"status": "healthy"}


@router.get("/health/ai")
async def ai_health_check(db: AsyncSession = Depends(get_db)):
    ai_service = AIService(db, "test")
    healthy = await ai_service.health_check()
    return {"status": "healthy" if healthy else "unhealthy", "provider": "ollama"}