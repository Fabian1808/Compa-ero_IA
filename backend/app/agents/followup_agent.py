from __future__ import annotations

from datetime import datetime, timedelta

from app.ai.service import AIService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext, AgentTask, BaseAgent
from app.models.email import Email
from app.models.followup import FollowUp, FollowUpStatus
from app.models.task import Task, TaskPriority, TaskStatus


class FollowUpAgent(BaseAgent):
    """Agent for proactive follow-ups on sent emails and commitments."""

    def __init__(self, db: AsyncSession, user_id: str):
        super().__init__("followup_agent", "Follow-up Agent", "Proactive follow-ups on sent emails and commitments")
        self.db = db
        self.user_id = user_id
        self.ai_service = AIService(db, user_id)

    @property
    def capabilities(self) -> list[str]:
        return [
            "followup_detection",
            "followup_draft",
            "followup_scheduling",
            "followup_escalation",
            "response_tracking",
            "reminder_generation",
        ]

    @property
    def required_permissions(self) -> list[str]:
        return ["followups:read", "followups:write", "emails:read", "tasks:write"]

    async def initialize(self, context: AgentContext) -> bool:
        return True

    async def execute(self, task: AgentTask, context: AgentContext) -> dict:
        task_type = task.type

        if task_type == "followup_detection":
            return await self._detect_followups(task.payload, context)
        elif task_type == "followup_draft":
            return await self._draft_followup(task.payload, context)
        elif task_type == "followup_scheduling":
            return await self._schedule_followups(task.payload, context)
        elif task_type == "followup_escalation":
            return await self._escalate_followups(task.payload, context)
        elif task_type == "response_tracking":
            return await self._track_responses(task.payload, context)
        elif task_type == "reminder_generation":
            return await self._generate_reminders(task.payload, context)

        return {"error": f"Unknown task type: {task_type}"}

    async def handle_message(self, message, context: AgentContext):
        return None

    async def _detect_followups(self, payload: dict, context: AgentContext) -> dict:
        """Detect emails that need follow-up."""
        days_threshold = payload.get("days_threshold", 3)
        limit = payload.get("limit", 50)

        # Get sent emails from last 30 days
        cutoff = datetime.utcnow() - timedelta(days=30)
        stmt = select(Email).where(
            Email.account.has(user_id=self.user_id),
            Email.sender_email == (await self._get_user_email()),
            Email.received_at >= cutoff,
        ).order_by(Email.received_at.desc()).limit(limit)

        result = await self.db.execute(stmt)
        sent_emails = result.scalars().all()

        detected = []
        for email in sent_emails:
            # Check if already has follow-up
            existing_stmt = select(FollowUp).where(FollowUp.source_email_id == email.id)
            existing_result = await self.db.execute(existing_stmt)
            if existing_result.scalar_one_or_none():
                continue

            # Check for responses in thread
            if email.thread_id:
                thread_stmt = select(Email).where(
                    Email.thread_id == email.thread_id,
                    Email.account.has(user_id=self.user_id),
                    Email.sender_email != (await self._get_user_email()),
                    Email.received_at > email.received_at
                )
                thread_result = await self.db.execute(thread_stmt)
                response = thread_result.scalar_one_or_none()
                if response:
                    continue  # Already has response

            days_waiting = (datetime.utcnow() - email.received_at).days
            if days_waiting >= days_threshold:
                detected.append({
                    "email_id": email.id,
                    "subject": email.subject,
                    "recipient": email.recipients_json,
                    "sent_at": email.received_at.isoformat(),
                    "days_waiting": days_waiting,
                    "priority": "high" if days_waiting > 7 else "medium",
                    "suggested_action": self._suggest_followup_action(email, days_waiting),
                })

        return {"detected": len(detected), "followups": detected}

    async def _draft_followup(self, payload: dict, context: AgentContext) -> dict:
        """Draft a follow-up email."""
        email_id = payload.get("email_id")
        tone = payload.get("tone", "professional")
        custom_message = payload.get("custom_message")

        if not email_id:
            return {"error": "email_id required"}

        stmt = select(Email).where(Email.id == email_id)
        result = await self.db.execute(stmt)
        email = result.scalar_one_or_none()

        if not email:
            return {"error": "Email not found"}

        days_waiting = (datetime.utcnow() - email.received_at).days

        prompt = f"""
        Redacta un correo de seguimiento profesional para:
        
        Correo original:
        - Asunto: {email.subject}
        - Enviado a: {email.recipients_json}
        - Fecha: {email.received_at.strftime('%d/%m/%Y')}
        - Días sin respuesta: {days_waiting}
        - Contenido original: {email.body_text or email.body_preview or ''}
        
        Tono: {tone}
        {f'Mensaje personalizado: {custom_message}' if custom_message else ''}
        
        El seguimiento debe ser educado, breve y claro. Incluir referencia al correo anterior.
        """

        response = await self.ai_service.chat_with_tools(prompt)

        # Create follow-up record
        followup = FollowUp(
            user_id=self.user_id,
            source_email_id=email.id,
            contact_email=self._extract_first_recipient(email.recipients_json),
            subject=f"Re: {email.subject}",
            sent_at=datetime.utcnow(),
            status=FollowUpStatus.DRAFT_PREPARED,
            draft_response=response.get("answer", ""),
            days_waiting=days_waiting,
        )
        self.db.add(followup)
        await self.db.flush()

        return {
            "followup_id": followup.id,
            "draft": response.get("answer", ""),
            "tone": tone,
            "days_waiting": days_waiting,
        }

    async def _schedule_followups(self, payload: dict, context: AgentContext) -> dict:
        """Schedule automatic follow-ups for pending items."""
        return {"scheduled": 0, "message": "Follow-up scheduling not yet implemented"}

    async def _escalate_followups(self, payload: dict, context: AgentContext) -> dict:
        """Escalate overdue follow-ups."""
        escalation_days = payload.get("escalation_days", 10)

        stmt = select(FollowUp).where(
            FollowUp.user_id == self.user_id,
            FollowUp.status.in_([FollowUpStatus.PENDING, FollowUpStatus.REMINDER_SENT]),
            FollowUp.days_waiting >= escalation_days
        )
        result = await self.db.execute(stmt)
        overdue = result.scalars().all()

        escalated = []
        for followup in overdue:
            # Create escalation task
            task = Task(
                user_id=self.user_id,
                title=f"Escalation: Follow up on '{followup.subject}'",
                description=f"Follow-up sent {followup.days_waiting} days ago to {followup.contact_name or followup.contact_email}. No response received.",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                source_email_id=followup.source_email_id,
                metadata_json={"followup_id": followup.id, "escalation": True},
            )
            self.db.add(task)
            escalated.append({
                "followup_id": followup.id,
                "task_id": task.id,
                "action": "Created escalation task",
            })

        await self.db.commit()
        return {"escalated": len(escalated), "items": escalated}

    async def _track_responses(self, payload: dict, context: AgentContext) -> dict:
        """Track responses to followed-up emails."""
        stmt = select(FollowUp).where(
            FollowUp.user_id == self.user_id,
            FollowUp.status.in_([FollowUpStatus.PENDING, FollowUpStatus.REMINDER_SENT])
        )
        result = await self.db.execute(stmt)
        followups = result.scalars().all()

        tracked = []
        for followup in followups:
            if followup.source_email_id and followup.thread_id:
                # Check for responses in thread
                response_stmt = select(Email).where(
                    Email.thread_id == followup.thread_id,
                    Email.account.has(user_id=self.user_id),
                    Email.sender_email != (await self._get_user_email()),
                    Email.received_at > followup.sent_at
                )
                response_result = await self.db.execute(response_stmt)
                response = response_result.scalar_one_or_none()

                if response:
                    followup.status = FollowUpStatus.RESPONSE_RECEIVED
                    followup.response_received_at = datetime.utcnow()
                    tracked.append({
                        "followup_id": followup.id,
                        "response_from": response.sender_email,
                        "response_at": response.received_at.isoformat(),
                    })

        await self.db.commit()
        return {"tracked": len(tracked), "responses": tracked}

    async def _generate_reminders(self, payload: dict, context: AgentContext) -> dict:
        """Generate reminders for pending follow-ups."""
        reminder_days = payload.get("reminder_days", [3, 7, 14])

        stmt = select(FollowUp).where(
            FollowUp.user_id == self.user_id,
            FollowUp.status == FollowUpStatus.PENDING
        )
        result = await self.db.execute(stmt)
        followups = result.scalars().all()

        reminders = []
        for followup in followups:
            if followup.days_waiting in reminder_days:
                # Update status
                followup.status = FollowUpStatus.REMINDER_SENT
                reminders.append({
                    "followup_id": followup.id,
                    "days_waiting": followup.days_waiting,
                    "reminder_sent": True,
                })

        await self.db.commit()
        return {"reminders_sent": len(reminders), "followups": reminders}

    async def _get_user_email(self) -> str:
        from app.models.user import User
        stmt = select(User).where(User.id == self.user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        return user.email if user else ""

    def _extract_first_recipient(self, recipients_json: str) -> str:
        import json
        try:
            recipients = json.loads(recipients_json)
            return recipients[0].get("address", "") if recipients else ""
        except Exception:
            return ""

    def _suggest_followup_action(self, email: Email, days_waiting: int) -> str:
        if days_waiting > 14:
            return "Considerar llamada telefónica o canal alternativo"
        elif days_waiting > 7:
            return "Enviar segundo seguimiento con mayor urgencia"
        else:
            return "Enviar seguimiento educado recordando el correo anterior"
