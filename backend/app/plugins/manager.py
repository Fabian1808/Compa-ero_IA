from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

from app.plugins.base import (
    AIToolPlugin,
    BasePlugin,
    ConnectorPlugin,
    PluginCategory,
    PluginInstance,
    PluginManifest,
    PluginStatus,
    UIExtensionPlugin,
)


class PluginManager:
    """Manages plugin lifecycle: discovery, installation, enabling, configuration."""

    def __init__(self, plugins_dir: str = "./plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)

        self._manifests: dict[str, PluginManifest] = {}
        self._instances: dict[str, PluginInstance] = {}
        self._loaded_plugins: dict[str, BasePlugin] = {}
        self._plugin_modules: dict[str, object] = {}

    async def discover_plugins(self) -> list[PluginManifest]:
        """Discover available plugins from plugins directory."""
        discovered = []

        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue

            manifest_path = plugin_dir / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path) as f:
                    manifest_data = json.load(f)

                manifest = PluginManifest(**manifest_data)
                self._manifests[manifest.id] = manifest
                discovered.append(manifest)
            except Exception as e:
                print(f"Failed to load plugin {plugin_dir.name}: {e}")

        return discovered

    async def install_plugin(self, plugin_id: str, config: dict | None = None) -> PluginInstance:
        """Install a plugin."""
        if plugin_id not in self._manifests:
            raise ValueError(f"Plugin not found: {plugin_id}")

        manifest = self._manifests[plugin_id]

        # Check dependencies
        for dep in manifest.dependencies:
            if dep not in self._manifests:
                raise ValueError(f"Missing dependency: {dep}")
            dep_instance = self._instances.get(dep)
            if not dep_instance or dep_instance.status != PluginStatus.ENABLED:
                raise ValueError(f"Dependency not enabled: {dep}")

        # Create instance
        instance = PluginInstance(
            plugin_id=plugin_id,
            config=config or {},
            status=PluginStatus.INSTALLED,
        )

        self._instances[instance.instance_id] = instance
        return instance

    async def enable_plugin(self, instance_id: str) -> bool:
        """Enable a plugin instance."""
        instance = self._instances.get(instance_id)
        if not instance:
            return False

        manifest = self._manifests[instance.plugin_id]

        # Load plugin module
        try:
            plugin = await self._load_plugin_module(manifest)
            if not plugin:
                instance.status = PluginStatus.ERROR
                instance.last_error = "Failed to load plugin module"
                return False

            # Initialize plugin
            success = await plugin.initialize()
            if not success:
                instance.status = PluginStatus.ERROR
                instance.last_error = "Plugin initialization failed"
                return False

            self._loaded_plugins[instance_id] = plugin
            instance.status = PluginStatus.ENABLED
            instance.enabled_at = __import__('datetime').datetime.utcnow()
            instance.last_error = None
            return True
        except Exception as e:
            instance.status = PluginStatus.ERROR
            instance.last_error = str(e)
            return False

    async def disable_plugin(self, instance_id: str) -> bool:
        """Disable a plugin instance."""
        instance = self._instances.get(instance_id)
        if not instance:
            return False

        plugin = self._loaded_plugins.get(instance_id)
        if plugin:
            try:
                await plugin.shutdown()
            except Exception:
                pass
            del self._loaded_plugins[instance_id]

        instance.status = PluginStatus.DISABLED
        return True

    async def uninstall_plugin(self, instance_id: str) -> bool:
        """Uninstall a plugin instance."""
        await self.disable_plugin(instance_id)

        instance = self._instances.pop(instance_id, None)
        return instance is not None

    async def configure_plugin(self, instance_id: str, config: dict) -> bool:
        """Update plugin configuration."""
        instance = self._instances.get(instance_id)
        if not instance:
            return False

        plugin = self._loaded_plugins.get(instance_id)
        if plugin:
            success = await plugin.configure(config)
            if success:
                instance.config = config
            return success

        instance.config = config
        return True

    async def _load_plugin_module(self, manifest: PluginManifest) -> BasePlugin | None:
        """Load plugin Python module."""
        if manifest.id in self._plugin_modules:
            module = self._plugin_modules[manifest.id]
        else:
            # Add plugin directory to path
            plugin_dir = self.plugins_dir / manifest.id
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))

            try:
                module = importlib.import_module(manifest.entry_point)
                self._plugin_modules[manifest.id] = module
            except Exception as e:
                print(f"Failed to import plugin {manifest.id}: {e}")
                return None

        # Get plugin class from module
        plugin_class_name = manifest.entry_point.split(".")[-1].title().replace("_", "") + "Plugin"
        plugin_class = getattr(module, plugin_class_name, None)

        if not plugin_class:
            # Try common names
            for name in ["Plugin", "MainPlugin", f"{manifest.id.title().replace('-', '')}Plugin"]:
                plugin_class = getattr(module, name, None)
                if plugin_class:
                    break

        if not plugin_class or not issubclass(plugin_class, BasePlugin):
            return None

        return plugin_class(self._instances.get(manifest.id, PluginInstance(plugin_id=manifest.id)).config)

    def get_plugin(self, instance_id: str) -> BasePlugin | None:
        """Get loaded plugin instance."""
        return self._loaded_plugins.get(instance_id)

    def get_instance(self, instance_id: str) -> PluginInstance | None:
        """Get plugin instance."""
        return self._instances.get(instance_id)

    def list_instances(self, plugin_id: str | None = None) -> list[PluginInstance]:
        """List plugin instances."""
        instances = list(self._instances.values())
        if plugin_id:
            instances = [i for i in instances if i.plugin_id == plugin_id]
        return instances

    def get_manifest(self, plugin_id: str) -> PluginManifest | None:
        """Get plugin manifest."""
        return self._manifests.get(plugin_id)

    async def get_all_connectors(self) -> list[ConnectorPlugin]:
        """Get all enabled connector plugins."""
        connectors = []
        for instance_id, plugin in self._loaded_plugins.items():
            if isinstance(plugin, ConnectorPlugin):
                connectors.append(plugin)
        return connectors

    async def get_all_ai_tools(self) -> list[AIToolPlugin]:
        """Get all enabled AI tool plugins."""
        tools = []
        for instance_id, plugin in self._loaded_plugins.items():
            if isinstance(plugin, AIToolPlugin):
                tools.append(plugin)
        return tools

    async def get_all_ui_extensions(self) -> list[UIExtensionPlugin]:
        """Get all enabled UI extension plugins."""
        extensions = []
        for instance_id, plugin in self._loaded_plugins.items():
            if isinstance(plugin, UIExtensionPlugin):
                extensions.append(plugin)
        return extensions


class PluginMarketplace:
    """Plugin marketplace for discovering and installing plugins."""

    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager

    async def search_plugins(
        self,
        query: str = "",
        category: PluginCategory | None = None,
        tags: list[str] | None = None
    ) -> list[PluginManifest]:
        """Search available plugins."""
        await self.plugin_manager.discover_plugins()

        results = list(self.plugin_manager._manifests.values())

        if query:
            query_lower = query.lower()
            results = [p for p in results if query_lower in p.name.lower() or query_lower in p.description.lower()]

        if category:
            results = [p for p in results if p.category == category]

        if tags:
            results = [p for p in results if all(tag in p.tags for tag in tags)]

        return results

    async def get_plugin_details(self, plugin_id: str) -> PluginManifest | None:
        """Get detailed plugin information."""
        return self.plugin_manager.get_manifest(plugin_id)

    async def install_from_marketplace(
        self,
        plugin_id: str,
        config: dict | None = None
    ) -> PluginInstance:
        """Install plugin from marketplace."""
        return await self.plugin_manager.install_plugin(plugin_id, config)

    async def update_plugin(self, instance_id: str) -> bool:
        """Update plugin to latest version."""
        # This would check marketplace for updates
        # For now, just reinstall
        instance = self.plugin_manager.get_instance(instance_id)
        if not instance:
            return False

        config = instance.config
        await self.plugin_manager.uninstall_plugin(instance_id)
        new_instance = await self.plugin_manager.install_plugin(instance.plugin_id, config)
        return await self.plugin_manager.enable_plugin(new_instance.instance_id)


def create_default_manifest(
    plugin_id: str,
    name: str,
    version: str,
    description: str,
    author: str,
    category: PluginCategory,
    entry_point: str,
    **kwargs
) -> PluginManifest:
    """Helper to create a plugin manifest."""
    return PluginManifest(
        id=plugin_id,
        name=name,
        version=version,
        description=description,
        author=author,
        category=category,
        entry_point=entry_point,
        **kwargs
    )
