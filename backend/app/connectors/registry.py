from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.connectors.base import Connector
from app.connectors.outlook import OutlookConnector
from app.connectors.teams import TeamsConnector
from app.connectors.onedrive import OneDriveConnector
from app.connectors.sharepoint import SharePointConnector
from app.connectors.excel import ExcelConnector
from app.connectors.powerbi import PowerBIConnector
from app.connectors.sap import SAPConnector
from app.connectors.github import GitHubConnector
from app.connectors.automation import AutomationConnector, AutomationPlatform
from app.models.account import Account
from app.services.graph_service import GraphService


# Microsoft Graph-based connector types
MICROSOFT_CONNECTORS = {
    "outlook": OutlookConnector,
    "teams": TeamsConnector,
    "onedrive": OneDriveConnector,
    "sharepoint": SharePointConnector,
    "excel": ExcelConnector,
    "powerbi": PowerBIConnector,
}

# External connector types (non-Microsoft)
EXTERNAL_CONNECTORS = {
    "sap": SAPConnector,
    "github": GitHubConnector,
    "n8n": lambda *args, **kwargs: AutomationConnector(AutomationPlatform.N8N, *args, **kwargs),
    "power_automate": lambda *args, **kwargs: AutomationConnector(AutomationPlatform.POWER_AUTOMATE, *args, **kwargs),
}

ALL_CONNECTOR_TYPES = {**MICROSOFT_CONNECTORS, **EXTERNAL_CONNECTORS}


class ConnectorRegistry:
    """Registry for managing connectors."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._connectors: dict[str, Connector] = {}
        self._graph_service: GraphService | None = None
        self._external_configs: dict[str, dict] = {}

    @property
    def graph_service(self) -> GraphService:
        if self._graph_service is None:
            self._graph_service = GraphService(self.db)
        return self._graph_service

    def register_external_config(self, connector_type: str, config: dict) -> None:
        """Register configuration for external connectors."""
        self._external_configs[connector_type] = config

    def get_external_config(self, connector_type: str) -> dict:
        return self._external_configs.get(connector_type, {})

    def get_connector(
        self,
        account: Account,
        connector_type: str = "outlook",
        external_config: dict | None = None
    ) -> Connector:
        key = f"{account.provider}:{connector_type}:{account.id}"
        if key not in self._connectors:
            if account.provider == "microsoft":
                if connector_type in MICROSOFT_CONNECTORS:
                    connector_class = MICROSOFT_CONNECTORS[connector_type]
                    self._connectors[key] = connector_class(self.graph_service, account)
                else:
                    raise ValueError(f"Unknown Microsoft connector type: {connector_type}")
            elif connector_type in EXTERNAL_CONNECTORS:
                # External connectors need their own config
                config = external_config or self._external_configs.get(connector_type, {})
                connector_factory = EXTERNAL_CONNECTORS[connector_type]
                self._connectors[key] = connector_factory(**config)
            else:
                raise ValueError(f"Unknown connector type: {connector_type}")
        return self._connectors[key]

    async def test_connector(
        self,
        account: Account,
        connector_type: str = "outlook",
        external_config: dict | None = None
    ) -> bool:
        connector = self.get_connector(account, connector_type, external_config)
        return await connector.test_connection()

    def clear_connector(self, account: Account, connector_type: str = "outlook") -> None:
        key = f"{account.provider}:{connector_type}:{account.id}"
        if key in self._connectors:
            del self._connectors[key]

    def list_available_connectors(self) -> dict[str, list[str]]:
        """List all available connector types by category."""
        return {
            "microsoft": list(MICROSOFT_CONNECTORS.keys()),
            "external": list(EXTERNAL_CONNECTORS.keys()),
        }

    def get_connector_info(self, connector_type: str) -> dict:
        """Get metadata about a connector type."""
        info = {
            "outlook": {"name": "Outlook", "category": "microsoft", "description": "Email, Calendar, Contacts"},
            "teams": {"name": "Microsoft Teams", "category": "microsoft", "description": "Chats, Channels, Meetings"},
            "onedrive": {"name": "OneDrive", "category": "microsoft", "description": "Files, Documents"},
            "sharepoint": {"name": "SharePoint", "category": "microsoft", "description": "Sites, Lists, Documents"},
            "excel": {"name": "Excel", "category": "microsoft", "description": "Spreadsheets, Data Import/Export"},
            "powerbi": {"name": "Power BI", "category": "microsoft", "description": "Dashboards, Metrics"},
            "sap": {"name": "SAP", "category": "external", "description": "ERP, Orders, Finance"},
            "github": {"name": "GitHub", "category": "external", "description": "Issues, PRs, Commits"},
            "n8n": {"name": "n8n", "category": "external", "description": "Workflow Automation"},
            "power_automate": {"name": "Power Automate", "category": "external", "description": "Cloud Flows"},
        }
        return info.get(connector_type, {"name": connector_type, "category": "unknown"})