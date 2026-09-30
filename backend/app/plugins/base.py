from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4


class PluginStatus(str, Enum):
    """Plugin installation status."""
    AVAILABLE = "available"
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class PluginCategory(str, Enum):
    """Plugin categories."""
    CONNECTOR = "connector"
    AI_TOOL = "ai_tool"
    UI_EXTENSION = "ui_extension"
    AUTOMATION = "automation"
    INTEGRATION = "integration"


@dataclass
class PluginPermission:
    """Permission required by a plugin."""
    name: str
    description: str
    required: bool = True
    scope: str = "user"  # user, admin, system


@dataclass
class PluginManifest:
    """Plugin manifest/metadata."""
    id: str
    name: str
    version: str
    description: str
    author: str
    category: PluginCategory
    homepage: str = ""
    repository: str = ""
    license: str = "MIT"
    min_app_version: str = "0.1.0"
    max_app_version: str = ""
    dependencies: list[str] = field(default_factory=list)
    permissions: list[PluginPermission] = field(default_factory=list)
    entry_point: str = ""  # Python module path
    config_schema: dict = field(default_factory=dict)  # JSON schema for config
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PluginInstance:
    """Installed plugin instance."""
    plugin_id: str
    instance_id: str = field(default_factory=lambda: str(uuid4()))
    status: PluginStatus = PluginStatus.INSTALLED
    config: dict = field(default_factory=dict)
    installed_at: datetime = field(default_factory=datetime.utcnow)
    enabled_at: datetime | None = None
    last_error: str | None = None


class BasePlugin(ABC):
    """Base class for all plugins."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self._manifest: PluginManifest | None = None

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest:
        """Return plugin manifest."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize plugin. Return True if successful."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup plugin resources."""

    async def configure(self, config: dict) -> bool:
        """Update plugin configuration."""
        self.config = config
        return True

    async def health_check(self) -> dict:
        """Return health status."""
        return {"status": "healthy", "plugin": self.manifest.id}

    def get_permissions(self) -> list[PluginPermission]:
        """Get required permissions."""
        return self.manifest.permissions


class ConnectorPlugin(BasePlugin):
    """Base class for connector plugins."""

    @property
    @abstractmethod
    def connector_class(self):
        """Return the connector class."""

    async def initialize(self) -> bool:
        return True

    async def shutdown(self) -> None:
        pass


class AIToolPlugin(BasePlugin):
    """Base class for AI tool plugins."""

    @property
    @abstractmethod
    def tool_definition(self) -> dict:
        """Return tool definition for AI."""

    @property
    @abstractmethod
    def tool_executor(self):
        """Return tool executor instance."""

    async def initialize(self) -> bool:
        return True

    async def shutdown(self) -> None:
        pass


class UIExtensionPlugin(BasePlugin):
    """Base class for UI extension plugins."""

    @property
    @abstractmethod
    def routes(self) -> list[dict]:
        """Return UI routes."""

    @property
    @abstractmethod
    def components(self) -> dict:
        """Return component exports."""

    async def initialize(self) -> bool:
        return True

    async def shutdown(self) -> None:
        pass
