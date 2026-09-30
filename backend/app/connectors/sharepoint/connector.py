from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from app.connectors.base import Connector, SyncResult
from app.services.graph_service import GraphService


class SharePointConnector(Connector):
    """SharePoint connector using Microsoft Graph API."""

    def __init__(self, graph_service: GraphService, account_id: str, user_id: str):
        self.graph_service = graph_service
        self.account_id = account_id
        self.user_id = user_id

    @property
    def name(self) -> str:
        return "sharepoint"

    @property
    def required_scopes(self) -> list[str]:
        return [
            "Sites.Read.All",
            "Sites.ReadWrite.All",
            "Files.Read.All",
            "Files.ReadWrite.All",
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
                async for _ in client.get_followed_sites({"$top": 1}):
                    return True
        except Exception:
            return False

    async def sync_incremental(
        self,
        since: datetime | None = None,
        cursor: str | None = None
    ) -> AsyncIterator[SyncResult]:
        """Sync SharePoint sites and lists incrementally."""
        result = SyncResult()

        async with self.graph_service.create_client(self._get_account()) as client:
            # Sync followed sites
            async for site_page in client.get_followed_sites(
                {"$select": "id,displayName,webUrl,createdDateTime,lastModifiedDateTime"}
            ):
                for site in site_page.get("value", []):
                    result.items_processed += 1
                    result.items_created += 1

                    # Sync lists in the site
                    try:
                        async for list_page in client.get_site_lists(
                            site["id"],
                            {"$select": "id,displayName,createdDateTime,lastModifiedDateTime,list"}
                        ):
                            for sp_list in list_page.get("value", []):
                                result.items_processed += 1
                                result.items_created += 1

                                # Sync list items (documents)
                                if sp_list.get("list", {}).get("template") == "documentLibrary":
                                    async for item_page in client.get_list_items(
                                        site["id"],
                                        sp_list["id"],
                                        {
                                            "$select": "id,fields,createdDateTime,lastModifiedDateTime,webUrl",
                                            "$expand": "fields",
                                            "$top": 100,
                                        }
                                    ):
                                        for item in item_page.get("value", []):
                                            result.items_processed += 1
                                            result.items_created += 1

                                        yield result
                    except Exception:
                        pass

                    yield result

    async def get_item(self, item_id: str) -> dict | None:
        try:
            async with self.graph_service.create_client(self._get_account()) as client:
                return await client.get(f"/sites/root/lists/root/items/{item_id}")
        except Exception:
            return None

    async def search(self, query: str, limit: int = 50) -> list[dict]:
        results = []
        try:
            async with self.graph_service.create_client(self._get_account()) as client:
                async for site_page in client.get_followed_sites({"$top": 10}):
                    for site in site_page.get("value", []):
                        try:
                            async for page in client.search_site(site["id"], query, {"$top": limit}):
                                results.extend(page.get("value", []))
                        except Exception:
                            continue
        except Exception:
            pass
        return results[:limit]
