from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.memory.retriever import Retriever
from app.events.bus import event_bus
from app.events.events import EventType
from app.models.email import Email
from app.models.task import Task
from app.models.project import Project
from app.models.commitment import Commitment
from app.models.teams import TeamsMessage
from app.models.onedrive import OneDriveFile
from app.models.sharepoint import SharePointItem, SharePointListItem

logger = logging.getLogger(__name__)


class Indexer:
    """Service for automatically indexing content as it's created/updated."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def on_email_created(self, email_id: str, user_id: str) -> None:
        """Index a newly created email."""
        retriever = Retriever(self.db, user_id)
        try:
            await retriever.index_email(email_id)
        except Exception as e:
            logger.error(f"Failed to index email {email_id}: {e}")

    async def on_email_updated(self, email_id: str, user_id: str) -> None:
        """Reindex an updated email."""
        await self.on_email_created(email_id, user_id)

    async def on_task_created(self, task_id: str, user_id: str) -> None:
        """Index a newly created task."""
        retriever = Retriever(self.db, user_id)
        try:
            await retriever.index_task(task_id)
        except Exception as e:
            logger.error(f"Failed to index task {task_id}: {e}")

    async def on_task_updated(self, task_id: str, user_id: str) -> None:
        """Reindex an updated task."""
        await self.on_task_created(task_id, user_id)

    async def on_project_created(self, project_id: str, user_id: str) -> None:
        """Index a newly created project."""
        retriever = Retriever(self.db, user_id)
        try:
            await retriever.index_project(project_id)
        except Exception as e:
            logger.error(f"Failed to index project {project_id}: {e}")

    async def on_commitment_created(self, commitment_id: str, user_id: str) -> None:
        """Index a newly created commitment."""
        retriever = Retriever(self.db, user_id)
        try:
            await retriever.index_commitment(commitment_id)
        except Exception as e:
            logger.error(f"Failed to index commitment {commitment_id}: {e}")

    async def on_teams_message_created(self, message_id: str, user_id: str) -> None:
        """Index a newly created Teams message."""
        retriever = Retriever(self.db, user_id)
        try:
            await retriever.index_teams_message(message_id)
        except Exception as e:
            logger.error(f"Failed to index Teams message {message_id}: {e}")

    async def on_onedrive_file_created(self, file_id: str, user_id: str) -> None:
        """Index a newly created OneDrive file."""
        retriever = Retriever(self.db, user_id)
        try:
            await retriever.index_onedrive_file(file_id)
        except Exception as e:
            logger.error(f"Failed to index OneDrive file {file_id}: {e}")

    async def on_sharepoint_item_created(self, item_id: str, user_id: str) -> None:
        """Index a newly created SharePoint item."""
        retriever = Retriever(self.db, user_id)
        try:
            await retriever.index_sharepoint_item(item_id)
        except Exception as e:
            logger.error(f"Failed to index SharePoint item {item_id}: {e}")

    async def reindex_user_all(self, user_id: str) -> Dict[str, int]:
        """Reindex all content for a user."""
        retriever = Retriever(None, user_id)  # Will need db session
        # This would need a proper db session
        return {"reindexed": 0}


# Event handlers for automatic indexing
async def handle_email_synced(event):
    """Handle email synced event."""
    from app.database import async_session_maker
    async with async_session_maker() as db:
        from app.memory.indexer import Indexer
        indexer = Indexer(db)
        await indexer.on_email_created(event.payload.get("email_id"), event.user_id)


async def handle_task_created(event):
    """Handle task created event."""
    from app.database import async_session_maker
    async with async_session_maker() as db:
        from app.memory.indexer import Indexer
        indexer = Indexer(db)
        await indexer.on_task_created(event.payload.get("task_id"), event.user_id)


async def handle_teams_message_synced(event):
    """Handle Teams message synced event."""
    from app.database import async_session_maker
    async with async_session_maker() as db:
        from app.memory.indexer import Indexer
        indexer = Indexer(db)
        await indexer.on_teams_message_created(event.payload.get("message_id"), event.user_id)