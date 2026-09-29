from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import uuid

from app.database import get_db
from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskStatus
from app.schemas.project import ProjectResponse, ProjectCreate, ProjectUpdate, ProjectProgressResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    status: Optional[ProjectStatus] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import User
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        return []

    stmt = select(Project).where(Project.user_id == user.id)

    if status:
        stmt = stmt.where(Project.status == status)

    stmt = stmt.order_by(Project.updated_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    projects = result.scalars().all()
    return projects


@router.post("", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    from app.models.user import User
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    project = Project(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name=project_data.name,
        description=project_data.description,
        color=project_data.color,
        status=ProjectStatus.ACTIVE,
    )

    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, project_data: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.flush()
    await db.refresh(project)
    return project


@router.get("/{project_id}/progress", response_model=ProjectProgressResponse)
async def get_project_progress(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Count tasks by status
    total_result = await db.execute(select(func.count(Task.id)).where(Task.project_id == project_id))
    total = total_result.scalar() or 0

    completed_result = await db.execute(select(func.count(Task.id)).where(
        Task.project_id == project_id, Task.status == TaskStatus.COMPLETED
    ))
    completed = completed_result.scalar() or 0

    in_progress_result = await db.execute(select(func.count(Task.id)).where(
        Task.project_id == project_id, Task.status == TaskStatus.IN_PROGRESS
    ))
    in_progress = in_progress_result.scalar() or 0

    blocked_result = await db.execute(select(func.count(Task.id)).where(
        Task.project_id == project_id, Task.status == TaskStatus.BLOCKED
    ))
    blocked = blocked_result.scalar() or 0

    progress = int((completed / total * 100)) if total > 0 else 0

    return ProjectProgressResponse(
        project_id=project.id,
        name=project.name,
        progress=progress,
        total_tasks=total,
        completed_tasks=completed,
        in_progress_tasks=in_progress,
        blocked_tasks=blocked,
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.flush()
    return {"message": "Project deleted"}


# Need to import User and TaskStatus
from app.models.user import User
from app.models.task import TaskStatus