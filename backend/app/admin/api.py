from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.email import Email
from app.models.task import Task
from app.models.user import User
from app.multi_tenancy.middleware import require_tenant_admin
from app.multi_tenancy.models import Tenant, TenantInvitation, TenantSettings, TenantUser

router = APIRouter(prefix="/admin", tags=["admin"])

# Authorization lives in the multi-tenancy layer: roles are per tenant, so the
# check must read the TenantUser membership rather than the user record. A local
# `require_admin` that only checked the user would grant admin to everyone.
require_admin = require_tenant_admin


# Tenant Management
@router.get("/tenants")
async def list_tenants(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str = "",
    status: str = "",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """List all tenants."""
    stmt = select(Tenant).where(Tenant.deleted_at.is_(None))

    if search:
        stmt = stmt.where(
            Tenant.name.ilike(f"%{search}%") | Tenant.slug.ilike(f"%{search}%")
        )
    if status == "active":
        stmt = stmt.where(Tenant.is_active.is_(True))
    elif status == "inactive":
        stmt = stmt.where(Tenant.is_active.is_(False))

    stmt = stmt.order_by(desc(Tenant.created_at))

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    # Paginate
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    tenants = result.scalars().all()

    return {
        "tenants": [
            {
                "id": t.id,
                "name": t.name,
                "slug": t.slug,
                "domain": t.domain,
                "is_active": t.is_active,
                "subscription_tier": t.subscription_tier,
                "subscription_status": t.subscription_status,
                "created_at": t.created_at.isoformat(),
                "user_count": 0,  # Would count TenantUser
            }
            for t in tenants
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("/tenants")
async def create_tenant(
    name: str,
    slug: str,
    domain: str | None = None,
    subscription_tier: str = "free",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Create a new tenant."""
    # Check slug uniqueness
    existing = await db.execute(select(Tenant).where(Tenant.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already exists")

    if domain:
        existing = await db.execute(select(Tenant).where(Tenant.domain == domain))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Domain already exists")

    tenant = Tenant(
        name=name,
        slug=slug,
        domain=domain,
        subscription_tier=subscription_tier,
    )
    db.add(tenant)

    # Create default settings
    settings = TenantSettings(tenant_id=tenant.id)
    db.add(settings)

    await db.commit()

    return {"id": tenant.id, "name": tenant.name, "slug": tenant.slug}


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Get tenant details."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get user count
    user_count = await db.execute(
        select(func.count(TenantUser.id)).where(TenantUser.tenant_id == tenant_id)
    )

    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "domain": tenant.domain,
        "is_active": tenant.is_active,
        "subscription_tier": tenant.subscription_tier,
        "subscription_status": tenant.subscription_status,
        "created_at": tenant.created_at.isoformat(),
        "user_count": user_count.scalar(),
    }


@router.patch("/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    name: str | None = None,
    domain: str | None = None,
    is_active: bool | None = None,
    subscription_tier: str | None = None,
    subscription_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Update tenant."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if name is not None:
        tenant.name = name
    if domain is not None:
        # Check domain uniqueness
        existing = await db.execute(select(Tenant).where(Tenant.domain == domain, Tenant.id != tenant_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Domain already exists")
        tenant.domain = domain
    if is_active is not None:
        tenant.is_active = is_active
    if subscription_tier is not None:
        tenant.subscription_tier = subscription_tier
    if subscription_status is not None:
        tenant.subscription_status = subscription_status

    await db.commit()
    return {"success": True}


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Soft delete tenant."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    tenant.deleted_at = datetime.utcnow()
    tenant.is_active = False
    await db.commit()
    return {"success": True}


# Tenant Users
@router.get("/tenants/{tenant_id}/users")
async def list_tenant_users(
    tenant_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """List users in a tenant."""
    stmt = select(TenantUser, User).join(User).where(TenantUser.tenant_id == tenant_id)
    stmt = stmt.order_by(desc(TenantUser.joined_at))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    rows = result.all()

    return {
        "users": [
            {
                "id": tu.id,
                "user_id": u.id,
                "email": u.email,
                "name": u.name,
                "role": tu.role,
                "is_active": tu.is_active,
                "joined_at": tu.joined_at.isoformat() if tu.joined_at else None,
                "last_active_at": tu.last_active_at.isoformat() if tu.last_active_at else None,
            }
            for tu, u in rows
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("/tenants/{tenant_id}/users")
async def add_tenant_user(
    tenant_id: str,
    email: str,
    role: str = "member",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Add user to tenant."""
    # Find user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already member
    existing = await db.execute(
        select(TenantUser).where(TenantUser.tenant_id == tenant_id, TenantUser.user_id == user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already in tenant")

    membership = TenantUser(
        tenant_id=tenant_id,
        user_id=user.id,
        role=role,
        joined_at=datetime.utcnow(),
    )
    db.add(membership)
    await db.commit()

    return {"success": True, "membership_id": membership.id}


@router.patch("/tenants/{tenant_id}/users/{user_id}")
async def update_tenant_user(
    tenant_id: str,
    user_id: str,
    role: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Update tenant user membership."""
    result = await db.execute(
        select(TenantUser).where(TenantUser.tenant_id == tenant_id, TenantUser.user_id == user_id)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    if role is not None:
        membership.role = role
    if is_active is not None:
        membership.is_active = is_active

    await db.commit()
    return {"success": True}


@router.delete("/tenants/{tenant_id}/users/{user_id}")
async def remove_tenant_user(
    tenant_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Remove user from tenant."""
    result = await db.execute(
        select(TenantUser).where(TenantUser.tenant_id == tenant_id, TenantUser.user_id == user_id)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    await db.delete(membership)
    await db.commit()
    return {"success": True}


# Invitations
@router.post("/tenants/{tenant_id}/invitations")
async def create_invitation(
    tenant_id: str,
    email: str,
    role: str = "member",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Invite user to tenant."""
    import secrets
    token = secrets.token_urlsafe(32)

    invitation = TenantInvitation(
        tenant_id=tenant_id,
        email=email,
        role=role,
        invited_by=current_user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(invitation)
    await db.commit()

    return {"invitation_id": invitation.id, "token": token}


@router.get("/tenants/{tenant_id}/invitations")
async def list_invitations(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """List pending invitations."""
    result = await db.execute(
        select(TenantInvitation).where(TenantInvitation.tenant_id == tenant_id)
        .order_by(desc(TenantInvitation.created_at))
    )
    invitations = result.scalars().all()

    return [
        {
            "id": inv.id,
            "email": inv.email,
            "role": inv.role,
            "expires_at": inv.expires_at.isoformat(),
            "accepted_at": inv.accepted_at.isoformat() if inv.accepted_at else None,
            "created_at": inv.created_at.isoformat(),
        }
        for inv in invitations
    ]


# Tenant Settings
@router.get("/tenants/{tenant_id}/settings")
async def get_tenant_settings(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Get tenant settings."""
    result = await db.execute(select(TenantSettings).where(TenantSettings.tenant_id == tenant_id))
    settings = result.scalar_one_or_none()
    if not settings:
        # Create default
        settings = TenantSettings(tenant_id=tenant_id)
        db.add(settings)
        await db.commit()

    return {
        "ai_provider": settings.ai_provider,
        "ai_chat_model": settings.ai_chat_model,
        "ai_embed_model": settings.ai_embed_model,
        "ai_temperature": settings.ai_temperature,
        "ai_max_tokens": settings.ai_max_tokens,
        "ai_confidence_auto_create": settings.ai_confidence_auto_create,
        "ai_confidence_suggest": settings.ai_confidence_suggest,
        "email_retention_days": settings.email_retention_days,
        "task_retention_days": settings.task_retention_days,
        "require_mfa": settings.require_mfa,
        "session_timeout_minutes": settings.session_timeout_minutes,
        "enabled_connectors": settings.enabled_connectors_json,
    }


@router.patch("/tenants/{tenant_id}/settings")
async def update_tenant_settings(
    tenant_id: str,
    settings_data: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Update tenant settings."""
    result = await db.execute(select(TenantSettings).where(TenantSettings.tenant_id == tenant_id))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = TenantSettings(tenant_id=tenant_id)
        db.add(settings)

    # Update allowed fields
    allowed_fields = [
        "ai_provider", "ai_chat_model", "ai_embed_model", "ai_temperature", "ai_max_tokens",
        "ai_confidence_auto_create", "ai_confidence_suggest",
        "email_retention_days", "task_retention_days", "audit_log_retention_days",
        "require_mfa", "session_timeout_minutes", "password_min_length",
        "allowed_domains_json", "ip_whitelist_json",
        "enabled_connectors_json", "connector_configs_json",
        "daily_briefing_enabled", "daily_briefing_hour", "end_of_day_enabled", "end_of_day_hour",
        "notification_channels_json", "custom_branding_json", "custom_workflows_json",
    ]

    for field in allowed_fields:
        if field in settings_data:
            setattr(settings, field, settings_data[field])

    await db.commit()
    return {"success": True}


# Audit Logs
@router.get("/audit-logs")
async def list_audit_logs(
    tenant_id: str | None = None,
    user_id: str | None = None,
    action: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """List audit logs."""
    stmt = select(AuditLog).order_by(desc(AuditLog.created_at))

    if tenant_id:
        stmt = stmt.where(AuditLog.tenant_id == tenant_id)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if start_date:
        stmt = stmt.where(AuditLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        stmt = stmt.where(AuditLog.created_at <= datetime.fromisoformat(end_date))

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar()

    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": log.id,
                "tenant_id": log.tenant_id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details_json,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


# System Metrics
@router.get("/metrics")
async def get_system_metrics(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Get system-wide metrics."""
    # Total tenants
    total_tenants = (await db.execute(select(func.count(Tenant.id)))).scalar()
    active_tenants = (await db.execute(
        select(func.count(Tenant.id)).where(Tenant.is_active.is_(True))
    )).scalar()

    # Total users
    total_users = (await db.execute(select(func.count(User.id)))).scalar()

    # Total tasks
    total_tasks = (await db.execute(select(func.count(Task.id)))).scalar()
    completed_tasks = (await db.execute(
        select(func.count(Task.id)).where(Task.status == "completed")
    )).scalar()

    # Total emails
    total_emails = (await db.execute(select(func.count(Email.id)))).scalar()

    # Recent activity
    recent_tasks = (await db.execute(
        select(func.count(Task.id)).where(Task.created_at >= datetime.utcnow() - timedelta(days=7))
    )).scalar()

    return {
        "tenants": {
            "total": total_tenants,
            "active": active_tenants,
        },
        "users": {
            "total": total_users,
        },
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "completion_rate": round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0,
            "recent_week": recent_tasks,
        },
        "emails": {
            "total": total_emails,
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


from datetime import timedelta
