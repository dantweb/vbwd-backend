"""Plugin manager for loading and managing plugins."""
from typing import Dict, List, Optional
from src.plugins.base import BasePlugin, PluginStatus
from src.events.dispatcher import EventDispatcher, Event


class PluginManager:
    """
    Plugin manager for loading and managing plugins.

    Handles plugin discovery, registration, lifecycle, and dependencies.
    """

    def __init__(self, event_dispatcher: Optional[EventDispatcher] = None):
        self._plugins: Dict[str, BasePlugin] = {}
        self._event_dispatcher = event_dispatcher or EventDispatcher()

    @property
    def event_dispatcher(self) -> EventDispatcher:
        """Get event dispatcher."""
        return self._event_dispatcher

    def register_plugin(self, plugin: BasePlugin) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance to register

        Raises:
            ValueError: If plugin already registered
        """
        name = plugin.metadata.name

        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' already registered")

        self._plugins[name] = plugin

        # Emit event
        event = Event(name="plugin.registered", data={"plugin_name": name})
        self._event_dispatcher.dispatch(event)

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """Get plugin by name."""
        return self._plugins.get(name)

    def get_all_plugins(self) -> List[BasePlugin]:
        """Get all registered plugins."""
        return list(self._plugins.values())

    def get_enabled_plugins(self) -> List[BasePlugin]:
        """Get all enabled plugins."""
        return [
            plugin
            for plugin in self._plugins.values()
            if plugin.status == PluginStatus.ENABLED
        ]

    def initialize_plugin(
        self,
        name: str,
        config: Optional[Dict] = None,
    ) -> None:
        """
        Initialize plugin with configuration.

        Args:
            name: Plugin name
            config: Optional configuration

        Raises:
            ValueError: If plugin not found
        """
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found")

        plugin.initialize(config)

        # Emit event
        event = Event(name="plugin.initialized", data={"plugin_name": name})
        self._event_dispatcher.dispatch(event)

    def enable_plugin(self, name: str) -> None:
        """
        Enable plugin.

        Args:
            name: Plugin name

        Raises:
            ValueError: If plugin not found or dependencies not met
        """
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found")

        # Check dependencies
        for dep in plugin.metadata.dependencies or []:
            dep_plugin = self.get_plugin(dep)
            if not dep_plugin or dep_plugin.status != PluginStatus.ENABLED:
                raise ValueError(f"Dependency '{dep}' not enabled")

        plugin.enable()

        # Emit event
        event = Event(name="plugin.enabled", data={"plugin_name": name})
        self._event_dispatcher.dispatch(event)

    def disable_plugin(self, name: str) -> None:
        """
        Disable plugin.

        Args:
            name: Plugin name

        Raises:
            ValueError: If plugin not found or other plugins depend on it
        """
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin '{name}' not found")

        # Check if other plugins depend on this one
        dependent_plugins = [
            p
            for p in self._plugins.values()
            if name in (p.metadata.dependencies or [])
            and p.status == PluginStatus.ENABLED
        ]

        if dependent_plugins:
            names = [p.metadata.name for p in dependent_plugins]
            raise ValueError(f"Cannot disable: plugins {names} depend on it")

        plugin.disable()

        # Emit event
        event = Event(name="plugin.disabled", data={"plugin_name": name})
        self._event_dispatcher.dispatch(event)
