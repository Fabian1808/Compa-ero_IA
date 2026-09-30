from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from enum import Enum

from app.connectors.base import Connector, SyncResult


class AutomationPlatform(str, Enum):
    N8N = "n8n"
    POWER_AUTOMATE = "power_automate"


class AutomationConnector(Connector):
    """Connector for n8n and Power Automate workflow automation."""

    def __init__(
        self,
        platform: AutomationPlatform,
        base_url: str | None = None,
        api_key: str | None = None,
        tenant_id: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
    ):
        self.platform = platform
        self.base_url = base_url or self._default_base_url()
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: str | None = None

    def _default_base_url(self) -> str:
        if self.platform == AutomationPlatform.N8N:
            return "http://localhost:5678"
        return "https://api.flow.microsoft.com"

    @property
    def name(self) -> str:
        return f"automation_{self.platform.value}"

    @property
    def required_scopes(self) -> list[str]:
        if self.platform == AutomationPlatform.POWER_AUTOMATE:
            return [
                "https://service.flow.microsoft.com/.default",
            ]
        return []

    async def authenticate(self, credentials: dict) -> bool:
        if "api_key" in credentials:
            self.api_key = credentials["api_key"]
        if "base_url" in credentials:
            self.base_url = credentials["base_url"]
        if "tenant_id" in credentials:
            self.tenant_id = credentials["tenant_id"]
        if "client_id" in credentials:
            self.client_id = credentials["client_id"]
        if "client_secret" in credentials:
            self.client_secret = credentials["client_secret"]

        if self.platform == AutomationPlatform.POWER_AUTOMATE:
            return await self._authenticate_power_automate()
        return await self._authenticate_n8n()

    async def _authenticate_n8n(self) -> bool:
        if not self.api_key:
            return False
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/workflows",
                    headers={"X-N8N-API-KEY": self.api_key}
                )
                return response.status_code == 200
        except Exception:
            return False

    async def _authenticate_power_automate(self) -> bool:
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            return False

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": "https://service.flow.microsoft.com/.default",
                    }
                )
                if response.status_code == 200:
                    self._access_token = response.json().get("access_token")
                    return True
        except Exception:
            pass
        return False

    async def test_connection(self) -> bool:
        if self.platform == AutomationPlatform.N8N:
            return await self._authenticate_n8n()
        return await self._authenticate_power_automate()

    async def sync_incremental(
        self,
        since: datetime | None = None,
        cursor: str | None = None
    ) -> AsyncIterator[SyncResult]:
        """Sync workflows and runs."""
        result = SyncResult()

        if self.platform == AutomationPlatform.N8N:
            async for r in self._sync_n8n(since):
                yield r
        else:
            async for r in self._sync_power_automate(since):
                yield r

    async def _sync_n8n(self, since: datetime | None) -> AsyncIterator[SyncResult]:
        import httpx
        result = SyncResult()

        async with httpx.AsyncClient() as client:
            headers = {"X-N8N-API-KEY": self.api_key}

            # Get workflows
            response = await client.get(f"{self.base_url}/api/v1/workflows", headers=headers)
            if response.status_code == 200:
                workflows = response.json().get("data", [])
                for wf in workflows:
                    result.items_processed += 1
                    result.items_created += 1
                yield result

            # Get executions (runs)
            params = {"limit": 100}
            if since:
                params["startedAt"] = since.isoformat()

            response = await client.get(
                f"{self.base_url}/api/v1/executions",
                headers=headers,
                params=params
            )
            if response.status_code == 200:
                executions = response.json().get("data", [])
                for ex in executions:
                    result.items_processed += 1
                    result.items_created += 1
                yield result

    async def _sync_power_automate(self, since: datetime | None) -> AsyncIterator[SyncResult]:
        if not self._access_token:
            yield SyncResult()
            return

        import httpx
        result = SyncResult()

        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            }

            # Get flows
            response = await client.get(
                "https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/flows",
                headers=headers
            )
            if response.status_code == 200:
                flows = response.json().get("value", [])
                for flow in flows:
                    result.items_processed += 1
                    result.items_created += 1
                yield result

            # Get runs
            for flow in flows:
                run_response = await client.get(
                    f"https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/flows/{flow['name']}/runs",
                    headers=headers,
                    params={"$top": 50}
                )
                if run_response.status_code == 200:
                    runs = run_response.json().get("value", [])
                    for run in runs:
                        result.items_processed += 1
                        result.items_created += 1
                yield result

    async def get_item(self, item_id: str) -> dict | None:
        """Get workflow/flow by ID."""
        if self.platform == AutomationPlatform.N8N:
            return await self._get_n8n_workflow(item_id)
        return await self._get_power_automate_flow(item_id)

    async def _get_n8n_workflow(self, workflow_id: str) -> dict | None:
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}",
                    headers={"X-N8N-API-KEY": self.api_key}
                )
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return None

    async def _get_power_automate_flow(self, flow_id: str) -> dict | None:
        if not self._access_token:
            return None

        import httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/flows/{flow_id}",
                    headers={"Authorization": f"Bearer {self._access_token}"}
                )
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return None

    async def search(self, query: str, limit: int = 50) -> list[dict]:
        """Search workflows/flows."""
        results = []

        if self.platform == AutomationPlatform.N8N:
            import httpx
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/api/v1/workflows",
                        headers={"X-N8N-API-KEY": self.api_key}
                    )
                    if response.status_code == 200:
                        workflows = response.json().get("data", [])
                        for wf in workflows:
                            if query.lower() in wf.get("name", "").lower():
                                results.append(wf)
            except Exception:
                pass
        else:
            if not self._access_token:
                return results

            import httpx
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/flows",
                        headers={"Authorization": f"Bearer {self._access_token}"}
                    )
                    if response.status_code == 200:
                        flows = response.json().get("value", [])
                        for flow in flows:
                            if query.lower() in flow.get("properties", {}).get("displayName", "").lower():
                                results.append(flow)
            except Exception:
                pass

        return results[:limit]

    # n8n specific operations
    async def create_n8n_workflow(self, workflow_data: dict) -> dict:
        """Create n8n workflow."""
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/workflows",
                    headers={"X-N8N-API-KEY": self.api_key, "Content-Type": "application/json"},
                    json=workflow_data
                )
                if response.status_code in (200, 201):
                    return response.json()
                return {"error": f"Failed: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def execute_n8n_workflow(self, workflow_id: str, data: dict | None = None) -> dict:
        """Execute n8n workflow."""
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}/execute",
                    headers={"X-N8N-API-KEY": self.api_key, "Content-Type": "application/json"},
                    json=data or {}
                )
                if response.status_code in (200, 201):
                    return response.json()
                return {"error": f"Failed: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def activate_n8n_workflow(self, workflow_id: str) -> dict:
        """Activate n8n workflow."""
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}/activate",
                    headers={"X-N8N-API-KEY": self.api_key}
                )
                return {"success": response.status_code == 200}
        except Exception as e:
            return {"error": str(e)}

    async def deactivate_n8n_workflow(self, workflow_id: str) -> dict:
        """Deactivate n8n workflow."""
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}/deactivate",
                    headers={"X-N8N-API-KEY": self.api_key}
                )
                return {"success": response.status_code == 200}
        except Exception as e:
            return {"error": str(e)}

    # Power Automate specific operations
    async def create_power_automate_flow(self, flow_data: dict) -> dict:
        """Create Power Automate flow."""
        if not self._access_token:
            return {"error": "Not authenticated"}

        import httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/flows",
                    headers={
                        "Authorization": f"Bearer {self._access_token}",
                        "Content-Type": "application/json",
                    },
                    json=flow_data
                )
                if response.status_code in (200, 201):
                    return response.json()
                return {"error": f"Failed: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def trigger_power_automate_flow(self, flow_id: str, trigger_data: dict | None = None) -> dict:
        """Trigger Power Automate flow run."""
        if not self._access_token:
            return {"error": "Not authenticated"}

        import httpx
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/flows/{flow_id}/triggers/manual/paths/invoke",
                    headers={
                        "Authorization": f"Bearer {self._access_token}",
                        "Content-Type": "application/json",
                    },
                    json=trigger_data or {}
                )
                return {"success": response.status_code == 200, "response": response.json()}
        except Exception as e:
            return {"error": str(e)}

    # Generic trigger/action methods for both platforms
    async def register_webhook(self, workflow_id: str, webhook_url: str, events: list[str]) -> dict:
        """Register webhook for workflow events."""
        if self.platform == AutomationPlatform.N8N:
            # n8n uses webhook nodes in workflow
            return {"error": "Configure webhook node in n8n workflow"}

        # Power Automate - use HTTP trigger
        return {"info": "Use HTTP trigger in Power Automate flow"}

    async def get_workflow_runs(
        self,
        workflow_id: str,
        status: str | None = None,
        limit: int = 50
    ) -> list[dict]:
        """Get workflow execution history."""
        if self.platform == AutomationPlatform.N8N:
            import httpx
            try:
                async with httpx.AsyncClient() as client:
                    params = {"workflowId": workflow_id, "limit": limit}
                    if status:
                        params["status"] = status

                    response = await client.get(
                        f"{self.base_url}/api/v1/executions",
                        headers={"X-N8N-API-KEY": self.api_key},
                        params=params
                    )
                    if response.status_code == 200:
                        return response.json().get("data", [])
            except Exception:
                pass
        else:
            if not self._access_token:
                return []

            import httpx
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/flows/{workflow_id}/runs",
                        headers={"Authorization": f"Bearer {self._access_token}"},
                        params={"$top": limit}
                    )
                    if response.status_code == 200:
                        return response.json().get("value", [])
            except Exception:
                pass

        return []
