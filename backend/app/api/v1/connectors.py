
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.registry import ALL_CONNECTOR_TYPES, ConnectorRegistry
from app.database import get_db
from app.models.account import Account

router = APIRouter(prefix="/connectors", tags=["connectors"])


def get_user_id(db: AsyncSession) -> str:
    from sqlalchemy import select

    from app.models.user import User
    user_result = db.execute(select(User).limit(1))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.id


@router.get("")
async def list_connectors(db: AsyncSession = Depends(get_db)):
    """List all available connector types."""
    user_id = get_user_id(db)
    registry = ConnectorRegistry(db)
    return registry.list_available_connectors()


@router.get("/{connector_type}/info")
async def get_connector_info(connector_type: str, db: AsyncSession = Depends(get_db)):
    """Get connector metadata."""
    registry = ConnectorRegistry(db)
    return registry.get_connector_info(connector_type)


@router.get("/accounts")
async def list_accounts(db: AsyncSession = Depends(get_db)):
    """List connected accounts."""
    user_id = get_user_id(db)
    from sqlalchemy import select
    result = await db.execute(select(Account).where(Account.user_id == user_id))
    accounts = result.scalars().all()
    return [
        {
            "id": a.id,
            "provider": a.provider,
            "email": a.email,
            "status": a.status.value,
            "last_sync": a.last_sync_at.isoformat() if a.last_sync_at else None,
            "meta": a.meta,
        }
        for a in accounts
    ]


@router.post("/accounts/{account_id}/test/{connector_type}")
async def test_connector(
    account_id: str,
    connector_type: str,
    db: AsyncSession = Depends(get_db)
):
    """Test a specific connector for an account."""
    user_id = get_user_id(db)
    from sqlalchemy import select
    result = await db.execute(select(Account).where(Account.id == account_id, Account.user_id == user_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    registry = ConnectorRegistry(db)
    success = await registry.test_connector(account, connector_type)
    return {"success": success}


@router.post("/accounts/{account_id}/sync/{connector_type}")
async def sync_connector(
    account_id: str,
    connector_type: str,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger sync for a connector."""
    user_id = get_user_id(db)
    from sqlalchemy import select
    result = await db.execute(select(Account).where(Account.id == account_id, Account.user_id == user_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    registry = ConnectorRegistry(db)
    connector = registry.get_connector(account, connector_type)

    results = []
    async for sync_result in connector.sync_incremental():
        results.append(sync_result)

    return {"results": results}


@router.get("/accounts/{account_id}/items/{connector_type}")
async def list_connector_items(
    account_id: str,
    connector_type: str,
    query: str = "",
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """List/search items from a connector."""
    user_id = get_user_id(db)
    from sqlalchemy import select
    result = await db.execute(select(Account).where(Account.id == account_id, Account.user_id == user_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    registry = ConnectorRegistry(db)
    connector = registry.get_connector(account, connector_type)

    if query:
        items = await connector.search(query, limit)
    else:
        # Get recent items via sync
        items = []
        async for sync_result in connector.sync_incremental():
            pass  # Items would be in sync_result

    return {"items": items[:limit]}


# External connector management
@router.post("/external/config")
async def set_external_connector_config(
    connector_type: str,
    config: dict,
    db: AsyncSession = Depends(get_db)
):
    """Set configuration for external connector (SAP, GitHub, n8n, etc.)."""
    if connector_type not in ALL_CONNECTOR_TYPES:
        raise HTTPException(status_code=400, detail="Unknown connector type")

    registry = ConnectorRegistry(db)
    registry.register_external_config(connector_type, config)
    return {"success": True}


@router.get("/external/config/{connector_type}")
async def get_external_connector_config(connector_type: str, db: AsyncSession = Depends(get_db)):
    """Get external connector configuration."""
    registry = ConnectorRegistry(db)
    config = registry.get_external_config(connector_type)
    # Mask sensitive fields
    masked = {}
    for k, v in config.items():
        if k in ("client_secret", "password", "api_key", "token"):
            masked[k] = "***"
        else:
            masked[k] = v
    return masked
