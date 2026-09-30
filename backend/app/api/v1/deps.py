from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "[::1]"}


async def get_current_user_id(db: AsyncSession = Depends(get_db)) -> str:
    """Get the current user ID. For now, returns the first user (single-user mode)."""
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="No user found. Please complete setup first.")

    return user.id


async def get_optional_user_id(db: AsyncSession = Depends(get_db)) -> str | None:
    """Get the current user ID if exists, otherwise None."""
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    return user.id if user else None


def _is_loopback(client_host: str | None) -> bool:
    if not client_host:
        return False
    return client_host.strip("[]") in {"localhost", "127.0.0.1", "::1"}


async def require_local_client(request: Request) -> None:
    """
    Guard for first-run bootstrap endpoints.

    Setup runs before any Microsoft account is connected, so there is no user to
    authorize against yet. Those endpoints can install software, so they are
    restricted to callers on this machine: the request must originate from a
    loopback address and the app's own origins.

    This is intentionally narrower than authentication and must not be reused
    for endpoints that read or modify a user's data.
    """
    client_host = request.client.host if request.client else None
    if _is_loopback(client_host):
        return

    origin = request.headers.get("origin")
    if origin:
        origin_host = origin.split("//")[-1].split(":")[0]
        if origin_host in {"localhost", "127.0.0.1", "tauri"}:
            return

    raise HTTPException(
        status_code=403,
        detail="First-run setup is only available on this computer.",
    )
