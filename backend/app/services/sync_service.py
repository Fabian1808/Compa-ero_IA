import logging
from datetime import datetime
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.connectors.registry import ConnectorRegistry
from app.models.account import Account, AccountStatus
from app.models.email import Email
from app.models.task import Task
from app.models.commitment import Commitment
from app.models.followup import FollowUp
from app.models.meeting import Meeting
from app.models.project import Project
from app.services.ai_service import AIService
from app.memory.service import MemoryService
from app.events.bus import event_bus, EventType
from app.ai.confidence import ConfidenceTier, evaluate_confidence
from app.config import settings

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.registry = ConnectorRegistry(db)
        self._memory_services: dict[str, MemoryService] = {}

    def _get_memory_service(self, user_id: str) -> MemoryService:
        if user_id not in self._memory_services:
            self._memory_services[user_id] = MemoryService(self.db, user_id)
        return self._memory_services[user_id]

    async def sync_account(self, account_id: str) -> AsyncIterator[dict]:
        """Sync a single account incrementally."""
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()

        if not account:
            yield {"error": "Account not found"}
            return

        if account.status != AccountStatus.ACTIVE:
            yield {"error": "Account not active"}
            return

        connector = self.registry.get_connector(account)
        ai_service = AIService(self.db, account.user_id)

        total_processed = 0
        total_created = 0

        try:
            async for sync_result in connector.sync_incremental():
                total_processed += sync_result.items_processed
                total_created += sync_result.items_created

                # Process new emails with AI
                if sync_result.items_created > 0:
                    await self._process_new_emails(account, ai_service)

                yield {
                    "account_id": account_id,
                    "items_processed": sync_result.items_processed,
                    "items_created": sync_result.items_created,
                    "items_updated": sync_result.items_updated,
                    "items_deleted": sync_result.items_deleted,
                    "errors": sync_result.errors,
                    "next_cursor": sync_result.next_cursor,
                }

            # Update last sync time
            account.last_sync_at = datetime.utcnow()
            await self.db.flush()

            # Emit sync completed event
            await event_bus.emit(EventType.SYNC_COMPLETED, {
                "account_id": account_id,
                "total_processed": total_processed,
                "total_created": total_created,
            }, user_id=account.user_id)

        except Exception as e:
            logger.error(f"Sync failed for account {account_id}: {e}")
            account.status = AccountStatus.ERROR
            await self.db.flush()

            await event_bus.emit(EventType.SYNC_FAILED, {
                "account_id": account_id,
                "error": str(e),
            }, user_id=account.user_id)

            yield {"error": str(e)}

    async def _process_new_emails(self, account: Account, ai_service: AIService) -> None:
        """Process newly synced emails with AI."""
        from sqlalchemy import select
        from app.models.email import Email

        # Get unprocessed emails
        stmt = select(Email).where(
            Email.account_id == account.id,
            Email.is_processed == False
        ).limit(settings.sync_batch_size)

        result = await self.db.execute(stmt)
        emails = result.scalars().all()

        memory_service = self._get_memory_service(account.user_id)
        await memory_service.initialize()

        for email in emails:
            try:
                # Index the email itself
                await memory_service.index_email(email)

                analysis = await ai_service.analyze_email(email.id)
                await self._handle_analysis_results(email, analysis, ai_service, memory_service)
                email.is_processed = True
                await self.db.flush()
            except Exception as e:
                logger.error(f"Failed to process email {email.id}: {e}")

    async def _handle_analysis_results(self, email: Email, analysis: dict, ai_service: AIService, memory_service: MemoryService) -> None:
        """Handle AI analysis results and create suggestions."""
        from app.models.task import Task, TaskStatus, TaskPriority
        from app.models.commitment import Commitment, CommitmentStatus
        from app.models.followup import FollowUp, FollowUpStatus
        import uuid
        import json

        # Handle detected tasks
        for task_data in analysis.get("tasks", []):
            confidence = task_data.get("confidence", 0)
            decision = evaluate_confidence(confidence, "low")

            if decision.tier == ConfidenceTier.AUTO_CREATE:
                task = Task(
                    id=str(uuid.uuid4()),
                    user_id=email.account.user_id,
                    account_id=email.account_id,
                    source_email_id=email.id,
                    title=task_data["title"],
                    description=task_data.get("description"),
                    status=TaskStatus.PENDING,
                    priority=TaskPriority(task_data.get("priority", "medium")),
                    confidence_score=confidence,
                    estimated_minutes=task_data.get("estimated_minutes"),
                    deadline_at=task_data.get("deadline_iso"),
                    metadata_json=json.dumps({"project_hint": task_data.get("project_hint")}),
                )
                self.db.add(task)
                await self.db.flush()

                # Index the new task
                await memory_service.index_task(task)

                await event_bus.emit(EventType.TASK_DETECTED, {
                    "task_id": task.id,
                    "title": task.title,
                    "confidence": confidence,
                    "source_email_id": email.id,
                }, user_id=email.account.user_id)

            elif decision.tier == ConfidenceTier.SUGGEST_CONFIRM:
                await event_bus.emit(EventType.TASK_DETECTED, {
                    "title": task_data["title"],
                    "description": task_data.get("description"),
                    "deadline_at": task_data.get("deadline_iso"),
                    "priority": task_data.get("priority"),
                    "estimated_minutes": task_data.get("estimated_minutes"),
                    "confidence": confidence,
                    "evidence_quote": task_data.get("evidence_quote"),
                    "source_email_id": email.id,
                    "requires_confirmation": True,
                }, user_id=email.account.user_id)

        # Handle commitments
        for commitment_data in analysis.get("commitments", []):
            if commitment_data.get("is_user_commitment"):
                confidence = commitment_data.get("confidence", 0)
                decision = evaluate_confidence(confidence, "medium")

                if decision.tier in [ConfidenceTier.AUTO_CREATE, ConfidenceTier.SUGGEST_CONFIRM]:
                    commitment = Commitment(
                        id=str(uuid.uuid4()),
                        user_id=email.account.user_id,
                        source_email_id=email.id,
                        description=commitment_data["description"],
                        committed_at=datetime.utcnow(),
                        due_date=commitment_data.get("due_date_iso"),
                        status=CommitmentStatus.PENDING,
                        confidence_score=confidence,
                    )
                    self.db.add(commitment)
                    await self.db.flush()

                    # Index the new commitment
                    await memory_service.index_commitment(commitment)

                    await event_bus.emit(EventType.COMMITMENT_DETECTED, {
                        "commitment_id": commitment.id,
                        "description": commitment.description,
                        "due_date": commitment.due_date.isoformat() if commitment.due_date else None,
                        "confidence": confidence,
                        "source_email_id": email.id,
                    }, user_id=email.account.user_id)

        # Handle deadlines
        for deadline_data in analysis.get("deadlines", []):
            if deadline_data.get("is_external"):
                await event_bus.emit(EventType.DEADLINE_DETECTED, {
                    "description": deadline_data["description"],
                    "deadline_at": deadline_data["deadline_iso"],
                    "confidence": deadline_data.get("confidence"),
                    "source_email_id": email.id,
                }, user_id=email.account.user_id)

    async def sync_all_accounts(self, user_id: str) -> AsyncIterator[dict]:
        """Sync all active accounts for a user."""
        result = await self.db.execute(select(Account).where(
            Account.user_id == user_id,
            Account.status == AccountStatus.ACTIVE
        ))
        accounts = result.scalars().all()

        for account in accounts:
            async for sync_result in self.sync_account(account.id):
                yield sync_result