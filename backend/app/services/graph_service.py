import httpx
import json
from datetime import datetime
from typing import Optional, AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.account import Account
from app.services.auth_service import AuthService


class GraphClient:
    """Microsoft Graph API client with automatic token refresh."""

    def __init__(self, db: AsyncSession, account: Account):
        self.db = db
        self.account = account
        self.auth_service = AuthService(db)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    async def _get_headers(self) -> dict:
        access_token = await self.auth_service.get_valid_access_token(self.account)
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def get(self, path: str, params: dict = None) -> dict:
        headers = await self._get_headers()
        url = f"https://graph.microsoft.com/v1.0{path}"
        response = await self._client.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    async def get_paginated(self, path: str, params: dict = None) -> AsyncIterator[dict]:
        """Iterate through paginated Graph API responses."""
        headers = await self._get_headers()
        url = f"https://graph.microsoft.com/v1.0{path}"

        while url:
            response = await self._client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            yield data

            url = data.get("@odata.nextLink")
            params = None  # nextLink already contains params

    async def get_delta(self, path: str, delta_link: Optional[str] = None, params: dict = None) -> AsyncIterator[dict]:
        """Iterate through delta query responses."""
        headers = await self._get_headers()
        url = delta_link or f"https://graph.microsoft.com/v1.0{path}"

        while url:
            response = await self._client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            yield data

            url = data.get("@odata.deltaLink") or data.get("@odata.nextLink")
            params = None

    async def get_user(self) -> dict:
        return await self.get("/me")

    async def get_messages(self, folder_id: str = "inbox", params: dict = None) -> AsyncIterator[dict]:
        default_params = {
            "$select": "id,subject,from,toRecipients,receivedDateTime,bodyPreview,body,importance,hasAttachments,conversationId,isRead,categories",
            "$top": 100,
            "$orderby": "receivedDateTime desc",
        }
        if params:
            default_params.update(params)
        async for page in self.get_paginated(f"/me/mailFolders/{folder_id}/messages", default_params):
            yield page

    async def get_messages_delta(self, folder_id: str = "inbox", delta_link: Optional[str] = None) -> AsyncIterator[dict]:
        path = f"/me/mailFolders/{folder_id}/messages/delta"
        params = {
            "$select": "id,subject,from,toRecipients,receivedDateTime,bodyPreview,body,importance,hasAttachments,conversationId,isRead,categories",
            "$top": 100,
        }
        async for page in self.get_delta(path, delta_link, params):
            yield page

    async def get_calendar_events(self, start: datetime, end: datetime) -> list[dict]:
        params = {
            "$filter": f"start/dateTime ge '{start.isoformat()}' and end/dateTime le '{end.isoformat()}'",
            "$select": "id,subject,start,end,attendees,location,isOnlineMeeting,onlineMeetingUrl",
            "$orderby": "start/dateTime",
            "$top": 100,
        }
        result = await self.get("/me/calendar/events", params)
        return result.get("value", [])

    async def get_contacts(self, params: dict = None) -> AsyncIterator[dict]:
        default_params = {
            "$select": "id,emailAddresses,displayName,givenName,surname",
            "$top": 100,
        }
        if params:
            default_params.update(params)
        async for page in self.get_paginated("/me/contacts", default_params):
            yield page