from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from app.connectors.base import Connector, SyncResult


class GitHubConnector(Connector):
    """GitHub connector using GitHub REST API v3 / GraphQL v4."""

    def __init__(self, token: str | None = None, owner: str | None = None, repo: str | None = None):
        self.token = token
        self.owner = owner
        self.repo = repo
        self._base_url = "https://api.github.com"
        self._graphql_url = "https://api.github.com/graphql"

    @property
    def name(self) -> str:
        return "github"

    @property
    def required_scopes(self) -> list[str]:
        return [
            "repo",
            "read:org",
            "read:user",
            "project",
        ]

    async def authenticate(self, credentials: dict) -> bool:
        if "token" in credentials:
            self.token = credentials["token"]
        if "owner" in credentials:
            self.owner = credentials["owner"]
        if "repo" in credentials:
            self.repo = credentials["repo"]
        return bool(self.token)

    async def test_connection(self) -> bool:
        if not self.token:
            return False
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self._base_url}/user",
                    headers=self._headers()
                )
                return response.status_code == 200
        except Exception:
            return False

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def sync_incremental(
        self,
        since: datetime | None = None,
        cursor: str | None = None
    ) -> AsyncIterator[SyncResult]:
        """Sync GitHub issues, PRs, commits."""
        result = SyncResult()

        if not self.token or not self.owner or not self.repo:
            yield result
            return

        import httpx
        async with httpx.AsyncClient() as client:
            headers = self._headers()

            # Sync issues
            params = {"state": "all", "per_page": 100, "sort": "updated", "direction": "desc"}
            if since:
                params["since"] = since.isoformat()

            response = await client.get(
                f"{self._base_url}/repos/{self.owner}/{self.repo}/issues",
                headers=headers,
                params=params
            )
            if response.status_code == 200:
                issues = response.json()
                for issue in issues:
                    if "pull_request" not in issue:  # Skip PRs (they're in pulls endpoint)
                        result.items_processed += 1
                        result.items_created += 1
                yield result

            # Sync pull requests
            params = {"state": "all", "per_page": 100, "sort": "updated", "direction": "desc"}
            if since:
                params["since"] = since.isoformat()

            response = await client.get(
                f"{self._base_url}/repos/{self.owner}/{self.repo}/pulls",
                headers=headers,
                params=params
            )
            if response.status_code == 200:
                prs = response.json()
                for pr in prs:
                    result.items_processed += 1
                    result.items_created += 1
                yield result

            # Sync commits
            params = {"per_page": 100}
            if since:
                params["since"] = since.isoformat()

            response = await client.get(
                f"{self._base_url}/repos/{self.owner}/{self.repo}/commits",
                headers=headers,
                params=params
            )
            if response.status_code == 200:
                commits = response.json()
                for commit in commits:
                    result.items_processed += 1
                    result.items_created += 1
                yield result

    async def get_item(self, item_id: str) -> dict | None:
        """Get GitHub item (issue, PR, commit)."""
        if not self.token:
            return None

        import httpx
        async with httpx.AsyncClient() as client:
            headers = self._headers()

            # Try issue
            response = await client.get(
                f"{self._base_url}/repos/{self.owner}/{self.repo}/issues/{item_id}",
                headers=headers
            )
            if response.status_code == 200:
                return {"type": "issue", **response.json()}

            # Try PR
            response = await client.get(
                f"{self._base_url}/repos/{self.owner}/{self.repo}/pulls/{item_id}",
                headers=headers
            )
            if response.status_code == 200:
                return {"type": "pull_request", **response.json()}

            # Try commit
            response = await client.get(
                f"{self._base_url}/repos/{self.owner}/{self.repo}/commits/{item_id}",
                headers=headers
            )
            if response.status_code == 200:
                return {"type": "commit", **response.json()}

        return None

    async def search(self, query: str, limit: int = 50) -> list[dict]:
        """Search GitHub issues, PRs, code."""
        results = []
        if not self.token:
            return results

        import httpx
        async with httpx.AsyncClient() as client:
            headers = self._headers()

            # Search issues and PRs
            response = await client.get(
                f"{self._base_url}/search/issues",
                headers=headers,
                params={
                    "q": f"repo:{self.owner}/{self.repo} {query}",
                    "per_page": limit,
                }
            )
            if response.status_code == 200:
                items = response.json().get("items", [])
                for item in items:
                    results.append({"type": "pull_request" if "pull_request" in item else "issue", **item})

        return results[:limit]

    # GitHub-specific operations
    async def get_issues(
        self,
        state: str = "open",
        labels: list[str] | None = None,
        assignee: str | None = None,
        limit: int = 100
    ) -> list[dict]:
        """Get issues with filters."""
        if not self.token:
            return []

        import httpx
        async with httpx.AsyncClient() as client:
            headers = self._headers()
            params = {"state": state, "per_page": limit}

            if labels:
                params["labels"] = ",".join(labels)
            if assignee:
                params["assignee"] = assignee

            response = await client.get(
                f"{self._base_url}/repos/{self.owner}/{self.repo}/issues",
                headers=headers,
                params=params
            )
            if response.status_code == 200:
                return [i for i in response.json() if "pull_request" not in i]
        return []

    async def get_pull_requests(
        self,
        state: str = "open",
        base: str | None = None,
        head: str | None = None,
        limit: int = 100
    ) -> list[dict]:
        """Get pull requests with filters."""
        if not self.token:
            return []

        import httpx
        async with httpx.AsyncClient() as client:
            headers = self._headers()
            params = {"state": state, "per_page": limit}

            if base:
                params["base"] = base
            if head:
                params["head"] = head

            response = await client.get(
                f"{self._base_url}/repos/{self.owner}/{self.repo}/pulls",
                headers=headers,
                params=params
            )
            if response.status_code == 200:
                return response.json()
        return []

    async def get_commits(
        self,
        sha: str | None = None,
        path: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100
    ) -> list[dict]:
        """Get commits with filters."""
        if not self.token:
            return []

        import httpx
        async with httpx.AsyncClient() as client:
            headers = self._headers()
            params = {"per_page": limit}

            if sha:
                params["sha"] = sha
            if path:
                params["path"] = path
            if since:
                params["since"] = since.isoformat()
            if until:
                params["until"] = until.isoformat()

            response = await client.get(
                f"{self._base_url}/repos/{self.owner}/{self.repo}/commits",
                headers=headers,
                params=params
            )
            if response.status_code == 200:
                return response.json()
        return []

    async def link_issue_to_task(self, issue_number: int, task_id: str) -> dict:
        """Link GitHub issue to local task (add comment with task reference)."""
        if not self.token:
            return {"error": "Not authenticated"}

        import httpx
        async with httpx.AsyncClient() as client:
            headers = self._headers()

            comment = f"Linked to AI Workmate task: {task_id}"
            response = await client.post(
                f"{self._base_url}/repos/{self.owner}/{self.repo}/issues/{issue_number}/comments",
                headers=headers,
                json={"body": comment}
            )

            if response.status_code == 201:
                return {"success": True, "comment": response.json()}
            return {"error": f"Failed: {response.status_code}"}

    async def create_issue_from_task(self, task_data: dict) -> dict:
        """Create GitHub issue from local task."""
        if not self.token:
            return {"error": "Not authenticated"}

        import httpx
        async with httpx.AsyncClient() as client:
            headers = self._headers()

            body = task_data.get("description", "")
            if task_data.get("deadline_at"):
                body += f"\n\n**Deadline:** {task_data['deadline_at']}"
            body += f"\n\n---\n*Created from AI Workmate task: {task_data.get('id', 'unknown')}*"

            response = await client.post(
                f"{self._base_url}/repos/{self.owner}/{self.repo}/issues",
                headers=headers,
                json={
                    "title": task_data.get("title", "Untitled Task"),
                    "body": body,
                    "labels": [task_data.get("priority", "medium"), "ai-workmate"],
                }
            )

            if response.status_code == 201:
                return {"success": True, "issue": response.json()}
            return {"error": f"Failed: {response.status_code}", "details": response.text}

    async def get_repository_info(self) -> dict | None:
        """Get repository information."""
        if not self.token:
            return None

        import httpx
        async with httpx.AsyncClient() as client:
            headers = self._headers()
            response = await client.get(
                f"{self._base_url}/repos/{self.owner}/{self.repo}",
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
        return None
