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

    # Teams methods
    async def get_chats(self, params: dict = None) -> AsyncIterator[dict]:
        default_params = {
            "$select": "id,topic,chatType,createdDateTime,lastUpdatedDateTime,members",
            "$top": 50,
            "$orderby": "lastUpdatedDateTime desc",
        }
        if params:
            default_params.update(params)
        async for page in self.get_paginated("/me/chats", default_params):
            yield page

    async def get_joined_teams(self, params: dict = None) -> AsyncIterator[dict]:
        default_params = {
            "$select": "id,displayName,description",
            "$top": 50,
        }
        if params:
            default_params.update(params)
        async for page in self.get_paginated("/me/joinedTeams", default_params):
            yield page

    async def get_team_channels(self, team_id: str, params: dict = None) -> AsyncIterator[dict]:
        default_params = {
            "$select": "id,displayName,description,membershipType",
            "$top": 100,
        }
        if params:
            default_params.update(params)
        async for page in self.get_paginated(f"/teams/{team_id}/channels", default_params):
            yield page

    async def get_channel_messages(self, team_id: str, channel_id: str, params: dict = None) -> AsyncIterator[dict]:
        default_params = {
            "$select": "id,createdDateTime,lastModifiedDateTime,from,body,subject",
            "$top": 50,
            "$orderby": "lastModifiedDateTime desc",
        }
        if params:
            default_params.update(params)
        async for page in self.get_paginated(f"/teams/{team_id}/channels/{channel_id}/messages", default_params):
            yield page

    # OneDrive methods
    async def get_drive(self) -> dict:
        return await self.get("/me/drive")

    async def get_drive_delta(self, params: dict = None) -> AsyncIterator[dict]:
        default_params = {
            "$select": "id,name,createdDateTime,lastModifiedDateTime,size,file,folder,webUrl,parentReference",
        }
        if params:
            default_params.update(params)
        async for page in self.get_delta("/me/drive/root/delta", None, default_params):
            yield page

    async def search_drive(self, query: str, params: dict = None) -> AsyncIterator[dict]:
        default_params = {
            "$select": "id,name,createdDateTime,lastModifiedDateTime,size,file,folder,webUrl",
            "$top": 50,
        }
        if params:
            default_params.update(params)
        async for page in self.get_paginated(f"/me/drive/root/search(q='{query}')", default_params):
            yield page

    # SharePoint methods
    async def get_followed_sites(self, params: dict = None) -> AsyncIterator[dict]:
        default_params = {
            "$select": "id,displayName,webUrl,createdDateTime,lastModifiedDateTime",
            "$top": 50,
        }
        if params:
            default_params.update(params)
        async for page in self.get_paginated("/me/followedSites", default_params):
            yield page

    async def get_site_lists(self, site_id: str, params: dict = None) -> AsyncIterator[dict]:
        default_params = {
            "$select": "id,displayName,createdDateTime,lastModifiedDateTime,list",
            "$top": 100,
        }
        if params:
            default_params.update(params)
        async for page in self.get_paginated(f"/sites/{site_id}/lists", default_params):
            yield page

    async def get_list_items(self, site_id: str, list_id: str, params: dict = None) -> AsyncIterator[dict]:
        default_params = {
            "$select": "id,fields,createdDateTime,lastModifiedDateTime,webUrl",
            "$expand": "fields",
            "$top": 100,
        }
        if params:
            default_params.update(params)
        async for page in self.get_paginated(f"/sites/{site_id}/lists/{list_id}/items", default_params):
            yield page

    async def search_site(self, site_id: str, query: str, params: dict = None) -> AsyncIterator[dict]:
        default_params = {
            "$select": "id,name,webUrl,lastModifiedDateTime",
            "$top": 50,
        }
        if params:
            default_params.update(params)
        async for page in self.get_paginated(f"/sites/{site_id}/search(q='{query}')", default_params):
            yield page


class GraphService:
    """High-level Graph service that manages GraphClient lifecycle."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def create_client(self, account: Account) -> GraphClient:
        return GraphClient(self.db, account)

    async def authenticate(self, account: Account) -> bool:
        """Authenticate and test connection."""
        async with self.create_client(account) as client:
            try:
                await client.get_user()
                return True
            except Exception:
                return False

    async def get_user(self, account: Account) -> dict:
        async with self.create_client(account) as client:
            return await client.get_user()