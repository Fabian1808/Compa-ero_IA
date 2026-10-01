import msal
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.account import Account, AccountStatus
from app.models.session import Session
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
from app.security.encryption import get_encryption
from app.security.session import (
    create_session,
    set_auth_cookies,
    clear_auth_cookies,
    get_session_from_cookies,
    revoke_session,
    revoke_all_user_sessions,
    hash_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_msal_app():
    return msal.PublicClientApplication(
        client_id=settings.ms_graph_client_id,
        authority=settings.ms_graph_authority,
    )


@router.get("/login", response_model=AuthInitiateResponse)
async def login():
    """Initiate device code flow for Microsoft OAuth."""
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
async def callback(
    request: AuthCallbackRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Complete device code flow, store tokens, and create session with httpOnly cookies."""
    app = get_msal_app()
    result = app.acquire_token_by_device_flow({"device_code": request.device_code})

    if "access_token" not in result:
        error = result.get("error")
        error_description = result.get("error_description")
        raise HTTPException(status_code=400, detail=f"Token acquisition failed: {error} - {error_description}")

    auth_service = AuthService(db)
    user = await auth_service.get_or_create_user_from_token(result["access_token"])
    account = await auth_service.store_account_tokens(user, result)

    # Create session with httpOnly cookies
    await create_session(
        db=db,
        user_id=user.id,
        access_token=result["access_token"],
        refresh_token=result.get("refresh_token", ""),
        expires_in=result.get("expires_in", 3600),
        request=None,  # callback is typically from same origin
    )
    set_auth_cookies(
        response=response,
        access_token=result["access_token"],
        refresh_token=result.get("refresh_token", ""),
        expires_in=result.get("expires_in", 3600),
    )

    return TokenResponse(
        access_token=result["access_token"],
        expires_in=result.get("expires_in", 3600),
        refresh_token=result.get("refresh_token"),
    )


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Check authentication status from httpOnly cookie session."""
    session = await get_session_from_cookies(db, request)

    if not session:
        clear_auth_cookies(response)
        return AuthStatusResponse(authenticated=False, user=None)

    user = await db.get(User, session.user_id)
    if not user:
        clear_auth_cookies(response)
        return AuthStatusResponse(authenticated=False, user=None)

    return AuthStatusResponse(
        authenticated=True,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=SessionResponse)
async def current_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Return the caller's identity and the role they hold in the active tenant."""
    session = await get_session_from_cookies(db, request)

    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = await db.get(User, session.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

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
async def refresh_token(
    request: RefreshTokenRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token from cookie."""
    refresh_token = request.cookies.get("refresh_token") or request.refresh_token
    if not refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token provided")

    app = get_msal_app()
    result = app.acquire_token_by_refresh_token(refresh_token, scopes=settings.ms_graph_scopes_list)

    if "access_token" not in result:
        raise HTTPException(status_code=400, detail="Failed to refresh token")

    # Update session with new tokens
    refresh_token_hash = hash_token(refresh_token)
    result_obj = await db.execute(
        select(Session).where(Session.refresh_token_hash == refresh_token_hash)
    )
    session = result_obj.scalar_one_or_none()

    if session:
        session.access_token_hash = hash_token(result["access_token"])
        session.refresh_token_hash = hash_token(result.get("refresh_token", refresh_token))
        session.expires_at = datetime.utcnow() + timedelta(seconds=result.get("expires_in", 3600))
        await db.flush()

    # Update cookies
    set_auth_cookies(
        response=response,
        access_token=result["access_token"],
        refresh_token=result.get("refresh_token", refresh_token),
        expires_in=result.get("expires_in", 3600),
    )

    return TokenResponse(
        access_token=result["access_token"],
        expires_in=result.get("expires_in", 3600),
        refresh_token=result.get("refresh_token"),
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Logout - revoke session and clear cookies."""
    session = await get_session_from_cookies(db, request)

    if session:
        await revoke_session(db, session)

    clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.post("/logout-all")
async def logout_all(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Logout from all devices - revoke all sessions for user."""
    session = await get_session_from_cookies(db, request)

    if session:
        await revoke_all_user_sessions(db, session.user_id)

    clear_auth_cookies(response)
    return {"message": "Logged out from all devices"}