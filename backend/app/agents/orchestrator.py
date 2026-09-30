from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.agents.base import AgentOrchestrator, BaseAgent, AgentTask, AgentContext, AgentMessage
from app.agents.planning_agent import PlanningAgent
from app.agents.email_agent import EmailAgent
from app.agents.followup_agent import FollowUpAgent
from app.agents.research_agent import ResearchAgent
from app.agents.document_agent import DocumentAgent
from app.ai.service import AIService


class WorkmateOrchestrator(AgentOrchestrator):
    """Main orchestrator for AI Workmate - coordinates all specialized agents."""

    def __init__(self, db, user_id: str):
        super().__init__()
        self.db = db
        self.user_id = user_id
        self.ai_service = AIService(db, user_id)
        
        # Initialize all agents
        self._init_agents()

    def _init_agents(self) -> None:
        """Initialize and register all specialized agents."""
        agents = [
            PlanningAgent(self.db, self.user_id),
            EmailAgent(self.db, self.user_id),
            FollowUpAgent(self.db, self.user_id),
            ResearchAgent(self.db, self.user_id),
            DocumentAgent(self.db, self.user_id),
        ]
        
        for agent in agents:
            self.register_agent(agent)

    async def initialize_all(self, context: AgentContext) -> bool:
        """Initialize all agents."""
        results = []
        for agent in self.agents.values():
            try:
                result = await agent.initialize(context)
                results.append(result)
            except Exception as e:
                print(f"Failed to initialize {agent.agent_id}: {e}")
                results.append(False)
        return all(results)

    async def process_user_request(
        self,
        user_input: str,
        context: AgentContext,
        available_tools: list[dict] | None = None
    ) -> dict:
        """Process a natural language user request, delegating to appropriate agents."""
        
        # First, use AI to understand the intent and plan
        planning_prompt = f"""
        Analiza la siguiente solicitud del usuario y determina qué agentes especializados deben intervenir:
        
        Solicitud: {user_input}
        
        Agentes disponibles:
        1. planning_agent: planificación diaria/semanal, optimización de agenda, time-blocking
        2. email_agent: triaje de correos, categorización, borradores de respuesta, detección spam
        3. followup_agent: detección de seguimientos, borradores de seguimiento, escalación
        4. research_agent: búsqueda web/documentos, investigación de temas, fact-checking
        5. document_agent: generación de documentos, resúmenes, extracción de datos, reportes, Excel
        
        Responde en formato JSON con:
        {{
            "intent": "descripción breve de la intención",
            "agents_needed": ["agent_id1", "agent_id2"],
            "tasks": [
                {{"agent": "agent_id", "type": "task_type", "payload": {{...}}}
            ],
            "reasoning": "por qué se eligieron estos agentes"
        }}
        """

        response = await self.ai_service.chat_with_tools(planning_prompt)
        
        try:
            import json
            plan = json.loads(response.get("answer", "{}"))
        except Exception:
            # Fallback: simple routing
            plan = self._simple_routing(user_input)

        # Execute planned tasks
        results = {}
        for task_spec in plan.get("tasks", []):
            agent_id = task_spec.get("agent")
            task_type = task_spec.get("type")
            payload = task_spec.get("payload", {})
            
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                task = AgentTask(
                    agent_id=agent_id,
                    type=task_type,
                    payload=payload,
                )
                result = await self.dispatch_task(task, context)
                results[agent_id] = result

        return {
            "intent": plan.get("intent"),
            "reasoning": plan.get("reasoning"),
            "agents_used": list(results.keys()),
            "results": results,
        }

    def _simple_routing(self, user_input: str) -> dict:
        """Simple keyword-based routing as fallback."""
        input_lower = user_input.lower()
        
        agents_needed = []
        tasks = []
        
        if any(kw in input_lower for kw in ["plan", "agenda", "semana", "día", "organiza", "horario"]):
            agents_needed.append("planning_agent")
            tasks.append({"agent": "planning_agent", "type": "daily_planning", "payload": {}})
        
        if any(kw in input_lower for kw in ["correo", "email", "mail", "bandeja", "responder"]):
            agents_needed.append("email_agent")
            tasks.append({"agent": "email_agent", "type": "email_triage", "payload": {}})
        
        if any(kw in input_lower for kw in ["seguimiento", "followup", "respuesta", "recordar"]):
            agents_needed.append("followup_agent")
            tasks.append({"agent": "followup_agent", "type": "followup_detection", "payload": {}})
        
        if any(kw in input_lower for kw in ["busca", "investiga", "información", "sabe", "contexto"]):
            agents_needed.append("research_agent")
            tasks.append({"agent": "research_agent", "type": "topic_research", "payload": {"topic": user_input}})
        
        if any(kw in input_lower for kw in ["documento", "informe", "reporte", "excel", "plantilla", "notas"]):
            agents_needed.append("document_agent")
            tasks.append({"agent": "document_agent", "type": "document_generation", "payload": {"topic": user_input}})

        if not agents_needed:
            # Default to research agent for general queries
            agents_needed.append("research_agent")
            tasks.append({"agent": "research_agent", "type": "topic_research", "payload": {"topic": user_input}})

        return {
            "intent": "General query",
            "agents_needed": list(set(agents_needed)),
            "tasks": tasks,
            "reasoning": "Keyword-based routing",
        }

    async def run_daily_cycle(self, context: AgentContext) -> dict:
        """Run the complete daily agent cycle."""
        results = {}
        
        # 1. Email triage
        if "email_agent" in self.agents:
            task = AgentTask(agent_id="email_agent", type="email_triage", payload={"limit": 50})
            results["email_triage"] = await self.dispatch_task(task, context)
        
        # 2. Follow-up detection
        if "followup_agent" in self.agents:
            task = AgentTask(agent_id="followup_agent", type="followup_detection", payload={"days_threshold": 3})
            results["followup_detection"] = await self.dispatch_task(task, context)
        
        # 3. Daily planning
        if "planning_agent" in self.agents:
            task = AgentTask(agent_id="planning_agent", type="daily_planning", payload={"focus_hours": 4})
            results["daily_planning"] = await self.dispatch_task(task, context)
        
        # 4. Follow-up escalation
        if "followup_agent" in self.agents:
            task = AgentTask(agent_id="followup_agent", type="followup_escalation", payload={"escalation_days": 10})
            results["followup_escalation"] = await self.dispatch_task(task, context)
        
        # 5. Response tracking
        if "followup_agent" in self.agents:
            task = AgentTask(agent_id="followup_agent", type="response_tracking", payload={})
            results["response_tracking"] = await self.dispatch_task(task, context)
        
        return {
            "cycle": "daily",
            "completed_at": datetime.utcnow().isoformat(),
            "results": results,
        }

    async def run_weekly_cycle(self, context: AgentContext) -> dict:
        """Run the weekly agent cycle."""
        results = {}
        
        # Weekly planning
        if "planning_agent" in self.agents:
            task = AgentTask(agent_id="planning_agent", type="weekly_planning", payload={"focus_hours": 3})
            results["weekly_planning"] = await self.dispatch_task(task, context)
        
        # Weekly report generation
        if "document_agent" in self.agents:
            task = AgentTask(agent_id="document_agent", type="report_generation", payload={
                "report_type": "weekly",
                "period": datetime.utcnow().strftime("%Y-%m-%d"),
            })
            results["weekly_report"] = await self.dispatch_task(task, context)
        
        return {
            "cycle": "weekly",
            "completed_at": datetime.utcnow().isoformat(),
            "results": results,
        }

    def get_all_agent_status(self) -> dict:
        """Get status of all registered agents."""
        return {
            agent_id: agent.get_status()
            for agent_id, agent in self.agents.items()
        }

    async def shutdown_all(self) -> None:
        """Shutdown all agents."""
        for agent in self.agents.values():
            await agent.shutdown()
        await self.stop()


# Factory function
def create_orchestrator(db, user_id: str) -> WorkmateOrchestrator:
    """Create and initialize the main orchestrator."""
    return WorkmateOrchestrator(db, user_id)