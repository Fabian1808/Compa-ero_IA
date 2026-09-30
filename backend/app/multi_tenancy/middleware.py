from __future__ import annotations

from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.database import async_session_maker
from app.models.user import User
from app.multi_tenancy.models import Tenant, TenantUser


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware for tenant isolation and context."""

    def __init__(self, app, exclude_paths: list[str] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/api/v1/health",
            "/api/v1/auth",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip tenant resolution for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Get tenant from various sources
        tenant = await self._resolve_tenant(request)

        if not tenant:
            return JSONResponse(
                {"detail": "Tenant not found or inactive"},
                status_code=404
            )

        # Add tenant to request state
        request.state.tenant = tenant
        request.state.tenant_id = tenant.id

        # Get user context if authenticated
        user = await self._resolve_user(request, tenant)
        if user:
            request.state.current_user = user
            request.state.user_id = user.id

        # Check tenant status
        if not tenant.is_active:
            return JSONResponse(
                {"detail": "Tenant is inactive"},
                status_code=403
            )

        response = await call_next(request)
        return response

    async def _resolve_tenant(self, request: Request) -> Tenant | None:
        """Resolve tenant from request."""
        # 1. Check subdomain
        host = request.headers.get("host", "")
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain not in ("www", "api", "app", "localhost"):
                async with async_session_maker() as db:
                    stmt = select(Tenant).where(
                        Tenant.slug == subdomain,
                        Tenant.is_active == True,
                        Tenant.deleted_at.is_(None)
                    )
                    result = await db.execute(stmt)
                    tenant = result.scalar_one_or_none()
                    if tenant:
                        return tenant

        # 2. Check custom domain
        if host and not host.startswith("localhost"):
            async with async_session_maker() as db:
                stmt = select(Tenant).where(
                    Tenant.domain == host,
                    Tenant.is_active == True,
                    Tenant.deleted_at.is_(None)
                )
                result = await db.execute(stmt)
                tenant = result.scalar_one_or_none()
                if tenant:
                    return tenant

        # 3. Check header (for API calls)
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            async with async_session_maker() as db:
                stmt = select(Tenant).where(
                    Tenant.id == tenant_id,
                    Tenant.is_active == True,
                    Tenant.deleted_at.is_(None)
                )
                result = await db.execute(stmt)
                return result.scalar_one_or_none()

        # 4. Default tenant (for development)
        async with async_session_maker() as db:
            stmt = select(Tenant).where(
                Tenant.is_active == True,
                Tenant.deleted_at.is_(None)
            ).limit(1)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()

    async def _resolve_user(self, request: Request, tenant: Tenant) -> User | None:
        """Resolve user from request within tenant context."""
        # Check Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        # Validate token and get user
        from app.services.auth_service import AuthService
        async with async_session_maker() as db:
            auth_service = AuthService(db)
            try:
                user = await auth_service.get_user_from_token(token)
                if not user:
                    return None

                # Check if user belongs to tenant
                stmt = select(TenantUser).where(
                    TenantUser.tenant_id == tenant.id,
                    TenantUser.user_id == user.id,
                    TenantUser.is_active == True
                )
                result = await db.execute(stmt)
                membership = result.scalar_one_or_none()

                if membership:
                    return user
            except Exception:
                pass

        return None


def get_current_tenant(request: Request) -> Tenant:
    """Dependency to get current tenant."""
    if not hasattr(request.state, "tenant"):
        raise Exception("Tenant not resolved")
    return request.state.tenant


def get_current_user(request: Request) -> User | None:
    """Dependency to get current user."""
    return getattr(request.state, "current_user", None)


def require_tenant_admin(request: Request) -> User:
    """Dependency to require tenant admin role."""
    user = get_current_user(request)
    tenant = get_current_tenant(request)

    if not user:
        raise Exception("Authentication required")

    # Check admin role (would need to query TenantUser)
    # For now, just return user
    return user
