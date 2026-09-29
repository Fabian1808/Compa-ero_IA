from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import msal

from app.database import get_db
from app.config import settings
from app.services.auth_service import AuthService
from app.models.account import Account
from app.models.user import User
from app.schemas.auth import (
    AuthInitiateResponse,
    AuthCallbackRequest,
    AuthStatusResponse,
    TokenResponse,
    RefreshTokenRequest,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def get_msal_app():
    return msal.PublicClientApplication(
        client_id=settings.ms_graph_client_id,
        client_credential=settings.ms_graph_client_secret,
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