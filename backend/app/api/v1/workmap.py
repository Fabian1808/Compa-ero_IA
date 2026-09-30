from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.workmap_service import WorkMapService

router = APIRouter(prefix="/workmap", tags=["workmap"])


def get_user_id(db: AsyncSession) -> str:
    from sqlalchemy import select

    from app.models.user import User
    user_result = db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id


@router.get("")
async def get_work_map(db: AsyncSession = Depends(get_db)):
    """Get complete work map for visualization."""
    user_id = get_user_id(db)
    workmap = WorkMapService(db, user_id)
    data = await workmap.get_work_map()
    return data


@router.get("/project/{project_id}/progress")
async def get_project_progress(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed progress for a specific project."""
    user_id = get_user_id(db)
    workmap = WorkMapService(db, user_id)
    data = await workmap.get_project_progress(project_id)
    return data


@router.get("/bottlenecks")
async def get_bottlenecks(db: AsyncSession = Depends(get_db)):
    """Get identified bottlenecks."""
    user_id = get_user_id(db)
    workmap = WorkMapService(db, user_id)
    data = await workmap.get_work_map()
    return {"bottlenecks": data["bottlenecks"], "count": len(data["bottlenecks"])}
