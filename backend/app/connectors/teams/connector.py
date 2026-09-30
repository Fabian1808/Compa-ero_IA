from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from app.connectors.base import Connector, SyncResult
from app.services.graph_service import GraphService


class TeamsConnector(Connector):
    """Microsoft Teams connector using Microsoft Graph API."""

    def __init__(self, graph_service: GraphService, account_id: str, user_id: str):
        self.graph_service = graph_service
        self.account_id = account_id
        self.user_id = user_id

    @property
    def name(self) -> str:
        return "teams"

    @property
    def required_scopes(self) -> list[str]:
        return [
            "Chat.Read",
            "Chat.ReadWrite",
            "ChannelMessage.Read.All",
            "Channel.ReadBasic.All",
            "Team.ReadBasic.All",
        ]

    async def authenticate(self, credentials: dict) -> bool:
        """Authenticate using the shared Graph service."""
        # We need an account object - this is a simplified version
        return True

    async def test_connection(self) -> bool:
        """Test if we can access Teams data."""
        try:
            async with self.graph_service.create_client(self._get_account()) as client:
                async for _ in client.get_chats({"$top": 1}):
                    return True
        except Exception:
            return False

    def _get_account(self):
        """Get account object from graph_service."""
        from app.models.account import Account
        account = Account()
        account.id = self.account_id
        account.user_id = self.user_id
        return account

    async def sync_incremental(
        self,
        since: datetime | None = None,
        cursor: str | None = None
    ) -> AsyncIterator[SyncResult]:
        """Sync chats and messages incrementally."""
        result = SyncResult()

        async with self.graph_service.create_client(self._get_account()) as client:
            # Sync chats
            async for chat_page in client.get_chats(
                {
                    "$select": "id,topic,chatType,createdDateTime,lastUpdatedDateTime,members",
                    "$orderby": "lastUpdatedDateTime desc",
                }
            ):
                for chat in chat_page.get("value", []):
                    result.items_processed += 1
                    result.items_created += 1

                yield result

            # Sync channel messages for each team
            async for team_page in client.get_joined_teams({"$select": "id,displayName,description"}):
                for team in team_page.get("value", []):
                    async for channel_page in client.get_team_channels(team["id"], {"$select": "id,displayName,description,membershipType"}):
                        for channel in channel_page.get("value", []):
                            async for msg_page in client.get_channel_messages(
                                team["id"],
                                channel["id"],
                                {
                                    "$select": "id,createdDateTime,lastModifiedDateTime,from,body,subject",
                                    "$top": 50,
                                    "$orderby": "lastModifiedDateTime desc",
                                }
                            ):
                                for msg in msg_page.get("value", []):
                                    result.items_processed += 1
                                    result.items_created += 1

                                yield result

    async def get_item(self, item_id: str) -> dict | None:
        """Get a specific chat or message by ID."""
        try:
            async with self.graph_service.create_client(self._get_account()) as client:
                return await client.get(f"/chats/{item_id}")
        except Exception:
            return None

    async def search(self, query: str, limit: int = 50) -> list[dict]:
        """Search chats and messages."""
        results = []
        try:
            async with self.graph_service.create_client(self._get_account()) as client:
                async for page in client.get_chats({
                    "$search": f"\"{query}\"",
                    "$top": limit,
                    "$select": "id,topic,chatType,lastUpdatedDateTime",
                }):
                    results.extend(page.get("value", []))
        except Exception:
            pass
        return results[:limit]
