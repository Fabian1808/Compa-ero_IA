from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"


class AgentPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentMessage:
    """Message passed between agents."""
    id: str = field(default_factory=lambda: str(uuid4()))
    from_agent: str = ""
    to_agent: str = ""
    type: str = ""
    payload: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: str | None = None
    reply_to: str | None = None


@dataclass
class AgentTask:
    """Task assigned to an agent."""
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    type: str = ""
    payload: dict = field(default_factory=dict)
    priority: AgentPriority = AgentPriority.NORMAL
    status: AgentStatus = AgentStatus.IDLE
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict | None = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class AgentContext:
    """Shared context for agent execution."""
    user_id: str
    tenant_id: str | None = None
    session_id: str | None = None
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all specialized agents."""

    def __init__(self, agent_id: str, name: str, description: str = ""):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self._message_queue: list[AgentMessage] = []
        self._tasks: dict[str, AgentTask] = {}

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        """List of capabilities this agent provides."""

    @property
    @abstractmethod
    def required_permissions(self) -> list[str]:
        """Permissions required to run this agent."""

    @abstractmethod
    async def initialize(self, context: AgentContext) -> bool:
        """Initialize agent with context. Return True if successful."""

    @abstractmethod
    async def execute(self, task: AgentTask, context: AgentContext) -> dict:
        """Execute a task. Return result dict."""

    @abstractmethod
    async def handle_message(self, message: AgentMessage, context: AgentContext) -> AgentMessage | None:
        """Handle incoming message. Return reply message if needed."""

    async def shutdown(self) -> None:
        """Cleanup resources."""

    def can_handle(self, task_type: str) -> bool:
        """Check if agent can handle a task type."""
        return task_type in self.capabilities

    def add_task(self, task: AgentTask) -> None:
        self._tasks[task.id] = task

    def get_task(self, task_id: str) -> AgentTask | None:
        return self._tasks.get(task_id)

    def enqueue_message(self, message: AgentMessage) -> None:
        self._message_queue.append(message)

    def dequeue_message(self) -> AgentMessage | None:
        if self._message_queue:
            return self._message_queue.pop(0)
        return None

    def get_status(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "status": self.status.value,
            "pending_tasks": len([t for t in self._tasks.values() if t.status == AgentStatus.IDLE]),
            "running_tasks": len([t for t in self._tasks.values() if t.status == AgentStatus.RUNNING]),
            "queue_size": len(self._message_queue),
        }


class AgentOrchestrator:
    """Orchestrates multiple agents, handles task routing and coordination."""

    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}
        self._message_bus: list[AgentMessage] = []
        self._task_queue: list[AgentTask] = []
        self._running = False

    def register_agent(self, agent: BaseAgent) -> None:
        self.agents[agent.agent_id] = agent

    def unregister_agent(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False

    def get_agent(self, agent_id: str) -> BaseAgent | None:
        return self.agents.get(agent_id)

    def find_agent_for_task(self, task_type: str) -> BaseAgent | None:
        """Find best agent for a task type."""
        for agent in self.agents.values():
            if agent.can_handle(task_type) and agent.status != AgentStatus.ERROR:
                return agent
        return None

    async def dispatch_task(self, task: AgentTask, context: AgentContext) -> dict:
        """Dispatch task to appropriate agent."""
        agent = self.find_agent_for_task(task.type)
        if not agent:
            return {"error": f"No agent found for task type: {task.type}"}

        task.agent_id = agent.agent_id
        task.status = AgentStatus.RUNNING
        task.started_at = datetime.utcnow()
        agent.add_task(task)

        try:
            result = await agent.execute(task, context)
            task.status = AgentStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            return result
        except Exception as e:
            task.status = AgentStatus.ERROR
            task.error = str(e)
            task.retry_count += 1

            if task.retry_count < task.max_retries:
                task.status = AgentStatus.IDLE
                return await self.dispatch_task(task, context)

            return {"error": str(e), "task_id": task.id}

    async def send_message(self, message: AgentMessage) -> AgentMessage | None:
        """Send message to target agent."""
        if message.to_agent in self.agents:
            agent = self.agents[message.to_agent]
            agent.enqueue_message(message)
            return await agent.handle_message(message, AgentContext(user_id=""))
        return None

    async def broadcast_message(self, message: AgentMessage) -> list[AgentMessage]:
        """Broadcast message to all agents."""
        replies = []
        for agent in self.agents.values():
            if agent.agent_id != message.from_agent:
                agent.enqueue_message(message)
                reply = await agent.handle_message(message, AgentContext(user_id=""))
                if reply:
                    replies.append(reply)
        return replies

    async def process_message_queue(self, context: AgentContext) -> None:
        """Process all queued messages."""
        while self._message_bus:
            message = self._message_bus.pop(0)
            if message.to_agent:
                await self.send_message(message)
            else:
                await self.broadcast_message(message)

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False
        for agent in self.agents.values():
            await agent.shutdown()

    def get_orchestrator_status(self) -> dict:
        return {
            "agents": {aid: agent.get_status() for aid, agent in self.agents.items()},
            "message_queue_size": len(self._message_bus),
            "task_queue_size": len(self._task_queue),
            "running": self._running,
        }
