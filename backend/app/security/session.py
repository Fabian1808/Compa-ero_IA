import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Response, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.models.account import Account
from app.security.encryption import get_encryption
from app.config import settings


def hash_token(token: str) -> str:
    """Hash a token for storage using SHA256."""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token_hash(token: str, token_hash: str) -> bool:
    """Verify a token against its hash."""
    return hash_token(token) == token_hash


def generate_csrf_token() -> str:
    """Generate a CSRF token."""
    return secrets.token_urlsafe(32)


async def create_session(
    db: AsyncSession,
    user_id: str,
    access_token: str,
    refresh_token: str,
    expires_in: int,
    request: Optional[Request] = None,
) -> Session:
    """Create a new session record."""
    access_token_hash = hash_token(access_token)
    refresh_token_hash = hash_token(refresh_token)
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    user_agent = request.headers.get("user-agent") if request else None
    ip_address = request.client.host if request and request.client else None

    session = Session(
        user_id=user_id,
        access_token_hash=access_token_hash,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(session)
    await db.flush()
    return session


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    expires_in: int,
):
    """Set httpOnly secure cookies for authentication."""
    # Access token cookie (short-lived)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=expires_in,
        path="/",
    )
    # Refresh token cookie (longer-lived)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,  # 30 days
        path="/",
    )


def clear_auth_cookies(response: Response):
    """Clear authentication cookies."""
    response.delete_cookie(key="access_token", path="/", secure=settings.cookie_secure, samesite="lax")
    response.delete_cookie(key="refresh_token", path="/", secure=settings.cookie_secure, samesite="lax")


async def get_session_from_cookies(
    db: AsyncSession,
    request: Request,
) -> Optional[Session]:
    """Get valid session from cookies."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        return None

    access_token_hash = hash_token(access_token)

    result = await db.execute(
        select(Session).where(
            Session.access_token_hash == access_token_hash,
            Session.expires_at > datetime.utcnow(),
        )
    )
    session = result.scalar_one_or_none()

    if session:
        session.last_used_at = datetime.utcnow()
        await db.flush()

    return session


async def revoke_session(db: AsyncSession, session: Session):
    """Revoke a session."""
    await db.delete(session)
    await db.flush()


async def revoke_all_user_sessions(db: AsyncSession, user_id: str):
    """Revoke all sessions for a user."""
    result = await db.execute(select(Session).where(Session.user_id == user_id))
    sessions = result.scalars().all()
    for session in sessions:
        await db.delete(session)
    await db.flush()