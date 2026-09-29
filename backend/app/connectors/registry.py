from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.connectors.base import Connector
from app.connectors.outlook import OutlookConnector
from app.models.account import Account


class ConnectorRegistry:
    """Registry for managing connectors."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._connectors: dict[str, Connector] = {}

    def get_connector(self, account: Account) -> Connector:
        key = f"{account.provider}:{account.id}"
        if key not in self._connectors:
            if account.provider == "microsoft":
                self._connectors[key] = OutlookConnector(self.db, account)
            else:
                raise ValueError(f"Unknown connector provider: {account.provider}")
        return self._connectors[key]

    async def test_connector(self, account: Account) -> bool:
        connector = self.get_connector(account)
        return await connector.test_connection()

    def clear_connector(self, account: Account) -> None:
        key = f"{account.provider}:{account.id}"
        if key in self._connectors:
            del self._connectors[key]