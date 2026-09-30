from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Tenant(Base):
    """Multi-tenant organization."""
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(7), default="#3b82f6")
    secondary_color: Mapped[str] = mapped_column(String(7), default="#1e40af")

    # Settings
    settings_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    features_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    # Limits
    max_users: Mapped[int] = mapped_column(default=100)
    max_storage_mb: Mapped[int] = mapped_column(default=10240)
    max_api_calls_per_day: Mapped[int] = mapped_column(default=100000)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    subscription_tier: Mapped[str] = mapped_column(String(50), default="free")
    subscription_status: Mapped[str] = mapped_column(String(50), default="active")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    users: Mapped[list[User]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    audit_logs: Mapped[list[AuditLog]] = relationship(back_populates="tenant")

    __table_args__ = (
        Index("ix_tenant_slug_active", "slug", "is_active"),
    )


#: Roles a member can hold within a tenant. Stored as a plain string on
#: ``TenantUser.role``; these constants keep the values consistent.
TENANT_ROLE_OWNER = "owner"
TENANT_ROLE_ADMIN = "admin"
TENANT_ROLE_MEMBER = "member"
TENANT_ROLE_VIEWER = "viewer"

TENANT_ROLES = frozenset(
    {TENANT_ROLE_OWNER, TENANT_ROLE_ADMIN, TENANT_ROLE_MEMBER, TENANT_ROLE_VIEWER}
)

#: Roles allowed to administer a tenant.
TENANT_ADMIN_ROLES = frozenset({TENANT_ROLE_OWNER, TENANT_ROLE_ADMIN})


class TenantUser(Base):
    """User membership in a tenant."""
    __tablename__ = "tenant_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(50), default="member")  # owner, admin, member, viewer
    permissions_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    invited_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    invited_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    tenant: Mapped[Tenant] = relationship(back_populates="users")
    user: Mapped[User] = relationship(back_populates="tenant_memberships")

    __table_args__ = (
        Index("ix_tenant_user_tenant_user", "tenant_id", "user_id", unique=True),
        Index("ix_tenant_user_active", "tenant_id", "is_active"),
    )


class TenantInvitation(Base):
    """Invitation to join a tenant."""
    __tablename__ = "tenant_invitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="member")
    permissions_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    invited_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    # Relationships
    tenant: Mapped[Tenant] = relationship()


class TenantSettings(Base):
    """Tenant-level configuration."""
    __tablename__ = "tenant_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False)

    # AI Configuration
    ai_provider: Mapped[str] = mapped_column(String(50), default="ollama")
    ai_chat_model: Mapped[str] = mapped_column(String(100), default="phi3:3.8b")
    ai_embed_model: Mapped[str] = mapped_column(String(100), default="nomic-embed-text")
    ai_temperature: Mapped[float] = mapped_column(default=0.1)
    ai_max_tokens: Mapped[int] = mapped_column(default=2048)
    ai_confidence_auto_create: Mapped[int] = mapped_column(default=95)
    ai_confidence_suggest: Mapped[int] = mapped_column(default=80)

    # Data Retention
    email_retention_days: Mapped[int] = mapped_column(default=365)
    task_retention_days: Mapped[int] = mapped_column(default=1095)
    audit_log_retention_days: Mapped[int] = mapped_column(default=2555)
    attachment_retention_days: Mapped[int] = mapped_column(default=365)

    # Security
    require_mfa: Mapped[bool] = mapped_column(Boolean, default=False)
    session_timeout_minutes: Mapped[int] = mapped_column(default=480)
    password_min_length: Mapped[int] = mapped_column(default=8)
    allowed_domains_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    ip_whitelist_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    # Integrations
    enabled_connectors_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    connector_configs_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    # Notifications
    daily_briefing_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_briefing_hour: Mapped[int] = mapped_column(default=8)
    end_of_day_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    end_of_day_hour: Mapped[int] = mapped_column(default=18)
    notification_channels_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    # Customization
    custom_branding_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    custom_workflows_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    tenant: Mapped[Tenant] = relationship()
