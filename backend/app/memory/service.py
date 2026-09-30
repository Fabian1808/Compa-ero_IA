import hashlib
import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai import AIProviderConfig, OllamaProvider
from app.config import settings
from app.memory.qdrant_service import QdrantService
from app.models.ai_memory import AIMemory, Embedding
from app.models.commitment import Commitment
from app.models.email import Email
from app.models.followup import FollowUp
from app.models.meeting import Meeting
from app.models.project import Project
from app.models.task import Task


class MemoryService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

        config = AIProviderConfig(
            provider="ollama",
            base_url=settings.ollama_base_url,
            chat_model=settings.ollama_chat_model,
            embed_model=settings.ollama_embed_model,
        )
        self.ai_provider = OllamaProvider(config)
        self.qdrant = QdrantService(self.ai_provider)

    async def initialize(self) -> None:
        await self.qdrant.initialize()

    async def index_email(self, email: Email) -> str | None:
        """Index an email into semantic memory."""
        content_parts = [
            f"Asunto: {email.subject}",
            f"De: {email.sender_name} <{email.sender_email}>",
            f"Fecha: {email.received_at.strftime('%Y-%m-%d %H:%M')}",
        ]

        if email.body_text:
            content_parts.append(f"Contenido: {email.body_text[:3000]}")
        elif email.body_preview:
            content_parts.append(f"Vista previa: {email.body_preview}")

        content = "\n".join(content_parts)

        metadata = {
            "thread_id": email.thread_id,
            "is_read": email.is_read,
            "importance": email.importance,
            "has_attachments": email.has_attachments,
            "recipients": email.recipients_json,
        }

        vector_id = await self.qdrant.upsert_memory(
            user_id=self.user_id,
            content=content,
            source_type="email",
            source_id=email.id,
            metadata=metadata,
        )

        # Update SQL tracking
        await self._upsert_ai_memory(email.id, "email", vector_id, content, metadata)

        return vector_id

    async def index_task(self, task: Task) -> str | None:
        """Index a task into semantic memory."""
        content_parts = [
            f"Tarea: {task.title}",
        ]

        if task.description:
            content_parts.append(f"Descripción: {task.description}")
        if task.deadline_at:
            content_parts.append(f"Fecha límite: {task.deadline_at.strftime('%Y-%m-%d %H:%M')}")
        content_parts.append(f"Prioridad: {task.priority.value}")
        content_parts.append(f"Estado: {task.status.value}")

        if task.project:
            content_parts.append(f"Proyecto: {task.project.name}")

        content = "\n".join(content_parts)

        metadata = {
            "status": task.status.value,
            "priority": task.priority.value,
            "deadline_at": task.deadline_at.isoformat() if task.deadline_at else None,
            "project_id": task.project_id,
            "project_name": task.project.name if task.project else None,
            "estimated_minutes": task.estimated_minutes,
            "actual_minutes": task.actual_minutes,
        }

        vector_id = await self.qdrant.upsert_memory(
            user_id=self.user_id,
            content=content,
            source_type="task",
            source_id=task.id,
            metadata=metadata,
        )

        await self._upsert_ai_memory(task.id, "task", vector_id, content, metadata)

        return vector_id

    async def index_commitment(self, commitment: Commitment) -> str | None:
        """Index a commitment into semantic memory."""
        content_parts = [
            f"Compromiso: {commitment.description}",
        ]

        if commitment.due_date:
            content_parts.append(f"Fecha límite: {commitment.due_date.strftime('%Y-%m-%d')}")
        content_parts.append(f"Estado: {commitment.status.value}")
        content_parts.append(f"Confianza: {commitment.confidence_score}%")

        content = "\n".join(content_parts)

        metadata = {
            "status": commitment.status.value,
            "due_date": commitment.due_date.isoformat() if commitment.due_date else None,
            "confidence_score": commitment.confidence_score,
            "source_email_id": commitment.source_email_id,
            "related_task_id": commitment.related_task_id,
        }

        vector_id = await self.qdrant.upsert_memory(
            user_id=self.user_id,
            content=content,
            source_type="commitment",
            source_id=commitment.id,
            metadata=metadata,
        )

        await self._upsert_ai_memory(commitment.id, "commitment", vector_id, content, metadata)

        return vector_id

    async def index_followup(self, followup: FollowUp) -> str | None:
        """Index a followup into semantic memory."""
        content_parts = [
            f"Seguimiento: {followup.subject}",
            f"Contacto: {followup.contact_name or followup.contact_email}",
            f"Enviado: {followup.sent_at.strftime('%Y-%m-%d %H:%M')}",
            f"Estado: {followup.status.value}",
            f"Días esperando: {followup.days_waiting}",
        ]

        if followup.draft_response:
            content_parts.append(f"Borrador: {followup.draft_response}")

        content = "\n".join(content_parts)

        metadata = {
            "contact_email": followup.contact_email,
            "contact_name": followup.contact_name,
            "subject": followup.subject,
            "status": followup.status.value,
            "days_waiting": followup.days_waiting,
            "source_email_id": followup.source_email_id,
            "draft_response": followup.draft_response,
        }

        vector_id = await self.qdrant.upsert_memory(
            user_id=self.user_id,
            content=content,
            source_type="followup",
            source_id=followup.id,
            metadata=metadata,
        )

        await self._upsert_ai_memory(followup.id, "followup", vector_id, content, metadata)

        return vector_id

    async def index_meeting(self, meeting: Meeting) -> str | None:
        """Index a meeting into semantic memory."""
        content_parts = [
            f"Reunión: {meeting.subject}",
            f"Inicio: {meeting.start_at.strftime('%Y-%m-%d %H:%M')}",
            f"Fin: {meeting.end_at.strftime('%Y-%m-%d %H:%M')}",
        ]

        if meeting.organizer:
            content_parts.append(f"Organizador: {meeting.organizer}")
        if meeting.attendees_json:
            content_parts.append(f"Asistentes: {meeting.attendees_json}")
        if meeting.body_preview:
            content_parts.append(f"Detalles: {meeting.body_preview}")
        if meeting.meeting_url:
            content_parts.append(f"Enlace: {meeting.meeting_url}")

        content = "\n".join(content_parts)

        metadata = {
            "organizer": meeting.organizer,
            "attendees": meeting.attendees_json,
            "is_online": meeting.is_online,
            "meeting_url": meeting.meeting_url,
            "start_at": meeting.start_at.isoformat(),
            "end_at": meeting.end_at.isoformat(),
        }

        vector_id = await self.qdrant.upsert_memory(
            user_id=self.user_id,
            content=content,
            source_type="meeting",
            source_id=meeting.id,
            metadata=metadata,
        )

        await self._upsert_ai_memory(meeting.id, "meeting", vector_id, content, metadata)

        return vector_id

    async def index_project(self, project: Project) -> str | None:
        """Index a project into semantic memory."""
        content_parts = [
            f"Proyecto: {project.name}",
        ]

        if project.description:
            content_parts.append(f"Descripción: {project.description}")
        content_parts.append(f"Estado: {project.status}")
        content_parts.append(f"Progreso: {project.progress}%")

        content = "\n".join(content_parts)

        metadata = {
            "status": project.status,
            "progress": project.progress,
            "color": project.color,
            "parent_project_id": project.parent_project_id,
        }

        vector_id = await self.qdrant.upsert_memory(
            user_id=self.user_id,
            content=content,
            source_type="project",
            source_id=project.id,
            metadata=metadata,
        )

        await self._upsert_ai_memory(project.id, "project", vector_id, content, metadata)

        return vector_id

    async def _upsert_ai_memory(
        self,
        source_id: str,
        source_type: str,
        vector_id: str,
        content: str,
        metadata: dict,
    ) -> None:
        """Update SQL tracking tables."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Check if embedding exists
        stmt = select(Embedding).where(Embedding.vector_id == vector_id)
        result = await self.db.execute(stmt)
        embedding = result.scalar_one_or_none()

        if not embedding:
            embedding = Embedding(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                vector_id=vector_id,
                content_hash=content_hash,
                model=settings.ollama_embed_model,
                dimensions=768,
            )
            self.db.add(embedding)
            await self.db.flush()

        # Check if AIMemory exists
        stmt = select(AIMemory).where(
            AIMemory.user_id == self.user_id,
            AIMemory.source_type == source_type,
            AIMemory.source_id == source_id,
        )
        result = await self.db.execute(stmt)
        ai_memory = result.scalar_one_or_none()

        if not ai_memory:
            ai_memory = AIMemory(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                content=content[:10000],  # Truncate for storage
                embedding_id=embedding.id,
                source_type=source_type,
                source_id=source_id,
                metadata_json=json.dumps(metadata),
            )
            self.db.add(ai_memory)
        else:
            ai_memory.content = content[:10000]
            ai_memory.embedding_id = embedding.id
            ai_memory.metadata_json = json.dumps(metadata)

        await self.db.flush()

    async def search(
        self,
        query: str,
        limit: int = 10,
        source_types: list[str] | None = None,
    ) -> list[dict]:
        """Search across all indexed memory."""
        return await self.qdrant.search(
            user_id=self.user_id,
            query=query,
            limit=limit,
            source_types=source_types,
        )

    async def get_stats(self) -> dict:
        """Get memory statistics."""
        return await self.qdrant.get_stats(self.user_id)

    async def reindex_all(self) -> dict:
        """Reindex all user data from SQL to Qdrant."""
        await self.initialize()

        counts = {"email": 0, "task": 0, "commitment": 0, "followup": 0, "meeting": 0, "project": 0}

        # Index emails
        stmt = select(Email).where(Email.account.has(user_id=self.user_id))
        result = await self.db.execute(stmt)
        emails = result.scalars().all()
        for email in emails:
            await self.index_email(email)
            counts["email"] += 1

        # Index tasks
        stmt = select(Task).where(Task.user_id == self.user_id)
        result = await self.db.execute(stmt)
        tasks = result.scalars().all()
        for task in tasks:
            await self.index_task(task)
            counts["task"] += 1

        # Index commitments
        stmt = select(Commitment).where(Commitment.user_id == self.user_id)
        result = await self.db.execute(stmt)
        commitments = result.scalars().all()
        for c in commitments:
            await self.index_commitment(c)
            counts["commitment"] += 1

        # Index followups
        stmt = select(FollowUp).where(FollowUp.user_id == self.user_id)
        result = await self.db.execute(stmt)
        followups = result.scalars().all()
        for f in followups:
            await self.index_followup(f)
            counts["followup"] += 1

        # Index meetings
        stmt = select(Meeting).where(Meeting.account.has(user_id=self.user_id))
        result = await self.db.execute(stmt)
        meetings = result.scalars().all()
        for m in meetings:
            await self.index_meeting(m)
            counts["meeting"] += 1

        # Index projects
        stmt = select(Project).where(Project.user_id == self.user_id)
        result = await self.db.execute(stmt)
        projects = result.scalars().all()
        for p in projects:
            await self.index_project(p)
            counts["project"] += 1

        await self.db.commit()
        return counts

    async def delete_by_source(self, source_type: str, source_id: str) -> bool:
        """Delete memory entry by source."""
        # Delete from Qdrant
        success = await self.qdrant.delete_memory(self.user_id, source_type, source_id)

        # Delete from SQL
        stmt = select(AIMemory).where(
            AIMemory.user_id == self.user_id,
            AIMemory.source_type == source_type,
            AIMemory.source_id == source_id,
        )
        result = await self.db.execute(stmt)
        ai_memory = result.scalar_one_or_none()

        if ai_memory:
            # Delete embedding if no other memories reference it
            if ai_memory.embedding_id:
                stmt2 = select(AIMemory).where(AIMemory.embedding_id == ai_memory.embedding_id)
                result2 = await self.db.execute(stmt2)
                other_memories = result2.scalars().all()
                if len(other_memories) <= 1:
                    stmt3 = select(Embedding).where(Embedding.id == ai_memory.embedding_id)
                    result3 = await self.db.execute(stmt3)
                    embedding = result3.scalar_one_or_none()
                    if embedding:
                        await self.db.delete(embedding)

            await self.db.delete(ai_memory)
            await self.db.commit()

        return success
