import msal
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.multi_tenancy.models import TENANT_ADMIN_ROLES, Tenant, TenantUser
from app.schemas.auth import (
    AuthCallbackRequest,
    AuthInitiateResponse,
    AuthStatusResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.user import SessionResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_msal_app():
    return msal.PublicClientApplication(
        client_id=settings.ms_graph_client_id,

        authority=settings.ms_graph_authority,
    )


@router.get("/login", response_model=AuthInitiateResponse)
async def login():
    """Initiate device code flow for Microsoft OAuth."""
    auth_service = AuthService(None)  # We'll create a new one with db in the method
    # Use MSAL directly for device code flow initiation
    app = get_msal_app()
    flow = app.initiate_device_flow(scopes=settings.ms_graph_scopes_list)

    if "user_code" not in flow:
        raise HTTPException(status_code=500, detail="Failed to initiate device code flow")

    return AuthInitiateResponse(
        device_code=flow["device_code"],
        user_code=flow["user_code"],
        verification_uri=flow["verification_uri"],
        expires_in=flow["expires_in"],
        interval=flow["interval"],
        message=flow["message"],
    )


@router.post("/callback", response_model=TokenResponse)
async def callback(request: AuthCallbackRequest, db: AsyncSession = Depends(get_db)):
    """Complete device code flow and store tokens."""
    app = get_msal_app()
    result = app.acquire_token_by_device_flow({"device_code": request.device_code})

    if "access_token" not in result:
        error = result.get("error")
        error_description = result.get("error_description")
        raise HTTPException(status_code=400, detail=f"Token acquisition failed: {error} - {error_description}")

    auth_service = AuthService(db)
    user = await auth_service.get_or_create_user_from_token(result["access_token"])
    account = await auth_service.store_account_tokens(user, result)

    return TokenResponse(
        access_token=result["access_token"],
        expires_in=result.get("expires_in", 3600),
        refresh_token=result.get("refresh_token"),
    )


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(db: AsyncSession = Depends(get_db)):
    """Check authentication status."""
    # For now, return unauthenticated - in production would check session/cookie
    return AuthStatusResponse(authenticated=False, user=None)


@router.get("/me", response_model=SessionResponse)
async def current_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Return the caller's identity and the role they hold in the active tenant.

    This endpoint lives under the ``/auth`` prefix, which ``TenantMiddleware``
    skips, so the tenant membership is resolved here instead of from
    ``request.state``. An explicit ``X-Tenant-ID`` header wins; otherwise the
    first active membership is used, matching the single-user local mode that
    ``get_current_user_id`` already assumes.

    ``is_admin`` is computed from the stored membership so the frontend never
    decides admin access on its own.
    """
    user = await db.scalar(select(User).limit(1))
    if not user:
        raise HTTPException(status_code=401, detail="Not signed in")

    requested_tenant_id = request.headers.get("X-Tenant-ID")

    membership_query = select(TenantUser).where(
        TenantUser.user_id == user.id,
        TenantUser.is_active.is_(True),
    )
    if requested_tenant_id:
        membership_query = membership_query.where(
            TenantUser.tenant_id == requested_tenant_id
        )

    membership = await db.scalar(
        membership_query.order_by(TenantUser.invited_at.asc()).limit(1)
    )

    tenant_name = None
    if membership is not None:
        tenant = await db.get(Tenant, membership.tenant_id)
        tenant_name = tenant.name if tenant else None

    role = membership.role if membership else None

    return SessionResponse(
        user=UserResponse.model_validate(user),
        tenant_id=membership.tenant_id if membership else None,
        tenant_name=tenant_name,
        role=role,
        is_admin=role in TENANT_ADMIN_ROLES,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token."""
    app = get_msal_app()
    result = app.acquire_token_by_refresh_token(request.refresh_token, scopes=settings.ms_graph_scopes_list)

    if "access_token" not in result:
        raise HTTPException(status_code=400, detail="Failed to refresh token")

    return TokenResponse(
        access_token=result["access_token"],
        expires_in=result.get("expires_in", 3600),
        refresh_token=result.get("refresh_token"),
    )


@router.post("/logout")
async def logout(db: AsyncSession = Depends(get_db)):
    """Logout - in a real app would clear session/cookie."""
    return {"message": "Logged out"}
