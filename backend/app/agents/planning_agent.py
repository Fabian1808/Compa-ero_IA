from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext, AgentTask, BaseAgent
from app.memory.service import MemoryService
from app.models.commitment import Commitment, CommitmentStatus
from app.models.meeting import Meeting
from app.models.task import Task, TaskStatus


class PlanningAgent(BaseAgent):
    """Agent for automatic day/week planning."""

    def __init__(self, db: AsyncSession, user_id: str):
        super().__init__("planning_agent", "Planning Agent", "Automatic day and week planning")
        self.db = db
        self.user_id = user_id
        self.memory_service = MemoryService(db, user_id)

    @property
    def capabilities(self) -> list[str]:
        return [
            "daily_planning",
            "weekly_planning",
            "schedule_optimization",
            "time_blocking",
            "priority_rebalancing",
        ]

    @property
    def required_permissions(self) -> list[str]:
        return ["tasks:read", "tasks:write", "calendar:read", "projects:read"]

    async def initialize(self, context: AgentContext) -> bool:
        await self.memory_service.initialize()
        return True

    async def execute(self, task: AgentTask, context: AgentContext) -> dict:
        task_type = task.type

        if task_type == "daily_planning":
            return await self._generate_daily_plan(task.payload, context)
        elif task_type == "weekly_planning":
            return await self._generate_weekly_plan(task.payload, context)
        elif task_type == "schedule_optimization":
            return await self._optimize_schedule(task.payload, context)
        elif task_type == "time_blocking":
            return await self._create_time_blocks(task.payload, context)
        elif task_type == "priority_rebalancing":
            return await self._rebalance_priorities(task.payload, context)

        return {"error": f"Unknown task type: {task_type}"}

    async def handle_message(self, message, context: AgentContext):
        return None

    async def _generate_daily_plan(self, payload: dict, context: AgentContext) -> dict:
        """Generate optimized daily plan."""
        date = payload.get("date", datetime.utcnow().date())
        if isinstance(date, str):
            date = datetime.fromisoformat(date).date()

        day_start = datetime.combine(date, datetime.min.time())
        day_end = day_start + timedelta(days=1)

        # Get all relevant data
        tasks = await self._get_pending_tasks()
        meetings = await self._get_meetings(day_start, day_end)
        commitments = await self._get_commitments_due(day_start, day_end)
        focus_time = payload.get("focus_hours", 4)

        # Build schedule
        schedule = await self._build_schedule(tasks, meetings, commitments, focus_time, day_start, day_end)

        # Save plan
        plan = {
            "date": date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "schedule": schedule,
            "focus_blocks": self._extract_focus_blocks(schedule),
            "meetings": [{"id": m.id, "subject": m.subject, "start": m.start_at.isoformat(), "end": m.end_at.isoformat()} for m in meetings],
            "tasks_planned": len([s for s in schedule if s["type"] == "task"]),
            "total_focus_hours": sum(b["duration_hours"] for b in self._extract_focus_blocks(schedule)),
        }

        return plan

    async def _generate_weekly_plan(self, payload: dict, context: AgentContext) -> dict:
        """Generate weekly plan."""
        start_date = payload.get("start_date", datetime.utcnow().date())
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).date()

        weekly_plan = []
        for i in range(7):
            day = start_date + timedelta(days=i)
            daily = await self._generate_daily_plan({"date": day, "focus_hours": payload.get("focus_hours", 3)}, context)
            weekly_plan.append(daily)

        return {
            "week_start": start_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "daily_plans": weekly_plan,
            "summary": self._summarize_week(weekly_plan),
        }

    async def _optimize_schedule(self, payload: dict, context: AgentContext) -> dict:
        """Optimize existing schedule for better productivity."""
        # This would analyze current schedule and suggest improvements
        return {"optimizations": [], "message": "Schedule optimization not yet implemented"}

    async def _create_time_blocks(self, payload: dict, context: AgentContext) -> dict:
        """Create focused time blocks for deep work."""
        return {"time_blocks": [], "message": "Time blocking not yet implemented"}

    async def _rebalance_priorities(self, payload: dict, context: AgentContext) -> dict:
        """Rebalance task priorities based on deadlines and dependencies."""
        return {"rebalanced": [], "message": "Priority rebalancing not yet implemented"}

    async def _get_pending_tasks(self) -> list[Task]:
        stmt = select(Task).where(
            Task.user_id == self.user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            Task.status != TaskStatus.BLOCKED
        ).order_by(Task.deadline_at.nulls_last(), Task.priority.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _get_meetings(self, start: datetime, end: datetime) -> list[Meeting]:
        stmt = select(Meeting).where(
            Meeting.account.has(user_id=self.user_id),
            Meeting.start_at >= start,
            Meeting.start_at < end
        ).order_by(Meeting.start_at)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _get_commitments_due(self, start: datetime, end: datetime) -> list[Commitment]:
        stmt = select(Commitment).where(
            Commitment.user_id == self.user_id,
            Commitment.due_date >= start,
            Commitment.due_date < end,
            Commitment.status.in_([CommitmentStatus.PENDING, CommitmentStatus.CONFIRMED])
        ).order_by(Commitment.due_date)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _build_schedule(
        self,
        tasks: list[Task],
        meetings: list[Meeting],
        commitments: list[Commitment],
        focus_hours: float,
        day_start: datetime,
        day_end: datetime
    ) -> list[dict]:
        """Build optimized schedule."""
        schedule = []
        current_time = day_start.replace(hour=8, minute=0)  # Start at 8 AM
        work_end = day_start.replace(hour=18, minute=0)  # End at 6 PM

        # Add meetings first (fixed)
        for meeting in meetings:
            if current_time < meeting.start_at:
                # Free slot before meeting
                free_duration = (meeting.start_at - current_time).total_seconds() / 3600
                if free_duration >= 0.5:
                    schedule.append({
                        "type": "focus",
                        "start": current_time.isoformat(),
                        "end": meeting.start_at.isoformat(),
                        "duration_hours": round(free_duration, 2),
                        "suggested_task": self._suggest_task_for_slot(tasks, free_duration),
                    })

            schedule.append({
                "type": "meeting",
                "id": meeting.id,
                "subject": meeting.subject,
                "start": meeting.start_at.isoformat(),
                "end": meeting.end_at.isoformat(),
                "duration_hours": (meeting.end_at - meeting.start_at).total_seconds() / 3600,
            })
            current_time = max(current_time, meeting.end_at)

        # Fill remaining time with tasks
        remaining_focus = focus_hours
        for task in tasks:
            if current_time >= work_end or remaining_focus <= 0:
                break

            estimated_hours = (task.estimated_minutes or 60) / 60
            estimated_hours = min(estimated_hours, remaining_focus)

            end_time = current_time + timedelta(hours=estimated_hours)
            if end_time > work_end:
                end_time = work_end
                estimated_hours = (work_end - current_time).total_seconds() / 3600

            if estimated_hours >= 0.25:  # At least 15 min
                schedule.append({
                    "type": "task",
                    "task_id": task.id,
                    "title": task.title,
                    "priority": task.priority.value,
                    "start": current_time.isoformat(),
                    "end": end_time.isoformat(),
                    "duration_hours": round(estimated_hours, 2),
                })
                current_time = end_time
                remaining_focus -= estimated_hours

        # Add commitments
        for commitment in commitments:
            schedule.append({
                "type": "commitment",
                "id": commitment.id,
                "description": commitment.description,
                "due": commitment.due_date.isoformat() if commitment.due_date else None,
            })

        return schedule

    def _suggest_task_for_slot(self, tasks: list[Task], duration_hours: float) -> dict | None:
        """Suggest best task for a time slot."""
        suitable = [t for t in tasks if (t.estimated_minutes or 60) / 60 <= duration_hours]
        if not suitable:
            return None
        # Prefer high priority, urgent tasks
        suitable.sort(key=lambda t: (t.priority.value, t.deadline_at or datetime.max))
        return {"id": suitable[0].id, "title": suitable[0].title, "priority": suitable[0].priority.value}

    def _extract_focus_blocks(self, schedule: list[dict]) -> list[dict]:
        return [s for s in schedule if s["type"] == "focus"]

    def _summarize_week(self, weekly_plan: list[dict]) -> dict:
        total_tasks = sum(p.get("tasks_planned", 0) for p in weekly_plan)
        total_focus = sum(p.get("total_focus_hours", 0) for p in weekly_plan)
        total_meetings = sum(len(p.get("meetings", [])) for p in weekly_plan)
        return {
            "total_tasks_planned": total_tasks,
            "total_focus_hours": round(total_focus, 1),
            "total_meetings": total_meetings,
        }
