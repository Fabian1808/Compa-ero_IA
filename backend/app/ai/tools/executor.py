import json
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.models.task import Task, TaskStatus
from app.models.meeting import Meeting
from app.models.email import Email
from app.models.followup import FollowUp
from app.memory.service import MemoryService


class ToolExecutor:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self._memory_service: MemoryService | None = None

    @property
    def memory_service(self) -> MemoryService:
        if self._memory_service is None:
            self._memory_service = MemoryService(self.db, self.user_id)
        return self._memory_service

    async def execute(self, tool_name: str, arguments: dict) -> Any:
        method = getattr(self, f"_{tool_name}", None)
        if not method:
            return {"error": f"Unknown tool: {tool_name}"}
        return await method(**arguments)

    async def _get_pending_tasks(
        self,
        project_id: str | None = None,
        status: list[str] | None = None,
        limit: int = 20
    ) -> dict:
        if status is None:
            status = ["pending", "in_progress", "blocked"]

        stmt = select(Task).where(
            Task.user_id == self.user_id,
            Task.status.in_([TaskStatus(s) for s in status])
        )
        if project_id:
            stmt = stmt.where(Task.project_id == project_id)
        stmt = stmt.order_by(Task.deadline_at.nulls_last(), Task.priority.desc()).limit(limit)

        result = await self.db.execute(stmt)
        tasks = result.scalars().all()

        return {
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status.value,
                    "priority": t.priority.value,
                    "deadline_at": t.deadline_at.isoformat() if t.deadline_at else None,
                    "estimated_minutes": t.estimated_minutes,
                    "project_id": t.project_id,
                }
                for t in tasks
            ]
        }

    async def _get_calendar_events(
        self,
        start_date: str,
        end_date: str
    ) -> dict:
        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        stmt = select(Meeting).where(
            Meeting.account.has(user_id=self.user_id),
            Meeting.start_at >= start,
            Meeting.end_at <= end
        ).order_by(Meeting.start_at)

        result = await self.db.execute(stmt)
        meetings = result.scalars().all()

        return {
            "events": [
                {
                    "id": m.id,
                    "subject": m.subject,
                    "start_at": m.start_at.isoformat(),
                    "end_at": m.end_at.isoformat(),
                    "is_online": m.is_online,
                    "meeting_url": m.meeting_url,
                }
                for m in meetings
            ]
        }

    async def _search_emails(
        self,
        query: str,
        limit: int = 10,
        since_days: int | None = None
    ) -> dict:
        stmt = select(Email).where(
            Email.account.has(user_id=self.user_id),
            Email.subject.ilike(f"%{query}%") | Email.body_preview.ilike(f"%{query}%")
        )
        if since_days:
            cutoff = datetime.utcnow() - timedelta(days=since_days)
            stmt = stmt.where(Email.received_at >= cutoff)
        stmt = stmt.order_by(Email.received_at.desc()).limit(limit)

        result = await self.db.execute(stmt)
        emails = result.scalars().all()

        return {
            "emails": [
                {
                    "id": e.id,
                    "subject": e.subject,
                    "sender_email": e.sender_email,
                    "sender_name": e.sender_name,
                    "received_at": e.received_at.isoformat(),
                    "body_preview": e.body_preview,
                }
                for e in emails
            ]
        }

    async def _create_task(
        self,
        title: str,
        description: str | None = None,
        deadline_at: str | None = None,
        estimated_minutes: int | None = None,
        project_id: str | None = None,
        source_email_id: str | None = None
    ) -> dict:
        # This tool only prepares the task - actual creation requires user confirmation
        return {
            "prepared_task": {
                "title": title,
                "description": description,
                "deadline_at": deadline_at,
                "estimated_minutes": estimated_minutes,
                "project_id": project_id,
                "source_email_id": source_email_id,
            },
            "requires_confirmation": True
        }

    async def _complete_task(
        self,
        task_id: str,
        actual_minutes: int | None = None
    ) -> dict:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == self.user_id)
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            return {"error": "Task not found"}

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        if actual_minutes:
            task.actual_minutes = actual_minutes

        await self.db.flush()
        return {"success": True, "task_id": task_id}

    async def _prepare_followup_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        original_email_id: str | None = None
    ) -> dict:
        # Just prepare the draft - don't send
        followup = FollowUp(
            id="temp-" + str(hash(to_email + subject))[:8],
            user_id=self.user_id,
            source_email_id=original_email_id,
            contact_email=to_email,
            subject=subject,
            sent_at=datetime.utcnow(),
            status="draft_prepared",
            draft_response=body,
        )

        return {
            "draft": {
                "to": to_email,
                "subject": subject,
                "body": body,
            },
            "requires_confirmation": True
        }

    async def _semantic_search(
        self,
        query: str,
        limit: int = 10,
        source_types: list[str] | None = None
    ) -> dict:
        """Semantic search across all indexed memory."""
        await self.memory_service.initialize()
        results = await self.memory_service.search(
            query=query,
            limit=limit,
            source_types=source_types,
        )
        
        return {
            "results": [
                {
                    "content": r["content"][:300],
                    "source_type": r["source_type"],
                    "source_id": r["source_id"],
                    "score": r["score"],
                    "metadata": r["metadata"],
                    "search_type": r["search_type"],
                }
                for r in results
            ],
            "total": len(results),
        }