import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.ai import AIProvider, OllamaProvider, ChatMessage, AIProviderConfig
from app.ai.prompts import (
    TASK_EXTRACTION_PROMPT,
    COMMITMENT_EXTRACTION_PROMPT,
    DEADLINE_EXTRACTION_PROMPT,
    FOLLOWUP_DETECTION_PROMPT,
    NEXT_TASK_RECOMMENDATION_PROMPT,
)
from app.ai.tools import TOOL_DEFINITIONS, ToolExecutor
from app.ai.confidence import evaluate_confidence, ConfidenceTier
from app.config import settings
from app.models.email import Email
from app.models.task import Task, TaskStatus
from app.models.commitment import Commitment, CommitmentStatus
from app.models.followup import FollowUp, FollowUpStatus
from app.models.meeting import Meeting
from app.models.project import Project


class AIService:
    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id
        self._provider: Optional[AIProvider] = None
        self._tool_executor: Optional[ToolExecutor] = None

    @property
    def provider(self) -> AIProvider:
        if self._provider is None:
            config = AIProviderConfig(
                provider="ollama",
                base_url=settings.ollama_base_url,
                chat_model=settings.ollama_chat_model,
                embed_model=settings.ollama_embed_model,
            )
            self._provider = OllamaProvider(config)
        return self._provider

    @property
    def tool_executor(self) -> ToolExecutor:
        if self._tool_executor is None:
            self._tool_executor = ToolExecutor(self.db, self.user_id)
        return self._tool_executor

    async def analyze_email(self, email_id: str) -> dict:
        """Analyze a single email for tasks, commitments, deadlines, followups."""
        result = await self.db.execute(select(Email).where(Email.id == email_id))
        email = result.scalar_one_or_none()

        if not email:
            return {"error": "Email not found"}

        # Build email content for analysis
        email_content = f"Subject: {email.subject}\nFrom: {email.sender_name} <{email.sender_email}>\nDate: {email.received_at}\n\n{email.body_text or email.body_preview or ''}"

        # Extract tasks
        tasks_result = await self._extract_tasks(email_content)
        # Extract commitments
        commitments_result = await self._extract_commitments(email_content)
        # Extract deadlines
        deadlines_result = await self._extract_deadlines(email_content)

        return {
            "email_id": email_id,
            "tasks_detected": len(tasks_result.get("tasks", [])),
            "commitments_detected": len(commitments_result.get("commitments", [])),
            "deadlines_detected": len(deadlines_result.get("deadlines", [])),
            "tasks": tasks_result.get("tasks", []),
            "commitments": commitments_result.get("commitments", []),
            "deadlines": deadlines_result.get("deadlines", []),
        }

    async def _extract_tasks(self, email_content: str) -> dict:
        messages = [
            ChatMessage(role="system", content=TASK_EXTRACTION_PROMPT),
            ChatMessage(role="user", content=f"Analiza este correo:\n\n{email_content}"),
        ]

        response = await self.provider.chat_completion(messages, temperature=0.1)
        try:
            return json.loads(response.message.content or "{}")
        except json.JSONDecodeError:
            return {"tasks": [], "has_actionable_content": False}

    async def _extract_commitments(self, email_content: str) -> dict:
        messages = [
            ChatMessage(role="system", content=COMMITMENT_EXTRACTION_PROMPT),
            ChatMessage(role="user", content=f"Analiza este correo:\n\n{email_content}"),
        ]

        response = await self.provider.chat_completion(messages, temperature=0.1)
        try:
            return json.loads(response.message.content or "{}")
        except json.JSONDecodeError:
            return {"commitments": []}

    async def _extract_deadlines(self, email_content: str) -> dict:
        messages = [
            ChatMessage(role="system", content=DEADLINE_EXTRACTION_PROMPT),
            ChatMessage(role="user", content=f"Analiza este correo:\n\n{email_content}"),
        ]

        response = await self.provider.chat_completion(messages, temperature=0.1)
        try:
            return json.loads(response.message.content or "{}")
        except json.JSONDecodeError:
            return {"deadlines": []}

    async def detect_followups(self) -> dict:
        """Detect followups needed based on sent emails without response."""
        # Get sent emails from last 30 days
        cutoff = datetime.utcnow() - timedelta(days=30)
        stmt = select(Email).where(
            Email.account.has(user_id=self.user_id),
            Email.sender_email == (await self._get_user_email()),
            Email.received_at >= cutoff,
        ).order_by(Email.received_at.desc())

        result = await self.db.execute(stmt)
        sent_emails = result.scalars().all()

        # Build conversation context
        conversations = []
        for email in sent_emails:
            conversations.append({
                "subject": email.subject,
                "sent_at": email.received_at.isoformat(),
                "to": email.recipients_json,
                "thread_id": email.thread_id,
            })

        if not conversations:
            return {"followups": []}

        messages = [
            ChatMessage(role="system", content=FOLLOWUP_DETECTION_PROMPT),
            ChatMessage(role="user", content=f"Conversaciones enviadas:\n{json.dumps(conversations, default=str)}"),
        ]

        response = await self.provider.chat_completion(messages, temperature=0.1)
        try:
            return json.loads(response.message.content or "{}")
        except json.JSONDecodeError:
            return {"followups": []}

    async def recommend_next_task(self, available_minutes: int | None = None) -> dict:
        """Recommend the next task to work on."""
        # Get pending tasks
        stmt = select(Task).where(
            Task.user_id == self.user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            Task.status != TaskStatus.BLOCKED,
        ).order_by(Task.deadline_at.nulls_last(), Task.priority.desc()).limit(20)

        result = await self.db.execute(stmt)
        tasks = result.scalars().all()

        # Get upcoming meetings (next 4 hours)
        now = datetime.utcnow()
        stmt = select(Meeting).where(
            Meeting.account.has(user_id=self.user_id),
            Meeting.start_at >= now,
            Meeting.start_at <= now + timedelta(hours=4)
        ).order_by(Meeting.start_at).limit(5)

        result = await self.db.execute(stmt)
        meetings = result.scalars().all()

        # Get active projects
        stmt = select(Project).where(
            Project.user_id == self.user_id,
            Project.status == "active"
        ).limit(10)

        result = await self.db.execute(stmt)
        projects = result.scalars().all()

        # Build context
        context = {
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status.value,
                    "priority": t.priority.value,
                    "deadline_at": t.deadline_at.isoformat() if t.deadline_at else None,
                    "estimated_minutes": t.estimated_minutes,
                    "project_id": t.project_id,
                    "project_name": t.project.name if t.project else None,
                }
                for t in tasks
            ],
            "meetings": [
                {
                    "subject": m.subject,
                    "start_at": m.start_at.isoformat(),
                    "end_at": m.end_at.isoformat(),
                }
                for m in meetings
            ],
            "projects": [{"id": p.id, "name": p.name} for p in projects],
            "available_minutes": available_minutes,
            "current_time": now.isoformat(),
        }

        messages = [
            ChatMessage(role="system", content=NEXT_TASK_RECOMMENDATION_PROMPT),
            ChatMessage(role="user", content=f"Contexto:\n{json.dumps(context, default=str)}"),
        ]

        response = await self.provider.chat_completion(messages, temperature=0.1)
        try:
            return json.loads(response.message.content or "{}")
        except json.JSONDecodeError:
            return {
                "recommended_task_id": None,
                "title": "No hay tarea recomendada",
                "reasoning": "No se pudo generar recomendación",
                "confidence": 0,
            }

    async def chat_with_tools(self, question: str, context: dict | None = None) -> dict:
        """Chat with AI using tool calling."""
        messages = [
            ChatMessage(role="system", content="Eres AI Workmate, un asistente de productividad. Usa las herramientas disponibles para responder."),
            ChatMessage(role="user", content=question),
        ]

        # Add context if provided
        if context:
            messages.insert(1, ChatMessage(role="system", content=f"Contexto actual: {json.dumps(context, default=str)}"))

        response = await self.provider.chat_completion(
            messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        # Handle tool calls
        if response.message.tool_calls:
            tool_results = []
            for tool_call in response.message.tool_calls:
                func_name = tool_call["function"]["name"]
                args = json.loads(tool_call["function"]["arguments"])
                result = await self.tool_executor.execute(func_name, args)
                tool_results.append({"tool": func_name, "result": result})

            # Get final response with tool results
            messages.append(response.message)
            for tr in tool_results:
                messages.append(ChatMessage(
                    role="tool",
                    content=json.dumps(tr["result"]),
                    tool_call_id=tr["tool"]
                ))

            final_response = await self.provider.chat_completion(messages, temperature=0.1)
            return {
                "answer": final_response.message.content,
                "tool_calls": tool_results,
            }

        return {
            "answer": response.message.content,
            "tool_calls": [],
        }

    async def _get_user_email(self) -> str:
        from app.models.user import User
        result = await self.db.execute(select(User).where(User.id == self.user_id))
        user = result.scalar_one_or_none()
        return user.email if user else ""

    async def health_check(self) -> bool:
        return await self.provider.health_check()

    async def generate_daily_briefing(self, date: datetime | None = None) -> dict:
        """Generate daily briefing for the user."""
        if date is None:
            date = datetime.utcnow()
        
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        now = datetime.utcnow()
        
        # Get commitments due today
        stmt = select(Commitment).where(
            Commitment.user_id == self.user_id,
            Commitment.due_date >= day_start,
            Commitment.due_date < day_end,
            Commitment.status.in_([CommitmentStatus.PENDING, CommitmentStatus.CONFIRMED])
        )
        result = await self.db.execute(stmt)
        commitments_today = result.scalars().all()
        
        # Get pending tasks
        stmt = select(Task).where(
            Task.user_id == self.user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        )
        result = await self.db.execute(stmt)
        pending_tasks = result.scalars().all()
        
        # Get meetings today
        stmt = select(Meeting).where(
            Meeting.account.has(user_id=self.user_id),
            Meeting.start_at >= day_start,
            Meeting.start_at < day_end
        ).order_by(Meeting.start_at)
        result = await self.db.execute(stmt)
        meetings_today = result.scalars().all()
        
        # Get blocked tasks
        stmt = select(Task).where(
            Task.user_id == self.user_id,
            Task.status == TaskStatus.BLOCKED
        )
        result = await self.db.execute(stmt)
        blocked_tasks = result.scalars().all()
        
        # Get unread important emails
        stmt = select(Email).where(
            Email.account.has(user_id=self.user_id),
            Email.is_read == False,
            Email.importance == "high"
        ).limit(10)
        result = await self.db.execute(stmt)
        important_emails = result.scalars().all()
        
        # Get pending followups
        stmt = select(FollowUp).where(
            FollowUp.user_id == self.user_id,
            FollowUp.status.in_([FollowUpStatus.PENDING, FollowUpStatus.REMINDER_SENT])
        )
        result = await self.db.execute(stmt)
        pending_followups = result.scalars().all()
        
        # Build context for AI
        context = {
            "date": date.strftime("%Y-%m-%d"),
            "commitments_important": [
                {"description": c.description, "due_date": c.due_date.isoformat() if c.due_date else None}
                for c in commitments_today
            ],
            "tasks_pending": [
                {"title": t.title, "deadline": t.deadline_at.isoformat() if t.deadline_at else None, "priority": t.priority.value}
                for t in pending_tasks
            ],
            "meetings_today": [
                {"subject": m.subject, "start": m.start_at.isoformat(), "end": m.end_at.isoformat()}
                for m in meetings_today
            ],
            "tasks_blocked": [{"title": t.title} for t in blocked_tasks],
            "emails_require_response": len(important_emails),
            "followups_pending": [
                {"contact": f.contact_name or f.contact_email, "subject": f.subject}
                for f in pending_followups
            ],
        }
        
        # Generate briefing using AI
        DAILY_BRIEFING_PROMPT = """Eres AI Workmate, generando el briefing matutino para el usuario.
        
Genera un resumen ejecutivo del día en español, con tono profesional pero cercano.
Incluye:
1. Compromisos importantes del día
2. Tareas prioritarias (deadlines hoy, alta prioridad)
3. Reuniones programadas
4. Tareas bloqueadas que necesitan atención
5. Correos importantes sin leer
6. Seguimientos pendientes

Formato: párrafos cortos, usa viñetas para listas. Máximo 200 palabras.
Termina con una frase motivadora."""
        
        messages = [
            ChatMessage(role="system", content=DAILY_BRIEFING_PROMPT),
            ChatMessage(role="user", content=f"Datos del día:\n{json.dumps(context, default=str)}"),
        ]
        
        response = await self.provider.chat_completion(messages, temperature=0.3, max_tokens=500)
        
        return {
            "commitments_important": len(commitments_today),
            "tasks_pending": len(pending_tasks),
            "meetings_today": len(meetings_today),
            "tasks_blocked": len(blocked_tasks),
            "emails_require_response": len(important_emails),
            "followups_pending": len(pending_followups),
            "summary": response.message.content or "Briefing generado",
            "details": context,
        }

    async def generate_end_of_day(self, date: datetime | None = None) -> dict:
        """Generate end of day summary."""
        if date is None:
            date = datetime.utcnow()
        
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        tomorrow_start = day_end
        tomorrow_end = tomorrow_start + timedelta(days=1)
        
        # Tasks completed today
        stmt = select(Task).where(
            Task.user_id == self.user_id,
            Task.status == TaskStatus.COMPLETED,
            Task.completed_at >= day_start,
            Task.completed_at < day_end
        )
        result = await self.db.execute(stmt)
        completed_tasks = result.scalars().all()
        
        # Emails processed today (read emails received today)
        stmt = select(Email).where(
            Email.account.has(user_id=self.user_id),
            Email.received_at >= day_start,
            Email.received_at < day_end,
            Email.is_read == True
        )
        result = await self.db.execute(stmt)
        processed_emails = result.scalars().all()
        
        # Projects advanced (tasks completed in projects)
        project_ids = set(t.project_id for t in completed_tasks if t.project_id)
        projects_advanced = len(project_ids)
        
        # Pending open tasks
        stmt = select(Task).where(
            Task.user_id == self.user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED])
        )
        result = await self.db.execute(stmt)
        pending_open = result.scalars().all()
        
        # Deadlines tomorrow
        stmt = select(Task).where(
            Task.user_id == self.user_id,
            Task.deadline_at >= tomorrow_start,
            Task.deadline_at < tomorrow_end,
            Task.status != TaskStatus.COMPLETED
        )
        result = await self.db.execute(stmt)
        deadline_tomorrow = result.scalars().all()
        
        # Pending followups
        stmt = select(FollowUp).where(
            FollowUp.user_id == self.user_id,
            FollowUp.status.in_([FollowUpStatus.PENDING, FollowUpStatus.REMINDER_SENT])
        )
        result = await self.db.execute(stmt)
        pending_followups = result.scalars().all()
        
        context = {
            "date": date.strftime("%Y-%m-%d"),
            "tasks_completed": [
                {"title": t.title, "project": t.project.name if t.project else None}
                for t in completed_tasks
            ],
            "emails_processed": len(processed_emails),
            "projects_advanced": projects_advanced,
            "pending_open": len(pending_open),
            "deadline_tomorrow": [
                {"title": t.title, "deadline": t.deadline_at.isoformat() if t.deadline_at else None}
                for t in deadline_tomorrow
            ],
            "followups_pending": len(pending_followups),
        }
        
        END_OF_DAY_PROMPT = """Eres AI Workmate, generando el resumen de fin de día.
        
Genera un resumen reflexivo en español, tono profesional y cercano.
Incluye:
1. Logros del día (tareas completadas, proyectos avanzados)
2. Correos procesados
3. Qué queda pendiente para mañana
4. Deadlines de mañana
5. Seguimientos pendientes

Formato: párrafos cortos, viñetas. Máximo 150 palabras.
Termina con una frase de cierre positiva."""
        
        messages = [
            ChatMessage(role="system", content=END_OF_DAY_PROMPT),
            ChatMessage(role="user", content=f"Datos del día:\n{json.dumps(context, default=str)}"),
        ]
        
        response = await self.provider.chat_completion(messages, temperature=0.3, max_tokens=500)
        
        return {
            "tasks_completed": len(completed_tasks),
            "emails_processed": len(processed_emails),
            "projects_advanced": projects_advanced,
            "pending_open": len(pending_open),
            "deadline_tomorrow": len(deadline_tomorrow),
            "followups_pending": len(pending_followups),
            "summary": response.message.content or "Resumen generado",
            "details": context,
        }

    async def what_am_i_forgetting(self) -> dict:
        """Detect potential forgotten items."""
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        
        # Old pending tasks (no activity in 7 days)
        stmt = select(Task).where(
            Task.user_id == self.user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            Task.updated_at < week_ago
        ).limit(10)
        result = await self.db.execute(stmt)
        stale_tasks = result.scalars().all()
        
        # Commitments overdue
        stmt = select(Commitment).where(
            Commitment.user_id == self.user_id,
            Commitment.due_date < now,
            Commitment.status.in_([CommitmentStatus.PENDING, CommitmentStatus.CONFIRMED])
        ).limit(5)
        result = await self.db.execute(stmt)
        overdue_commitments = result.scalars().all()
        
        # Followups without response > 5 days
        five_days_ago = now - timedelta(days=5)
        stmt = select(FollowUp).where(
            FollowUp.user_id == self.user_id,
            FollowUp.status.in_([FollowUpStatus.PENDING, FollowUpStatus.REMINDER_SENT]),
            FollowUp.sent_at < five_days_ago
        ).limit(5)
        result = await self.db.execute(stmt)
        old_followups = result.scalars().all()
        
        # Unread important emails > 2 days
        two_days_ago = now - timedelta(days=2)
        stmt = select(Email).where(
            Email.account.has(user_id=self.user_id),
            Email.is_read == False,
            Email.importance == "high",
            Email.received_at < two_days_ago
        ).limit(5)
        result = await self.db.execute(stmt)
        old_important_emails = result.scalars().all()
        
        items = []
        
        for t in stale_tasks:
            days_stale = (now - t.updated_at).days
            items.append({
                "type": "stale_task",
                "title": f"Tarea sin actualizar: {t.title}",
                "description": f"Lleva {days_stale} días sin cambios",
                "priority": "medium",
                "action_url": f"/tasks/{t.id}",
            })
        
        for c in overdue_commitments:
            days_overdue = (now - c.due_date).days if c.due_date else 0
            items.append({
                "type": "overdue_commitment",
                "title": f"Compromiso vencido: {c.description}",
                "description": f"Vencido hace {days_overdue} días",
                "priority": "high",
                "action_url": f"/commitments/{c.id}",
            })
        
        for f in old_followups:
            days_waiting = (now - f.sent_at).days
            items.append({
                "type": "old_followup",
                "title": f"Seguimiento sin respuesta: {f.subject}",
                "description": f"Enviado hace {days_waiting} días a {f.contact_name or f.contact_email}",
                "priority": "medium",
                "action_url": f"/followups/{f.id}",
            })
        
        for e in old_important_emails:
            days_unread = (now - e.received_at).days
            items.append({
                "type": "unread_important",
                "title": f"Correo importante sin leer: {e.subject}",
                "description": f"De {e.sender_name}, {days_unread} días sin leer",
                "priority": "high",
                "action_url": f"/emails/{e.id}",
            })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        items.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return {
            "items": items[:10],
            "count": len(items),
        }