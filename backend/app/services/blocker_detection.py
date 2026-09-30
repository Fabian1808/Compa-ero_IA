from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.bus import EventType, event_bus
from app.models.commitment import Commitment, CommitmentStatus
from app.models.followup import FollowUp, FollowUpStatus
from app.models.meeting import Meeting
from app.models.project import Project
from app.models.task import DependencyType, Task, TaskDependency, TaskStatus


class BlockerDetector:
    """Automatic detection of blockers and dependencies between work items."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def detect_all_blockers(self) -> list[dict]:
        """Run all blocker detection algorithms and return detected blockers."""
        blockers = []

        # 1. Task dependency blockers (explicit dependencies)
        blockers.extend(await self._detect_task_dependency_blockers())

        # 2. Commitment-based blockers (waiting for others)
        blockers.extend(await self._detect_commitment_blockers())

        # 3. Follow-up blockers (no response to sent emails)
        blockers.extend(await self._detect_followup_blockers())

        # 4. Meeting-related blockers (decisions needed in meetings)
        blockers.extend(await self._detect_meeting_blockers())

        # 5. Resource contention (same person assigned to parallel critical tasks)
        blockers.extend(await self._detect_resource_contention())

        # 6. Deadline cascade blockers (upstream task delay affects downstream)
        blockers.extend(await self._detect_deadline_cascade())

        return blockers

    async def _detect_task_dependency_blockers(self) -> list[dict]:
        """Find tasks blocked by incomplete dependencies."""
        blockers = []

        # Get all pending/in_progress tasks with dependencies
        stmt = select(Task).where(
            Task.user_id == self.user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        )
        result = await self.db.execute(stmt)
        tasks = result.scalars().all()

        for task in tasks:
            # Get blocking dependencies
            dep_stmt = select(TaskDependency).where(
                TaskDependency.task_id == task.id,
                TaskDependency.dependency_type.in_([DependencyType.BLOCKS, DependencyType.RELATES_TO])
            )
            dep_result = await self.db.execute(dep_stmt)
            dependencies = dep_result.scalars().all()

            blocking_tasks = []
            for dep in dependencies:
                dep_task_stmt = select(Task).where(Task.id == dep.depends_on_task_id)
                dep_task_result = await self.db.execute(dep_task_stmt)
                dep_task = dep_task_result.scalar_one_or_none()

                if dep_task and dep_task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                    blocking_tasks.append({
                        "task_id": dep_task.id,
                        "title": dep_task.title,
                        "status": dep_task.status.value,
                        "dependency_type": dep.dependency_type.value,
                    })

            if blocking_tasks:
                blockers.append({
                    "type": "task_dependency",
                    "blocked_task_id": task.id,
                    "blocked_task_title": task.title,
                    "blocking_tasks": blocking_tasks,
                    "severity": "high" if any(bt["dependency_type"] == "blocks" for bt in blocking_tasks) else "medium",
                    "suggested_action": "Completa las tareas bloqueantes primero" if any(bt["dependency_type"] == "blocks" for bt in blocking_tasks) else "Revisa tareas relacionadas",
                    "detected_at": datetime.utcnow().isoformat(),
                })

        return blockers

    async def _detect_commitment_blockers(self) -> list[dict]:
        """Find commitments that are blocking work (waiting for others to deliver)."""
        blockers = []

        stmt = select(Commitment).where(
            Commitment.user_id == self.user_id,
            Commitment.status.in_([CommitmentStatus.PENDING, CommitmentStatus.CONFIRMED]),
            Commitment.due_date < datetime.utcnow() + timedelta(days=7)
        )
        result = await self.db.execute(stmt)
        commitments = result.scalars().all()

        for commitment in commitments:
            days_until_due = (commitment.due_date - datetime.utcnow()).days if commitment.due_date else 999

            # Check if there's a related task that's stuck
            related_task = None
            if commitment.related_task_id:
                task_stmt = select(Task).where(Task.id == commitment.related_task_id)
                task_result = await self.db.execute(task_stmt)
                related_task = task_result.scalar_one_or_none()

            blockers.append({
                "type": "commitment_waiting",
                "commitment_id": commitment.id,
                "description": commitment.description,
                "due_date": commitment.due_date.isoformat() if commitment.due_date else None,
                "days_until_due": days_until_due,
                "related_task": {
                    "id": related_task.id,
                    "title": related_task.title,
                    "status": related_task.status.value,
                } if related_task else None,
                "severity": "high" if days_until_due <= 2 else "medium" if days_until_due <= 5 else "low",
                "suggested_action": f"Seguimiento: {commitment.description}" if days_until_due <= 2 else "Programar seguimiento",
                "detected_at": datetime.utcnow().isoformat(),
            })

        return blockers

    async def _detect_followup_blockers(self) -> list[dict]:
        """Find follow-ups without response that are blocking progress."""
        blockers = []

        stmt = select(FollowUp).where(
            FollowUp.user_id == self.user_id,
            FollowUp.status.in_([FollowUpStatus.PENDING, FollowUpStatus.REMINDER_SENT]),
            FollowUp.days_waiting > 3
        )
        result = await self.db.execute(stmt)
        followups = result.scalars().all()

        for followup in followups:
            blockers.append({
                "type": "followup_no_response",
                "followup_id": followup.id,
                "subject": followup.subject,
                "contact": followup.contact_name or followup.contact_email,
                "days_waiting": followup.days_waiting,
                "has_draft": bool(followup.draft_response),
                "severity": "high" if followup.days_waiting > 7 else "medium",
                "suggested_action": "Enviar recordatorio" if not followup.draft_response else "Revisar y enviar borrador",
                "detected_at": datetime.utcnow().isoformat(),
            })

        return blockers

    async def _detect_meeting_blockers(self) -> list[dict]:
        """Find meetings where decisions are needed but not made."""
        blockers = []

        now = datetime.utcnow()
        soon = now + timedelta(hours=24)

        stmt = select(Meeting).where(
            Meeting.account.has(user_id=self.user_id),
            Meeting.start_at >= now,
            Meeting.start_at <= soon,
            or_(
                Meeting.subject.ilike("%decision%"),
                Meeting.subject.ilike("%aprob%"),
                Meeting.subject.ilike("%review%"),
                Meeting.subject.ilike("%revisión%"),
                Meeting.subject.ilike("%approval%"),
                Meeting.subject.ilike("%kickoff%"),
                Meeting.subject.ilike("%inicio%"),
            )
        )
        result = await self.db.execute(stmt)
        meetings = result.scalars().all()

        for meeting in meetings:
            hours_until = (meeting.start_at - now).total_seconds() / 3600
            blockers.append({
                "type": "meeting_decision_needed",
                "meeting_id": meeting.id,
                "subject": meeting.subject,
                "start_at": meeting.start_at.isoformat(),
                "hours_until": round(hours_until, 1),
                "is_online": meeting.is_online,
                "meeting_url": meeting.meeting_url,
                "severity": "high" if hours_until < 4 else "medium",
                "suggested_action": "Preparar puntos de decisión" if hours_until < 4 else "Agendar preparación",
                "detected_at": datetime.utcnow().isoformat(),
            })

        return blockers

    async def _detect_resource_contention(self) -> list[dict]:
        """Detect when user has too many high-priority tasks in parallel."""
        blockers = []

        stmt = select(Task).where(
            Task.user_id == self.user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            Task.priority.in_(["high", "critical"])
        )
        result = await self.db.execute(stmt)
        high_priority_tasks = result.scalars().all()

        # Group by project
        by_project = defaultdict(list)
        for task in high_priority_tasks:
            if task.project_id:
                by_project[task.project_id].append(task)

        for project_id, tasks in by_project.items():
            if len(tasks) > 3:
                project_stmt = select(Project).where(Project.id == project_id)
                project_result = await self.db.execute(project_stmt)
                project = project_result.scalar_one_or_none()

                blockers.append({
                    "type": "resource_contention",
                    "project_id": project_id,
                    "project_name": project.name if project else "Sin proyecto",
                    "task_count": len(tasks),
                    "tasks": [{"id": t.id, "title": t.title, "status": t.status.value} for t in tasks],
                    "severity": "medium",
                    "suggested_action": "Priorizar y secuenciar tareas",
                    "detected_at": datetime.utcnow().isoformat(),
                })

        return blockers

    async def _detect_deadline_cascade(self) -> list[dict]:
        """Detect deadline cascades where upstream delay affects downstream."""
        blockers = []

        # Find chains of dependent tasks where upstream is delayed
        stmt = select(TaskDependency).where(
            TaskDependency.dependency_type == DependencyType.BLOCKS
        )
        result = await self.db.execute(stmt)
        dependencies = result.scalars().all()

        for dep in dependencies:
            upstream_stmt = select(Task).where(Task.id == dep.depends_on_task_id)
            upstream_result = await self.db.execute(upstream_stmt)
            upstream = upstream_result.scalar_one_or_none()

            downstream_stmt = select(Task).where(Task.id == dep.task_id)
            downstream_result = await self.db.execute(downstream_stmt)
            downstream = downstream_result.scalar_one_or_none()

            if upstream and downstream:
                if (upstream.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS] and
                    upstream.deadline_at and upstream.deadline_at < datetime.utcnow() + timedelta(days=3)):
                    # Upstream is delayed or at risk
                    blockers.append({
                        "type": "deadline_cascade",
                        "upstream_task_id": upstream.id,
                        "upstream_title": upstream.title,
                        "upstream_deadline": upstream.deadline_at.isoformat() if upstream.deadline_at else None,
                        "upstream_status": upstream.status.value,
                        "downstream_task_id": downstream.id,
                        "downstream_title": downstream.title,
                        "downstream_deadline": downstream.deadline_at.isoformat() if downstream.deadline_at else None,
                        "severity": "high",
                        "suggested_action": f"Priorizar '{upstream.title}' para desbloquear '{downstream.title}'",
                        "detected_at": datetime.utcnow().isoformat(),
                    })

        return blockers

    async def create_blocker_notifications(self, blockers: list[dict]) -> int:
        """Create notifications for detected blockers."""
        from app.models.notification import Notification, NotificationSeverity, NotificationType
        from app.models.user import User

        if not blockers:
            return 0

        # Get user
        stmt = select(User).where(User.id == self.user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return 0

        created = 0
        for blocker in blockers:
            # Only create for high severity
            if blocker.get("severity") != "high":
                continue

            notification = Notification(
                id=str(uuid.uuid4()),
                user_id=self.user_id,
                type=NotificationType.BLOCKER_DETECTED,
                severity=NotificationSeverity.HIGH,
                title=f"Bloqueo detectado: {blocker.get('blocked_task_title', blocker.get('description', 'Tarea'))}",
                message=blocker.get("suggested_action", "Revisar bloqueo"),
                source_type=blocker["type"],
                source_id=blocker.get("blocked_task_id") or blocker.get("commitment_id") or blocker.get("followup_id") or blocker.get("meeting_id"),
                action_url=self._get_action_url(blocker),
                metadata_json=blocker,
            )
            self.db.add(notification)
            created += 1

        if created > 0:
            await self.db.flush()

        return created

    def _get_action_url(self, blocker: dict) -> str:
        """Generate action URL for blocker."""
        if "blocked_task_id" in blocker:
            return f"/tasks/{blocker['blocked_task_id']}"
        elif "commitment_id" in blocker:
            return f"/commitments/{blocker['commitment_id']}"
        elif "followup_id" in blocker:
            return f"/followups/{blocker['followup_id']}"
        elif "meeting_id" in blocker:
            return "/calendar"
        elif "project_id" in blocker:
            return f"/projects/{blocker['project_id']}"
        return "/"

    async def schedule_blocker_check(self) -> None:
        """Run blocker detection and create notifications."""
        blockers = await self.detect_all_blockers()
        if blockers:
            await self.create_blocker_notifications(blockers)
            # Emit event
            await event_bus.emit(EventType.BLOCKERS_DETECTED, {
                "user_id": self.user_id,
                "blockers_count": len(blockers),
                "high_severity": len([b for b in blockers if b.get("severity") == "high"]),
            }, user_id=self.user_id)
