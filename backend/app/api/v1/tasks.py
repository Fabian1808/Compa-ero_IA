from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import Optional
import uuid

from app.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority, TaskDependency
from app.models.project import Project
from app.services.ai_service import AIService
from app.schemas.task import (
    TaskResponse,
    TaskCreate,
    TaskUpdate,
    TaskCompleteRequest,
    TaskRecommendationRequest,
    TaskRecommendationResponse,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status: Optional[list[TaskStatus]] = Query(None),
    project_id: Optional[str] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    # Get user_id from auth - for now use first user
    from app.models.user import User
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        return []

    stmt = select(Task).where(Task.user_id == user.id)

    if status:
        stmt = stmt.where(Task.status.in_(status))
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    if priority:
        stmt = stmt.where(Task.priority == priority)

    stmt = stmt.order_by(
        Task.deadline_at.nulls_last(),
        Task.priority.desc(),
        Task.created_at
    ).limit(limit).offset(offset)

    result = await db.execute(stmt)
    tasks = result.scalars().all()
    return tasks


@router.get("/stats")
async def get_task_stats(db: AsyncSession = Depends(get_db)):
    from app.models.user import User
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        return {"completed_today": 0, "pending": 0, "in_progress": 0, "blocked": 0}

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Completed today
    completed_result = await db.execute(select(func.count(Task.id)).where(
        Task.user_id == user.id,
        Task.status == TaskStatus.COMPLETED,
        Task.completed_at >= today_start
    ))
    completed_today = completed_result.scalar() or 0

    # Pending
    pending_result = await db.execute(select(func.count(Task.id)).where(
        Task.user_id == user.id,
        Task.status == TaskStatus.PENDING
    ))
    pending = pending_result.scalar() or 0

    # In progress
    in_progress_result = await db.execute(select(func.count(Task.id)).where(
        Task.user_id == user.id,
        Task.status == TaskStatus.IN_PROGRESS
    ))
    in_progress = in_progress_result.scalar() or 0

    # Blocked
    blocked_result = await db.execute(select(func.count(Task.id)).where(
        Task.user_id == user.id,
        Task.status == TaskStatus.BLOCKED
    ))
    blocked = blocked_result.scalar() or 0

    return {
        "completed_today": completed_today,
        "pending": pending,
        "in_progress": in_progress,
        "blocked": blocked,
    }


@router.post("", response_model=TaskResponse)
async def create_task(task_data: TaskCreate, db: AsyncSession = Depends(get_db)):
    from app.models.user import User
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    task = Task(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        estimated_minutes=task_data.estimated_minutes,
        deadline_at=task_data.deadline_at,
        project_id=task_data.project_id,
        source_email_id=task_data.source_email_id,
        metadata_json=task_data.metadata_json,
        status=TaskStatus.PENDING,
        confidence_score=100,
    )

    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_data: TaskUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.flush()
    await db.refresh(task)
    return task


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(task_id: str, request: TaskCompleteRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    if request.actual_minutes is not None:
        task.actual_minutes = request.actual_minutes

    await db.flush()
    await db.refresh(task)
    return task


@router.post("/{task_id}/start", response_model=TaskResponse)
async def start_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = TaskStatus.IN_PROGRESS
    task.started_at = datetime.utcnow()

    await db.flush()
    await db.refresh(task)
    return task


@router.post("/{task_id}/block", response_model=TaskResponse)
async def block_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = TaskStatus.BLOCKED
    await db.flush()
    await db.refresh(task)
    return task


@router.post("/{task_id}/unblock", response_model=TaskResponse)
async def unblock_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = TaskStatus.PENDING
    await db.flush()
    await db.refresh(task)
    return task


@router.post("/recommend-next", response_model=TaskRecommendationResponse)
async def recommend_next_task(request: TaskRecommendationRequest, db: AsyncSession = Depends(get_db)):
    from app.models.user import User
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ai_service = AIService(db, user.id)
    recommendation = await ai_service.recommend_next_task(request.available_minutes)

    return TaskRecommendationResponse(**recommendation)