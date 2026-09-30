from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from app.connectors.base import Connector, SyncResult
from app.services.graph_service import GraphService


class OneDriveConnector(Connector):
    """OneDrive connector using Microsoft Graph API."""

    def __init__(self, graph_service: GraphService, account_id: str, user_id: str):
        self.graph_service = graph_service
        self.account_id = account_id
        self.user_id = user_id

    @property
    def name(self) -> str:
        return "onedrive"

    @property
    def required_scopes(self) -> list[str]:
        return [
            "Files.Read",
            "Files.Read.All",
            "Files.ReadWrite",
            "Files.ReadWrite.All",
            "Sites.Read.All",
        ]

    async def authenticate(self, credentials: dict) -> bool:
        return True

    def _get_account(self):
        from app.models.account import Account
        account = Account()
        account.id = self.account_id
        account.user_id = self.user_id
        return account

    async def test_connection(self) -> bool:
        try:
            async with self.graph_service.create_client(self._get_account()) as client:
                await client.get_drive()
                return True
        except Exception:
            return False

    async def sync_incremental(
        self,
        since: datetime | None = None,
        cursor: str | None = None
    ) -> AsyncIterator[SyncResult]:
        """Sync OneDrive files incrementally using delta queries."""
        result = SyncResult()

        async with self.graph_service.create_client(self._get_account()) as client:
            delta_link = cursor
            params = {"$select": "id,name,createdDateTime,lastModifiedDateTime,size,file,folder,webUrl,parentReference"}

            if delta_link:
                async for page in client.get_paginated(delta_link, params=None):
                    for item in page.get("value", []):
                        result.items_processed += 1
                        if item.get("deleted"):
                            result.items_deleted += 1
                        else:
                            result.items_created += 1

                    if "@odata.deltaLink" in page:
                        result.next_cursor = page["@odata.deltaLink"]

                    yield result
            else:
                async for page in client.get_drive_delta(params):
                    for item in page.get("value", []):
                        result.items_processed += 1
                        if item.get("deleted"):
                            result.items_deleted += 1
                        else:
                            result.items_created += 1

                    if "@odata.deltaLink" in page:
                        result.next_cursor = page["@odata.deltaLink"]

                    yield result

    async def get_item(self, item_id: str) -> dict | None:
        try:
            async with self.graph_service.create_client(self._get_account()) as client:
                return await client.get(f"/me/drive/items/{item_id}")
        except Exception:
            return None

    async def search(self, query: str, limit: int = 50) -> list[dict]:
        results = []
        try:
            async with self.graph_service.create_client(self._get_account()) as client:
                async for page in client.search_drive(query, {"$top": limit}):
                    results.extend(page.get("value", []))
        except Exception:
            pass
        return results[:limit]
