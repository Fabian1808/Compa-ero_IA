from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commitment import Commitment, CommitmentStatus
from app.models.meeting import Meeting
from app.models.project import Project
from app.models.task import DependencyType, Task, TaskDependency, TaskPriority, TaskStatus


class WorkMapService:
    """Generate visual work map: projects-tasks-people-deadlines graph."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def get_work_map(self) -> dict:
        """Get complete work map data for visualization."""
        # Get all relevant data
        projects = await self._get_projects()
        tasks = await self._get_tasks()
        commitments = await self._get_commitments()
        meetings = await self._get_meetings()
        dependencies = await self._get_dependencies()

        # Build nodes and edges
        nodes = []
        edges = []

        # Project nodes
        for project in projects:
            project_tasks = [t for t in tasks if t.project_id == project.id]
            completed_count = sum(1 for t in project_tasks if t.status == TaskStatus.COMPLETED)
            total_count = len(project_tasks)
            progress = (completed_count / total_count * 100) if total_count > 0 else 0

            nodes.append({
                "id": f"project_{project.id}",
                "type": "project",
                "label": project.name,
                "data": {
                    "id": project.id,
                    "name": project.name,
                    "status": project.status,
                    "progress": round(progress, 1),
                    "task_count": total_count,
                    "completed_count": completed_count,
                    "color": project.color or "#3b82f6",
                },
                "position": {"x": 0, "y": 0},  # Will be set by frontend layout
            })

        # Task nodes
        for task in tasks:
            project_node_id = f"project_{task.project_id}" if task.project_id else None

            # Calculate urgency
            urgency = self._calculate_urgency(task)

            nodes.append({
                "id": f"task_{task.id}",
                "type": "task",
                "label": task.title,
                "data": {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "deadline": task.deadline_at.isoformat() if task.deadline_at else None,
                    "estimated_minutes": task.estimated_minutes,
                    "actual_minutes": task.actual_minutes,
                    "project_id": task.project_id,
                    "project_name": task.project.name if task.project else None,
                    "urgency": urgency,
                    "is_blocked": task.status == TaskStatus.BLOCKED,
                    "is_overdue": task.deadline_at and task.deadline_at < datetime.utcnow() and task.status != TaskStatus.COMPLETED,
                },
                "position": {"x": 0, "y": 0},
                "parent": project_node_id,
            })

        # Commitment nodes
        for commitment in commitments:
            nodes.append({
                "id": f"commitment_{commitment.id}",
                "type": "commitment",
                "label": commitment.description[:50] + ("..." if len(commitment.description) > 50 else ""),
                "data": {
                    "id": commitment.id,
                    "description": commitment.description,
                    "status": commitment.status.value,
                    "due_date": commitment.due_date.isoformat() if commitment.due_date else None,
                    "confidence_score": commitment.confidence_score,
                    "related_task_id": commitment.related_task_id,
                },
                "position": {"x": 0, "y": 0},
            })

        # Meeting nodes (upcoming 7 days)
        for meeting in meetings:
            hours_until = (meeting.start_at - datetime.utcnow()).total_seconds() / 3600
            nodes.append({
                "id": f"meeting_{meeting.id}",
                "type": "meeting",
                "label": meeting.subject,
                "data": {
                    "id": meeting.id,
                    "subject": meeting.subject,
                    "start_at": meeting.start_at.isoformat(),
                    "end_at": meeting.end_at.isoformat(),
                    "hours_until": round(hours_until, 1),
                    "is_online": meeting.is_online,
                    "meeting_url": meeting.meeting_url,
                },
                "position": {"x": 0, "y": 0},
            })

        # Dependency edges
        for dep in dependencies:
            from_node = f"task_{dep.depends_on_task_id}"
            to_node = f"task_{dep.task_id}"

            edges.append({
                "id": f"dep_{dep.id}",
                "source": from_node,
                "target": to_node,
                "type": "dependency",
                "label": dep.dependency_type.value,
                "data": {
                    "dependency_type": dep.dependency_type.value,
                },
                "style": {
                    "stroke": "#ef4444" if dep.dependency_type == DependencyType.BLOCKS else "#f59e0b",
                    "strokeWidth": 2,
                },
            })

        # Commitment -> Task edges
        for commitment in commitments:
            if commitment.related_task_id:
                edges.append({
                    "id": f"commitment_task_{commitment.id}",
                    "source": f"commitment_{commitment.id}",
                    "target": f"task_{commitment.related_task_id}",
                    "type": "commitment",
                    "label": "relacionado",
                    "style": {"stroke": "#8b5cf6", "strokeWidth": 1, "strokeDasharray": "5,5"},
                })

        # Calculate bottlenecks
        bottlenecks = self._calculate_bottlenecks(nodes, edges, tasks)

        # Calculate stats
        stats = {
            "total_projects": len(projects),
            "active_projects": len([p for p in projects if p.status == "active"]),
            "total_tasks": len(tasks),
            "pending_tasks": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "in_progress_tasks": len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
            "blocked_tasks": len([t for t in tasks if t.status == TaskStatus.BLOCKED]),
            "completed_tasks": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "overdue_tasks": len([t for t in tasks if t.deadline_at and t.deadline_at < datetime.utcnow() and t.status != TaskStatus.COMPLETED]),
            "upcoming_meetings": len(meetings),
            "pending_commitments": len([c for c in commitments if c.status in [CommitmentStatus.PENDING, CommitmentStatus.CONFIRMED]]),
            "bottlenecks_count": len(bottlenecks),
        }

        return {
            "nodes": nodes,
            "edges": edges,
            "bottlenecks": bottlenecks,
            "stats": stats,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _calculate_urgency(self, task: Task) -> str:
        """Calculate task urgency based on deadline, priority, and status."""
        if task.status == TaskStatus.COMPLETED:
            return "none"

        if task.status == TaskStatus.BLOCKED:
            return "critical"

        if not task.deadline_at:
            return "low" if task.priority in [TaskPriority.LOW, TaskPriority.MEDIUM] else "medium"

        days_until = (task.deadline_at - datetime.utcnow()).days

        if days_until < 0:
            return "critical"
        elif days_until == 0:
            return "critical" if task.priority in [TaskPriority.HIGH, TaskPriority.CRITICAL] else "high"
        elif days_until <= 1:
            return "high"
        elif days_until <= 3:
            return "medium"
        elif days_until <= 7:
            return "low"
        else:
            return "none"

    def _calculate_bottlenecks(self, nodes: list[dict], edges: list[dict], tasks: list[Task]) -> list[dict]:
        """Identify bottlenecks in the work graph."""
        bottlenecks = []

        # Task-level bottlenecks: blocked tasks with dependents
        task_nodes = [n for n in nodes if n["type"] == "task"]
        task_by_id = {n["id"]: n for n in task_nodes}

        # Build adjacency for dependents
        dependents = defaultdict(list)
        for edge in edges:
            if edge["type"] == "dependency" and edge["data"]["dependency_type"] == "blocks":
                dependents[edge["source"]].append(edge["target"])

        for task_node in task_nodes:
            task_id = task_node["data"]["id"]
            task_data = task_node["data"]

            # If task is blocked or overdue and has dependents
            if (task_data["is_blocked"] or task_data["is_overdue"]) and dependents.get(f"task_{task_id}"):
                downstream = dependents[f"task_{task_id}"]
                downstream_titles = [task_by_id[d]["data"]["title"] for d in downstream if d in task_by_id]

                bottlenecks.append({
                    "type": "blocked_with_dependents",
                    "task_id": task_id,
                    "task_title": task_data["title"],
                    "blocked_reason": "blocked" if task_data["is_blocked"] else "overdue",
                    "downstream_tasks": downstream_titles,
                    "impact": "high",
                    "suggested_action": f"Desbloquear '{task_data['title']}' para desbloquear {len(downstream_titles)} tareas",
                })

        # Project-level bottlenecks: projects with many blocked/overdue tasks
        projects_with_issues = defaultdict(list)
        for task_node in task_nodes:
            project_id = task_node["data"].get("project_id")
            if project_id and (task_node["data"]["is_blocked"] or task_node["data"]["is_overdue"]):
                projects_with_issues[project_id].append(task_node["data"]["title"])

        for project_id, issue_tasks in projects_with_issues.items():
            if len(issue_tasks) >= 2:
                project_node = next((n for n in nodes if n["id"] == f"project_{project_id}"), None)
                bottlenecks.append({
                    "type": "project_bottleneck",
                    "project_id": project_id,
                    "project_name": project_node["data"]["name"] if project_node else "Unknown",
                    "affected_tasks": issue_tasks,
                    "impact": "high" if len(issue_tasks) >= 3 else "medium",
                    "suggested_action": f"Revisar proyecto '{project_node['data']['name'] if project_node else project_id}': {len(issue_tasks)} tareas bloqueadas/vencidas",
                })

        # Resource contention: too many high-priority tasks without project
        unassigned_high_priority = [
            n for n in task_nodes
            if not n["data"].get("project_id")
            and n["data"]["priority"] in ["high", "critical"]
            and n["data"]["status"] in ["pending", "in_progress"]
        ]
        if len(unassigned_high_priority) >= 3:
            bottlenecks.append({
                "type": "unassigned_high_priority",
                "affected_tasks": [n["data"]["title"] for n in unassigned_high_priority],
                "impact": "medium",
                "suggested_action": "Asignar proyecto o priorizar tareas sin proyecto",
            })

        return bottlenecks

    async def _get_projects(self) -> list[Project]:
        stmt = select(Project).where(Project.user_id == self.user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _get_tasks(self) -> list[Task]:
        stmt = select(Task).where(Task.user_id == self.user_id).options(
            # Note: relationships would need to be loaded if we want project name
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _get_commitments(self) -> list[Commitment]:
        stmt = select(Commitment).where(
            Commitment.user_id == self.user_id,
            Commitment.status.in_([CommitmentStatus.PENDING, CommitmentStatus.CONFIRMED, CommitmentStatus.COMPLETED])
        ).order_by(Commitment.due_date.nulls_last())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _get_meetings(self) -> list[Meeting]:
        now = datetime.utcnow()
        week_later = now + timedelta(days=7)
        stmt = select(Meeting).where(
            Meeting.account.has(user_id=self.user_id),
            Meeting.start_at >= now,
            Meeting.start_at <= week_later
        ).order_by(Meeting.start_at)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _get_dependencies(self) -> list[TaskDependency]:
        # Get dependencies for user's tasks
        task_ids_stmt = select(Task.id).where(Task.user_id == self.user_id)
        task_ids_result = await self.db.execute(task_ids_stmt)
        task_ids = [row[0] for row in task_ids_result.all()]

        if not task_ids:
            return []

        stmt = select(TaskDependency).where(
            or_(
                TaskDependency.task_id.in_(task_ids),
                TaskDependency.depends_on_task_id.in_(task_ids)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_project_progress(self, project_id: str) -> dict:
        """Get detailed progress for a specific project."""
        project_stmt = select(Project).where(Project.id == project_id, Project.user_id == self.user_id)
        project_result = await self.db.execute(project_stmt)
        project = project_result.scalar_one_or_none()

        if not project:
            return {"error": "Project not found"}

        task_stmt = select(Task).where(Task.project_id == project_id)
        task_result = await self.db.execute(task_stmt)
        tasks = task_result.scalars().all()

        by_status = defaultdict(int)
        by_priority = defaultdict(int)
        total_estimated = 0
        total_actual = 0

        for task in tasks:
            by_status[task.status.value] += 1
            by_priority[task.priority.value] += 1
            total_estimated += task.estimated_minutes or 0
            total_actual += task.actual_minutes or 0

        completed = by_status.get("completed", 0)
        total = len(tasks)
        progress = (completed / total * 100) if total > 0 else 0

        return {
            "project_id": project.id,
            "project_name": project.name,
            "status": project.status,
            "progress": round(progress, 1),
            "total_tasks": total,
            "by_status": dict(by_status),
            "by_priority": dict(by_priority),
            "total_estimated_minutes": total_estimated,
            "total_actual_minutes": total_actual,
            "efficiency": round((total_actual / total_estimated * 100), 1) if total_estimated > 0 else 0,
        }
