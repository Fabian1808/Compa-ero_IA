from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import json

from app.memory.vector_store import VectorStore
from app.memory.embedder import Embedder
from app.ai.provider import AIProvider
from app.config import settings
from app.models.email import Email
from app.models.task import Task
from app.models.project import Project
from app.models.commitment import Commitment
from app.models.followup import FollowUp
from app.models.meeting import Meeting
from app.models.teams import TeamsMessage, TeamsChat
from app.models.onedrive import OneDriveFile
from app.models.sharepoint import SharePointItem, SharePointListItem


class Retriever:
    """Service for retrieving relevant context using semantic search."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self.vector_store = VectorStore(settings.qdrant_path)
        self.ai_provider: Optional[AIProvider] = None
        self._embedder: Optional[Embedder] = None

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            if self.ai_provider is None:
                from app.ai.ollama_provider import OllamaProvider
                from app.ai.provider import AIProviderConfig
                config = AIProviderConfig(
                    provider="ollama",
                    base_url=settings.ollama_base_url,
                    chat_model=settings.ollama_chat_model,
                    embed_model=settings.ollama_embed_model,
                )
                self.ai_provider = OllamaProvider(config)
            self._embedder = Embedder(self.ai_provider)
        return self._embedder

    async def index_email(self, email_id: str) -> bool:
        """Index a single email for semantic search."""
        from sqlalchemy import select
        from app.models.email import Email
        
        result = await self.db.execute(select(Email).where(Email.id == email_id))
        email = result.scalar_one_or_none()
        if not email:
            return False

        content = f"Subject: {email.subject}\nFrom: {email.sender_name} <{email.sender_email}>\n\n{email.body_text or email.body_preview or ''}"
        metadata = {
            "type": "email",
            "source_id": email.id,
            "subject": email.subject,
            "sender": email.sender_email,
            "received_at": email.received_at.isoformat(),
            "thread_id": email.thread_id,
        }

        await self.embedder.embed_and_store(
            texts=[content],
            metadata=[metadata],
            user_id=self.user_id,
            vector_store=self.vector_store
        )
        return True

    async def index_task(self, task_id: str) -> bool:
        """Index a single task for semantic search."""
        from sqlalchemy import select
        from app.models.task import Task
        
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if not task:
            return False

        content = f"Task: {task.title}\n{task.description or ''}\nProject: {task.project.name if task.project else 'None'}\nStatus: {task.status.value}\nPriority: {task.priority.value}"
        metadata = {
            "type": "task",
            "source_id": task.id,
            "title": task.title,
            "status": task.status.value,
            "priority": task.priority.value,
            "project_id": task.project_id,
            "deadline": task.deadline_at.isoformat() if task.deadline_at else None,
        }

        await self.embedder.embed_and_store(
            texts=[content],
            metadata=[metadata],
            user_id=self.user_id,
            vector_store=self.vector_store
        )
        return True

    async def index_project(self, project_id: str) -> bool:
        """Index a single project for semantic search."""
        from sqlalchemy import select
        from app.models.project import Project
        
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            return False

        content = f"Project: {project.name}\n{project.description or ''}\nStatus: {project.status.value}\nProgress: {project.progress}%"
        metadata = {
            "type": "project",
            "source_id": project.id,
            "name": project.name,
            "status": project.status.value,
            "progress": project.progress,
        }

        await self.embedder.embed_and_store(
            texts=[content],
            metadata=[metadata],
            user_id=self.user_id,
            vector_store=self.vector_store
        )
        return True

    async def index_commitment(self, commitment_id: str) -> bool:
        """Index a single commitment for semantic search."""
        from sqlalchemy import select
        from app.models.commitment import Commitment
        
        result = await self.db.execute(select(Commitment).where(Commitment.id == commitment_id))
        commitment = result.scalar_one_or_none()
        if not commitment:
            return False

        content = f"Compromiso: {commitment.description}\nFecha límite: {commitment.due_date.isoformat() if commitment.due_date else 'Sin fecha'}\nEstado: {commitment.status.value}"
        metadata = {
            "type": "commitment",
            "source_id": commitment.id,
            "description": commitment.description,
            "due_date": commitment.due_date.isoformat() if commitment.due_date else None,
            "status": commitment.status.value,
        }

        await self.embedder.embed_and_store(
            texts=[content],
            metadata=[metadata],
            user_id=self.user_id,
            vector_store=self.vector_store
        )
        return True

    async def index_teams_message(self, message_id: str) -> bool:
        """Index a Teams message for semantic search."""
        from sqlalchemy import select
        from app.models.teams import TeamsMessage
        
        result = await self.db.execute(select(TeamsMessage).where(TeamsMessage.id == message_id))
        message = result.scalar_one_or_none()
        if not message:
            return False

        content = f"Teams message from {message.sender_name} in chat {message.chat_id}: {message.body_text or message.body_html or ''}"
        metadata = {
            "type": "teams_message",
            "source_id": message.id,
            "chat_id": message.chat_id,
            "sender": message.sender_name,
            "sent_at": message.sent_at.isoformat(),
        }

        await self.embedder.embed_and_store(
            texts=[content],
            metadata=[metadata],
            user_id=self.user_id,
            vector_store=self.vector_store
        )
        return True

    async def index_onedrive_file(self, file_id: str) -> bool:
        """Index a OneDrive file for semantic search."""
        from sqlalchemy import select
        from app.models.onedrive import OneDriveFile
        
        result = await self.db.execute(select(OneDriveFile).where(OneDriveFile.id == file_id))
        file_obj = result.scalar_one_or_none()
        if not file_obj:
            return False

        content = f"File: {file_obj.name}\nType: {file_obj.file_type}\nPath: {file_obj.path or 'Root'}"
        metadata = {
            "type": "onedrive_file",
            "source_id": file_obj.id,
            "name": file_obj.name,
            "file_type": file_obj.file_type,
            "mime_type": file_obj.mime_type,
            "size": file_obj.size,
            "path": file_obj.path,
            "last_modified": file_obj.last_modified_at.isoformat(),
        }

        await self.embedder.embed_and_store(
            texts=[content],
            metadata=[metadata],
            user_id=self.user_id,
            vector_store=self.vector_store
        )
        return True

    async def index_sharepoint_item(self, item_id: str) -> bool:
        """Index a SharePoint item for semantic search."""
        from sqlalchemy import select
        from app.models.sharepoint import SharePointItem
        
        result = await self.db.execute(select(SharePointItem).where(SharePointItem.id == item_id))
        item = result.scalar_one_or_none()
        if not item:
            return False

        content = f"SharePoint item: {item.name}\nType: {item.item_type}\nPath: {item.path or 'Root'}"
        metadata = {
            "type": "sharepoint_item",
            "source_id": item.id,
            "name": item.name,
            "item_type": item.item_type,
            "mime_type": item.mime_type,
            "size": item.size,
            "path": item.path,
            "last_modified": item.last_modified_at.isoformat(),
        }

        await self.embedder.embed_and_store(
            texts=[content],
            metadata=[metadata],
            user_id=self.user_id,
            vector_store=self.vector_store
        )
        return True

    async def search(
        self,
        query: str,
        limit: int = 10,
        types: List[str] = None,
        date_from: str = None,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for relevant content across all indexed sources."""
        filter_metadata = {"user_id": self.user_id}
        if types:
            filter_metadata["type"] = types

        results = await self.embedder.search_similar(
            query=query,
            user_id=self.user_id,
            vector_store=self.vector_store,
            limit=limit,
            score_threshold=0.6,  # Lower threshold for broader recall
            filter_metadata=filter_metadata if types else {"user_id": self.user_id}
        )

        # Filter by type if specified
        if types:
            results = [r for r in results if r["payload"].get("type") in types]

        return results

    async def search_by_type(self, query: str, content_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for content of a specific type."""
        return await self.search(query, limit=limit, types=[content_type])

    async def get_context_for_ai(self, query: str, max_tokens: int = 2000) -> str:
        """Get formatted context for AI prompts."""
        results = await self.search(query, limit=10, score_threshold=0.6)
        
        if not results:
            return "No se encontró información relevante."

        context_parts = []
        token_count = 0
        
        for result in results:
            payload = result["payload"]
            content = payload.get("content", "")
            source_type = payload.get("type", "unknown")
            
            # Estimate tokens (rough approximation: 1 token ≈ 4 chars)
            estimated_tokens = len(content) // 4
            if token_count + estimated_tokens > max_tokens:
                break
            
            context_parts.append(f"[{source_type.upper()}] {content}")
            token_count += estimated_tokens

        return "\n\n---\n\n".join(context_parts)

    async def reindex_all(self, batch_size: int = 100) -> Dict[str, int]:
        """Reindex all content for the user."""
        counts = {"emails": 0, "tasks": 0, "projects": 0, "commitments": 0, "teams_messages": 0}
        
        # Reindex emails
        from sqlalchemy import select
        from app.models.email import Email
        stmt = select(Email).where(Email.account.has(user_id=self.user_id)).limit(1000)
        result = await self.db.execute(stmt)
        for email in result.scalars().all():
            await self.index_email(email.id)
            counts["emails"] += 1

        # Reindex tasks
        from app.models.task import Task
        stmt = select(Task).where(Task.user_id == self.user_id)
        result = await self.db.execute(stmt)
        for task in result.scalars().all():
            await self.index_task(task.id)
            counts["tasks"] += 1

        # Reindex projects
        from app.models.project import Project
        stmt = select(Project).where(Project.user_id == self.user_id)
        result = await self.db.execute(stmt)
        for project in result.scalars().all():
            await self.index_project(project.id)
            counts["projects"] += 1

        # Reindex commitments
        from app.models.commitment import Commitment
        stmt = select(Commitment).where(Commitment.user_id == self.user_id)
        result = await self.db.execute(stmt)
        for commitment in result.scalars().all():
            await self.index_commitment(commitment.id)
            counts["commitments"] += 1

        return counts