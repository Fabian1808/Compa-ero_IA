from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from app.connectors.base import Connector, SyncResult
from app.services.graph_service import GraphService


class PowerBIConnector(Connector):
    """Power BI connector using Power BI REST API."""

    def __init__(self, graph_service: GraphService, account_id: str, user_id: str):
        self.graph_service = graph_service
        self.account_id = account_id
        self.user_id = user_id
        self._access_token: str | None = None

    @property
    def name(self) -> str:
        return "powerbi"

    @property
    def required_scopes(self) -> list[str]:
        return [
            "https://analysis.windows.net/powerbi/api/Dataset.ReadWrite.All",
            "https://analysis.windows.net/powerbi/api/Report.ReadWrite.All",
            "https://analysis.windows.net/powerbi/api/Dashboard.ReadWrite.All",
            "https://analysis.windows.net/powerbi/api/Workspace.ReadWrite.All",
        ]

    async def authenticate(self, credentials: dict) -> bool:
        # Power BI uses separate token from Graph
        self._access_token = credentials.get("access_token")
        return bool(self._access_token)

    def _get_account(self):
        from app.models.account import Account
        account = Account()
        account.id = self.account_id
        account.user_id = self.user_id
        return account

    async def test_connection(self) -> bool:
        if not self._access_token:
            return False
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.powerbi.com/v1.0/myorg/groups",
                    headers={"Authorization": f"Bearer {self._access_token}"}
                )
                return response.status_code == 200
        except Exception:
            return False

    async def sync_incremental(
        self,
        since: datetime | None = None,
        cursor: str | None = None
    ) -> AsyncIterator[SyncResult]:
        """Sync Power BI workspaces, datasets, reports."""
        result = SyncResult()

        if not self._access_token:
            yield result
            return

        import httpx
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self._access_token}"}

            # Sync workspaces
            response = await client.get("https://api.powerbi.com/v1.0/myorg/groups", headers=headers)
            if response.status_code == 200:
                workspaces = response.json().get("value", [])
                for ws in workspaces:
                    result.items_processed += 1
                    result.items_created += 1

                    # Sync datasets in workspace
                    ds_response = await client.get(
                        f"https://api.powerbi.com/v1.0/myorg/groups/{ws['id']}/datasets",
                        headers=headers
                    )
                    if ds_response.status_code == 200:
                        datasets = ds_response.json().get("value", [])
                        for ds in datasets:
                            result.items_processed += 1
                            result.items_created += 1

                    # Sync reports
                    rpt_response = await client.get(
                        f"https://api.powerbi.com/v1.0/myorg/groups/{ws['id']}/reports",
                        headers=headers
                    )
                    if rpt_response.status_code == 200:
                        reports = rpt_response.json().get("value", [])
                        for rpt in reports:
                            result.items_processed += 1
                            result.items_created += 1

                    yield result

    async def get_item(self, item_id: str) -> dict | None:
        """Get Power BI item (workspace/dataset/report)."""
        if not self._access_token:
            return None
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                # Try workspace first
                response = await client.get(
                    f"https://api.powerbi.com/v1.0/myorg/groups/{item_id}",
                    headers={"Authorization": f"Bearer {self._access_token}"}
                )
                if response.status_code == 200:
                    return response.json()
        except Exception:
            pass
        return None

    async def search(self, query: str, limit: int = 50) -> list[dict]:
        """Search Power BI items."""
        results = []
        if not self._access_token:
            return results

        import httpx
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self._access_token}"}

            # Search workspaces
            response = await client.get("https://api.powerbi.com/v1.0/myorg/groups", headers=headers)
            if response.status_code == 200:
                workspaces = response.json().get("value", [])
                for ws in workspaces:
                    if query.lower() in ws.get("name", "").lower():
                        results.append({"type": "workspace", **ws})
                        if len(results) >= limit:
                            return results

        return results[:limit]

    # Productivity metrics methods
    async def get_productivity_metrics(self, workspace_id: str, dataset_id: str) -> dict:
        """Get productivity metrics from Power BI dataset."""
        if not self._access_token:
            return {"error": "Not authenticated"}

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self._access_token}"}

                # Execute DAX query for metrics
                dax_query = """
                EVALUATE
                SUMMARIZE(
                    'Tasks',
                    'Tasks'[Status],
                    'Tasks'[Priority],
                    "Count", COUNTROWS('Tasks'),
                    "AvgDaysOpen", AVERAGEX('Tasks', DATEDIFF('Tasks'[CreatedAt], TODAY(), DAY))
                )
                """

                response = await client.post(
                    f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/executeQueries",
                    headers=headers,
                    json={"queries": [{"query": dax_query}]}
                )

                if response.status_code == 200:
                    return response.json()
                return {"error": f"Query failed: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_dashboard_data(self, workspace_id: str, dashboard_id: str) -> dict:
        """Get dashboard tiles data."""
        if not self._access_token:
            return {"error": "Not authenticated"}

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self._access_token}"}

                response = await client.get(
                    f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/dashboards/{dashboard_id}/tiles",
                    headers=headers
                )

                if response.status_code == 200:
                    return response.json()
                return {"error": f"Failed: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def refresh_dataset(self, workspace_id: str, dataset_id: str) -> dict:
        """Trigger dataset refresh."""
        if not self._access_token:
            return {"error": "Not authenticated"}

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {self._access_token}"}

                response = await client.post(
                    f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/refreshes",
                    headers=headers
                )

                return {"success": response.status_code == 202, "status": response.status_code}
        except Exception as e:
            return {"error": str(e)}
