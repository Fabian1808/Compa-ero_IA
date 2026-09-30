from __future__ import annotations

from datetime import datetime

from app.ai.service import AIService
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext, AgentTask, BaseAgent
from app.models.email import Email


class EmailAgent(BaseAgent):
    """Agent for email triage, categorization, and response drafting."""

    def __init__(self, db: AsyncSession, user_id: str):
        super().__init__("email_agent", "Email Agent", "Email triage, categorization, and response drafting")
        self.db = db
        self.user_id = user_id
        self.ai_service = AIService(db, user_id)

    @property
    def capabilities(self) -> list[str]:
        return [
            "email_triage",
            "email_categorization",
            "auto_reply_draft",
            "spam_detection",
            "newsletter_detection",
            "action_item_extraction",
            "thread_summarization",
        ]

    @property
    def required_permissions(self) -> list[str]:
        return ["emails:read", "emails:write", "tasks:write", "contacts:read"]

    async def initialize(self, context: AgentContext) -> bool:
        return True

    async def execute(self, task: AgentTask, context: AgentContext) -> dict:
        task_type = task.type

        if task_type == "email_triage":
            return await self._triage_emails(task.payload, context)
        elif task_type == "email_categorization":
            return await self._categorize_email(task.payload, context)
        elif task_type == "auto_reply_draft":
            return await self._draft_reply(task.payload, context)
        elif task_type == "spam_detection":
            return await self._detect_spam(task.payload, context)
        elif task_type == "newsletter_detection":
            return await self._detect_newsletter(task.payload, context)
        elif task_type == "action_item_extraction":
            return await self._extract_action_items(task.payload, context)
        elif task_type == "thread_summarization":
            return await self._summarize_thread(task.payload, context)

        return {"error": f"Unknown task type: {task_type}"}

    async def handle_message(self, message, context: AgentContext):
        return None

    async def _triage_emails(self, payload: dict, context: AgentContext) -> dict:
        """Triage unprocessed emails."""
        limit = payload.get("limit", 50)

        stmt = select(Email).where(
            Email.account.has(user_id=self.user_id),
            Email.is_processed == False
        ).order_by(Email.received_at.desc()).limit(limit)

        result = await self.db.execute(stmt)
        emails = result.scalars().all()

        triaged = []
        for email in emails:
            analysis = await self.ai_service.analyze_email(email.id)
            category = self._determine_category(email, analysis)

            triaged.append({
                "email_id": email.id,
                "subject": email.subject,
                "sender": email.sender_email,
                "category": category,
                "priority": self._determine_priority(email, analysis),
                "action_required": self._requires_action(analysis),
                "analysis": analysis,
            })

            email.is_processed = True

        await self.db.commit()
        return {"triaged": len(triaged), "emails": triaged}

    async def _categorize_email(self, payload: dict, context: AgentContext) -> dict:
        """Categorize a specific email."""
        email_id = payload.get("email_id")
        if not email_id:
            return {"error": "email_id required"}

        stmt = select(Email).where(Email.id == email_id)
        result = await self.db.execute(stmt)
        email = result.scalar_one_or_none()

        if not email:
            return {"error": "Email not found"}

        analysis = await self.ai_service.analyze_email(email_id)
        category = self._determine_category(email, analysis)

        return {
            "email_id": email_id,
            "category": category,
            "confidence": analysis.get("confidence", 0),
        }

    async def _draft_reply(self, payload: dict, context: AgentContext) -> dict:
        """Draft a reply to an email."""
        email_id = payload.get("email_id")
        tone = payload.get("tone", "professional")
        key_points = payload.get("key_points", [])

        if not email_id:
            return {"error": "email_id required"}

        stmt = select(Email).where(Email.id == email_id)
        result = await self.db.execute(stmt)
        email = result.scalar_one_or_none()

        if not email:
            return {"error": "Email not found"}

        # Generate reply using AI
        reply_prompt = f"""
        Redacta una respuesta profesional a este correo:
        
        De: {email.sender_name} <{email.sender_email}>
        Asunto: {email.subject}
        Contenido: {email.body_text or email.body_preview or ''}
        
        Tono: {tone}
        Puntos clave a incluir: {', '.join(key_points) if key_points else 'Responder apropiadamente'}
        
        La respuesta debe ser concisa y profesional.
        """

        response = await self.ai_service.chat_with_tools(reply_prompt)

        return {
            "email_id": email_id,
            "draft": response.get("answer", ""),
            "tone": tone,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _detect_spam(self, payload: dict, context: AgentContext) -> dict:
        """Detect spam/unwanted emails."""
        limit = payload.get("limit", 100)

        stmt = select(Email).where(
            Email.account.has(user_id=self.user_id),
            Email.is_read == False
        ).order_by(Email.received_at.desc()).limit(limit)

        result = await self.db.execute(stmt)
        emails = result.scalars().all()

        spam_candidates = []
        for email in emails:
            score = self._calculate_spam_score(email)
            if score > 0.7:
                spam_candidates.append({
                    "email_id": email.id,
                    "subject": email.subject,
                    "sender": email.sender_email,
                    "spam_score": score,
                    "reasons": self._get_spam_reasons(email),
                })

        return {"spam_candidates": len(spam_candidates), "emails": spam_candidates}

    async def _detect_newsletter(self, payload: dict, context: AgentContext) -> dict:
        """Detect newsletter/promotional emails."""
        limit = payload.get("limit", 100)

        stmt = select(Email).where(
            Email.account.has(user_id=self.user_id),
            or_(
                Email.sender_email.ilike("%newsletter%"),
                Email.sender_email.ilike("%noreply%"),
                Email.sender_email.ilike("%marketing%"),
                Email.subject.ilike("%newsletter%"),
                Email.subject.ilike("%promo%"),
                Email.subject.ilike("%oferta%"),
            )
        ).order_by(Email.received_at.desc()).limit(limit)

        result = await self.db.execute(stmt)
        emails = result.scalars().all()

        return {
            "newsletters": len(emails),
            "emails": [
                {"email_id": e.id, "subject": e.subject, "sender": e.sender_email}
                for e in emails
            ],
        }

    async def _extract_action_items(self, payload: dict, context: AgentContext) -> dict:
        """Extract action items from email."""
        email_id = payload.get("email_id")
        if not email_id:
            return {"error": "email_id required"}

        analysis = await self.ai_service.analyze_email(email_id)

        action_items = []
        for task_data in analysis.get("tasks", []):
            if task_data.get("confidence", 0) >= 80:
                action_items.append({
                    "title": task_data.get("title"),
                    "description": task_data.get("description"),
                    "priority": task_data.get("priority", "medium"),
                    "deadline": task_data.get("deadline_iso"),
                    "confidence": task_data.get("confidence"),
                })

        return {"email_id": email_id, "action_items": action_items}

    async def _summarize_thread(self, payload: dict, context: AgentContext) -> dict:
        """Summarize email thread."""
        thread_id = payload.get("thread_id")
        if not thread_id:
            return {"error": "thread_id required"}

        stmt = select(Email).where(
            Email.thread_id == thread_id,
            Email.account.has(user_id=self.user_id)
        ).order_by(Email.received_at)

        result = await self.db.execute(stmt)
        emails = result.scalars().all()

        if not emails:
            return {"error": "Thread not found"}

        # Build conversation for AI
        conversation = []
        for email in emails:
            conversation.append(f"De: {email.sender_name} ({email.sender_email})\nAsunto: {email.subject}\n{email.body_text or email.body_preview or ''}\n---")

        prompt = f"""
        Resume esta conversación de correo en español:
        
        {''.join(conversation)}
        
        Incluye:
        1. Tema principal
        2. Participantes clave
        3. Decisiones tomadas
        4. Pendientes/Acciones requeridas
        5. Resumen en 3-5 bullets
        """

        response = await self.ai_service.chat_with_tools(prompt)

        return {
            "thread_id": thread_id,
            "email_count": len(emails),
            "participants": list(set(e.sender_email for e in emails)),
            "summary": response.get("answer", ""),
        }

    def _determine_category(self, email: Email, analysis: dict) -> str:
        """Determine email category."""
        if self._is_newsletter(email):
            return "newsletter"
        if self._is_spam(email):
            return "spam"
        if analysis.get("tasks_detected", 0) > 0:
            return "action_required"
        if analysis.get("commitments_detected", 0) > 0:
            return "commitment"
        if analysis.get("followups_detected", 0) > 0:
            return "followup"
        if email.importance == "high":
            return "important"
        return "informational"

    def _determine_priority(self, email: Email, analysis: dict) -> str:
        """Determine email priority."""
        if email.importance == "high":
            return "high"
        if analysis.get("tasks_detected", 0) > 0:
            return "high"
        if analysis.get("deadlines_detected", 0) > 0:
            return "high"
        return "normal"

    def _requires_action(self, analysis: dict) -> bool:
        return (analysis.get("tasks_detected", 0) > 0 or
                analysis.get("commitments_detected", 0) > 0 or
                analysis.get("followups_detected", 0) > 0)

    def _is_newsletter(self, email: Email) -> bool:
        sender = (email.sender_email or "").lower()
        subject = (email.subject or "").lower()
        return any(kw in sender for kw in ["newsletter", "noreply", "marketing", "promo"]) or \
               any(kw in subject for kw in ["newsletter", "promo", "oferta", "descuento"])

    def _is_spam(self, email: Email) -> bool:
        sender = (email.sender_email or "").lower()
        return any(kw in sender for kw in ["spam", "scam", "phishing", "bitcoin", "crypto", "viagra"])

    def _calculate_spam_score(self, email: Email) -> float:
        score = 0.0
        sender = (email.sender_email or "").lower()
        subject = (email.subject or "").lower()

        spam_keywords = ["free", "win", "winner", "congratulations", "urgent", "act now", "limited time"]
        for kw in spam_keywords:
            if kw in subject:
                score += 0.15
            if kw in sender:
                score += 0.1

        if "noreply" in sender or "no-reply" in sender:
            score += 0.1
        if email.importance == "high" and not email.is_read:
            score -= 0.1  # High importance unread might be important

        return min(score, 1.0)

    def _get_spam_reasons(self, email: Email) -> list[str]:
        reasons = []
        sender = (email.sender_email or "").lower()
        subject = (email.subject or "").lower()

        if "noreply" in sender or "no-reply" in sender:
            reasons.append("Automated sender")
        if any(kw in subject for kw in ["free", "win", "urgent", "act now"]):
            reasons.append("Spam-like subject")
        if email.importance == "low":
            reasons.append("Low importance")

        return reasons
