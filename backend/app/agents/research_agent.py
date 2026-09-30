from __future__ import annotations

from datetime import datetime

from app.ai.service import AIService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext, AgentTask, BaseAgent
from app.memory.service import MemoryService


class ResearchAgent(BaseAgent):
    """Agent for web/document research to provide context for tasks."""

    def __init__(self, db: AsyncSession, user_id: str):
        super().__init__("research_agent", "Research Agent", "Web and document research for task context")
        self.db = db
        self.user_id = user_id
        self.memory_service = MemoryService(db, user_id)
        self.ai_service = AIService(db, user_id)

    @property
    def capabilities(self) -> list[str]:
        return [
            "web_search",
            "document_search",
            "topic_research",
            "competitor_analysis",
            "fact_checking",
            "context_gathering",
        ]

    @property
    def required_permissions(self) -> list[str]:
        return ["memory:read", "memory:write", "ai:chat"]

    async def initialize(self, context: AgentContext) -> bool:
        await self.memory_service.initialize()
        return True

    async def execute(self, task: AgentTask, context: AgentContext) -> dict:
        task_type = task.type

        if task_type == "web_search":
            return await self._web_search(task.payload, context)
        elif task_type == "document_search":
            return await self._document_search(task.payload, context)
        elif task_type == "topic_research":
            return await self._topic_research(task.payload, context)
        elif task_type == "competitor_analysis":
            return await self._competitor_analysis(task.payload, context)
        elif task_type == "fact_checking":
            return await self._fact_checking(task.payload, context)
        elif task_type == "context_gathering":
            return await self._context_gathering(task.payload, context)

        return {"error": f"Unknown task type: {task_type}"}

    async def handle_message(self, message, context: AgentContext):
        return None

    async def _web_search(self, payload: dict, context: AgentContext) -> dict:
        """Search the web for information."""
        query = payload.get("query")
        max_results = payload.get("max_results", 10)

        if not query:
            return {"error": "query required"}

        # Use semantic search in local memory first
        local_results = await self.memory_service.search(query, limit=max_results)

        # TODO: Integrate with actual web search API (SerpAPI, Bing, etc.)
        # For now, return local results with note
        return {
            "query": query,
            "local_results": local_results,
            "web_results": [],
            "note": "Web search integration pending - showing local memory results only",
            "searched_at": datetime.utcnow().isoformat(),
        }

    async def _document_search(self, payload: dict, context: AgentContext) -> dict:
        """Search local documents and memory."""
        query = payload.get("query")
        source_types = payload.get("source_types")
        limit = payload.get("limit", 20)

        if not query:
            return {"error": "query required"}

        results = await self.memory_service.search(query, limit=limit, source_types=source_types)

        return {
            "query": query,
            "results": results,
            "total": len(results),
            "searched_at": datetime.utcnow().isoformat(),
        }

    async def _topic_research(self, payload: dict, context: AgentContext) -> dict:
        """Research a topic comprehensively."""
        topic = payload.get("topic")
        depth = payload.get("depth", "standard")  # quick, standard, deep

        if not topic:
            return {"error": "topic required"}

        # Search local memory for topic
        local_results = await self.memory_service.search(topic, limit=20)

        # Build research context
        context_prompt = f"""
        Investiga el tema: {topic}
        
        Información local disponible:
        {self._format_results_for_context(local_results)}
        
        Proporciona:
        1. Resumen ejecutivo del tema
        2. Puntos clave encontrados
        3. Brechas de información
        4. Fuentes recomendadas para investigación adicional
        5. Próximos pasos sugeridos
        """

        response = await self.ai_service.chat_with_tools(context_prompt)

        return {
            "topic": topic,
            "depth": depth,
            "local_sources_found": len(local_results),
            "research": response.get("answer", ""),
            "sources": [r["source_type"] for r in local_results],
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _competitor_analysis(self, payload: dict, context: AgentContext) -> dict:
        """Analyze competitor information."""
        competitor = payload.get("competitor")
        focus_areas = payload.get("focus_areas", ["products", "pricing", "marketing"])

        if not competitor:
            return {"error": "competitor required"}

        # Search for competitor info in local memory
        results = await self.memory_service.search(competitor, limit=15)

        prompt = f"""
        Analiza la información disponible sobre el competidor: {competitor}
        
        Datos locales:
        {self._format_results_for_context(results)}
        
        Enfócate en: {', '.join(focus_areas)}
        
        Proporciona análisis estructurado con hallazgos y fuentes.
        """

        response = await self.ai_service.chat_with_tools(prompt)

        return {
            "competitor": competitor,
            "focus_areas": focus_areas,
            "sources_found": len(results),
            "analysis": response.get("answer", ""),
        }

    async def _fact_checking(self, payload: dict, context: AgentContext) -> dict:
        """Fact-check a claim against local knowledge."""
        claim = payload.get("claim")
        if not claim:
            return {"error": "claim required"}

        # Search for supporting/contradicting evidence
        results = await self.memory_service.search(claim, limit=10)

        prompt = f"""
        Verifica la siguiente afirmación basándote en la información disponible:
        
        Afirmación: {claim}
        
        Evidencia local:
        {self._format_results_for_context(results)}
        
        Proporciona:
        1. Veredicto: Soportado / Contradicho / Insuficiente evidencia
        2. Confianza (0-100%)
        3. Evidencia a favor
        4. Evidencia en contra
        5. Fuentes consultadas
        """

        response = await self.ai_service.chat_with_tools(prompt)

        return {
            "claim": claim,
            "fact_check": response.get("answer", ""),
            "sources_checked": len(results),
        }

    async def _context_gathering(self, payload: dict, context: AgentContext) -> dict:
        """Gather comprehensive context for a task or decision."""
        task_id = payload.get("task_id")
        topic = payload.get("topic")
        include_web = payload.get("include_web", False)

        if not task_id and not topic:
            return {"error": "task_id or topic required"}

        search_query = topic
        if task_id:
            from app.models.task import Task
            stmt = select(Task).where(Task.id == task_id)
            result = await self.db.execute(stmt)
            task = result.scalar_one_or_none()
            if task:
                search_query = f"{task.title} {task.description or ''}"

        # Gather from all sources
        local_results = await self.memory_service.search(search_query or "", limit=30)

        # Organize by source type
        by_source = {}
        for r in local_results:
            st = r["source_type"]
            if st not in by_source:
                by_source[st] = []
            by_source[st].append(r)

        return {
            "query": search_query,
            "total_sources": len(local_results),
            "by_source_type": {k: len(v) for k, v in by_source.items()},
            "details": by_source,
            "note": "Web search not yet integrated" if include_web else "Local memory only",
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _format_results_for_context(self, results: list[dict]) -> str:
        if not results:
            return "No local information found."

        formatted = []
        for r in results[:10]:
            formatted.append(f"- [{r['source_type']}] {r['content'][:300]}...")
        return "\n".join(formatted)
