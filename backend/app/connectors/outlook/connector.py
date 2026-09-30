import json
import uuid
from datetime import datetime
from typing import AsyncIterator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.connectors.base import Connector, SyncResult
from app.services.graph_service import GraphService
from app.models.account import Account
from app.models.email import Email, EmailThread
from app.models.contact import Contact
from app.models.meeting import Meeting
from app.config import settings


class OutlookConnector(Connector):
    """Microsoft Outlook connector using Microsoft Graph API."""

    def __init__(self, graph_service: GraphService, account: Account):
        self.graph_service = graph_service
        self.account = account
        self._client = None

    @property
    def name(self) -> str:
        return "outlook"

    @property
    def required_scopes(self) -> list[str]:
        return settings.ms_graph_scopes_list

    async def authenticate(self, credentials: dict) -> bool:
        return await self.graph_service.authenticate(self.account)

    async def test_connection(self) -> bool:
        try:
            async with self.graph_service.create_client(self.account) as client:
                await client.get_user()
                return True
        except Exception:
            return False

    async def sync_incremental(
        self,
        since: datetime | None = None,
        cursor: str | None = None
    ) -> AsyncIterator[SyncResult]:
        """Sync messages, contacts, and calendar events incrementally."""
        delta_link = cursor or self.account.meta.get("delta_link_messages")
        result = SyncResult()

        async with self.graph_service.create_client(self.account) as client:
            try:
                async for page in client.get_messages_delta("inbox", delta_link):
                    for msg_data in page.get("value", []):
                        if "@removed" in msg_data:
                            await self._soft_delete_email(msg_data["id"])
                            result.items_deleted += 1
                        else:
                            is_new = await self._upsert_email(msg_data, client)
                            if is_new:
                                result.items_created += 1
                            else:
                                result.items_updated += 1
                            result.items_processed += 1

                    # Update delta link
                    if "@odata.deltaLink" in page:
                        self.account.meta["delta_link_messages"] = page["@odata.deltaLink"]
                        await self.db.flush()
                        result.next_cursor = page["@odata.deltaLink"]

                    yield result
                    result = SyncResult()

            except Exception as e:
                result.errors.append(str(e))
                yield result

            # Sync contacts
            async for page in client.get_contacts():
                for contact_data in page.get("value", []):
                    await self._upsert_contact(contact_data)
                yield SyncResult(items_processed=len(page.get("value", [])))

            # Sync calendar events (last 30 days, next 90 days)
            start = datetime.utcnow().replace(day=1)
            end = start.replace(month=start.month + 3 if start.month < 10 else 1, year=start.year + (1 if start.month > 9 else 0))
            events = await client.get_calendar_events(start, end)
            for event_data in events:
                await self._upsert_meeting(event_data)
            yield SyncResult(items_processed=len(events))

    async def get_item(self, item_id: str) -> Optional[dict]:
        try:
            async with self.graph_service.create_client(self.account) as client:
                return await client.get(f"/me/messages/{item_id}")
        except Exception:
            return None

    async def search(self, query: str, limit: int = 50) -> list[dict]:
        try:
            async with self.graph_service.create_client(self.account) as client:
                params = {
                    "$search": f"\"{query}\"",
                    "$select": "id,subject,from,toRecipients,receivedDateTime,bodyPreview,importance,hasAttachments,conversationId,isRead",
                    "$top": limit,
                }
                result = await client.get("/me/messages", params)
                return result.get("value", [])
        except Exception:
            return []

    async def _upsert_email(self, msg_data: dict, client) -> bool:
        """Insert or update email. Returns True if new."""
        graph_id = msg_data["id"]

        result = await self.db.execute(select(Email).where(Email.graph_id == graph_id))
        email = result.scalar_one_or_none()

        sender = msg_data.get("from", {}).get("emailAddress", {})
        recipients = msg_data.get("toRecipients", [])

        email_data = {
            "account_id": self.account.id,
            "graph_id": graph_id,
            "subject": msg_data.get("subject", ""),
            "body_preview": msg_data.get("bodyPreview"),
            "body_text": msg_data.get("body", {}).get("content") if msg_data.get("body") else None,
            "sender_email": sender.get("address", ""),
            "sender_name": sender.get("name"),
            "recipients_json": json.dumps([{"address": r["emailAddress"]["address"], "name": r["emailAddress"].get("name")} for r in recipients]),
            "received_at": datetime.fromisoformat(msg_data["receivedDateTime"].replace("Z", "+00:00")),
            "has_attachments": msg_data.get("hasAttachments", False),
            "importance": msg_data.get("importance", "normal"),
            "categories_json": json.dumps(msg_data.get("categories", [])),
            "is_read": msg_data.get("isRead", False),
            "raw_json": json.dumps(msg_data),
        }

        conversation_id = msg_data.get("conversationId")
        if conversation_id:
            thread = await self._get_or_create_thread(conversation_id, msg_data.get("subject", ""))
            email_data["thread_id"] = thread.id

        if email is None:
            email = Email(id=str(uuid.uuid4()), **email_data)
            self.db.add(email)
            return True
        else:
            for key, value in email_data.items():
                setattr(email, key, value)
            return False

    async def _get_or_create_thread(self, conversation_id: str, subject: str) -> EmailThread:
        result = await self.db.execute(
            select(EmailThread).where(EmailThread.graph_thread_id == conversation_id)
        )
        thread = result.scalar_one_or_none()

        if thread is None:
            thread = EmailThread(
                id=str(uuid.uuid4()),
                account_id=self.account.id,
                graph_thread_id=conversation_id,
                subject=subject,
                participants_json="[]",
                last_message_at=datetime.utcnow(),
                message_count=0,
            )
            self.db.add(thread)
            await self.db.flush()

        return thread

    async def _soft_delete_email(self, graph_id: str) -> None:
        result = await self.db.execute(select(Email).where(Email.graph_id == graph_id))
        email = result.scalar_one_or_none()
        if email:
            await self.db.delete(email)

    async def _upsert_contact(self, contact_data: dict) -> None:
        graph_id = contact_data["id"]
        emails = contact_data.get("emailAddresses", [])
        primary_email = emails[0]["address"] if emails else ""

        if not primary_email:
            return

        result = await self.db.execute(
            select(Contact).where(Contact.account_id == self.account.id, Contact.email == primary_email)
        )
        contact = result.scalar_one_or_none()

        contact_data_clean = {
            "account_id": self.account.id,
            "graph_id": graph_id,
            "email": primary_email,
            "name": contact_data.get("displayName"),
            "display_name": contact_data.get("displayName"),
            "is_frequent": False,
        }

        if contact is None:
            contact = Contact(id=str(uuid.uuid4()), **contact_data_clean)
            self.db.add(contact)
        else:
            for key, value in contact_data_clean.items():
                setattr(contact, key, value)

    async def _upsert_meeting(self, event_data: dict) -> None:
        graph_id = event_data["id"]

        result = await self.db.execute(
            select(Meeting).where(Meeting.graph_id == graph_id)
        )
        meeting = result.scalar_one_or_none()

        start = event_data["start"]
        end = event_data["end"]
        attendees = event_data.get("attendees", [])
        location = event_data.get("location", {})
        is_online = event_data.get("isOnlineMeeting", False)
        meeting_url = event_data.get("onlineMeetingUrl")

        meeting_data = {
            "account_id": self.account.id,
            "graph_id": graph_id,
            "subject": event_data.get("subject", ""),
            "start_at": datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00")),
            "end_at": datetime.fromisoformat(end["dateTime"].replace("Z", "+00:00")),
            "attendees_json": json.dumps([
                {"email": a["emailAddress"]["address"], "name": a["emailAddress"].get("name"), "status": a.get("status", {}).get("response")}
                for a in attendees
            ]),
            "location": location.get("displayName") if location else None,
            "is_online": is_online,
            "meeting_url": meeting_url,
        }

        if meeting is None:
            meeting = Meeting(id=str(uuid.uuid4()), **meeting_data)
            self.db.add(meeting)
        else:
            for key, value in meeting_data.items():
                setattr(meeting, key, value)

    # Need to access db from the graph_service
    @property
    def db(self) -> AsyncSession:
        return self.graph_service.db