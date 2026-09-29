from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.models.notification import Notification, NotificationSeverity, NotificationType
from app.schemas.notification import NotificationResponse, NotificationSettings

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    is_read: Optional[bool] = Query(None),
    severity: Optional[NotificationSeverity] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    from app.models.user import User
    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        return []

    stmt = select(Notification).where(Notification.user_id == user.id)

    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)
    if severity:
        stmt = stmt.where(Notification.severity == severity)

    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    notifications = result.scalars().all()
    return notifications


@router.post("/{notification_id}/read")
async def mark_notification_read(notification_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalar_one_or_none()

    if not notification:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    await db.flush()
    return {"success": True}


@router.get("/settings", response_model=NotificationSettings)
async def get_notification_settings(db: AsyncSession = Depends(get_db)):
    from app.models.user import User
    from app.models.setting import Setting

    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get settings from DB or return defaults
    result = await db.execute(select(Setting).where(Setting.user_id == user.id, Setting.key == "notifications"))
    setting = result.scalar_one_or_none()

    if setting:
        import json
        return NotificationSettings(**json.loads(setting.value_json))

    return NotificationSettings()


@router.patch("/settings", response_model=NotificationSettings)
async def update_notification_settings(settings_data: NotificationSettings, db: AsyncSession = Depends(get_db)):
    from app.models.user import User
    from app.models.setting import Setting
    import json

    user_result = await db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(select(Setting).where(Setting.user_id == user.id, Setting.key == "notifications"))
    setting = result.scalar_one_or_none()

    if setting:
        setting.value_json = json.dumps(settings_data.model_dump())
    else:
        setting = Setting(
            id=str(uuid.uuid4()),
            user_id=user.id,
            key="notifications",
            value_json=json.dumps(settings_data.model_dump()),
        )
        db.add(setting)

    await db.flush()
    return settings_data


from app.models.user import User
from app.models.setting import Setting
import uuid
from fastapi import HTTPException