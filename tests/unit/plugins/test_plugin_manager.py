"""Tests for PluginManager."""
import pytest
from src.plugins.manager import PluginManager
from src.plugins.base import BasePlugin, PluginMetadata, PluginStatus
from src.events.dispatcher import Event


class MockPlugin(BasePlugin):
    """Mock plugin for testing."""

    def __init__(self, name: str, dependencies: list = None):
        super().__init__()
        self._name = name
        self._dependencies = dependencies or []

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self._name,
            version="1.0.0",
            author="Test",
            description="Test plugin",
            dependencies=self._dependencies,
        )


class TestPluginManagerRegistration:
    """Test cases for plugin registration."""

    @pytest.fixture
    def plugin_manager(self):
        """Create PluginManager."""
        return PluginManager()

    def test_register_plugin(self, plugin_manager):
        """register_plugin should register plugin."""
        plugin = MockPlugin("test-plugin")

        plugin_manager.register_plugin(plugin)

        assert plugin_manager.get_plugin("test-plugin") == plugin

    def test_register_duplicate_raises_error(self, plugin_manager):
        """register_plugin should raise error for duplicate."""
        plugin1 = MockPlugin("test-plugin")
        plugin2 = MockPlugin("test-plugin")

        plugin_manager.register_plugin(plugin1)

        with pytest.raises(ValueError, match="already registered"):
            plugin_manager.register_plugin(plugin2)

    def test_get_plugin_not_found(self, plugin_manager):
        """get_plugin should return None if not found."""
        result = plugin_manager.get_plugin("nonexistent")

        assert result is None

    def test_get_all_plugins(self, plugin_manager):
        """get_all_plugins should return all registered."""
        plugin1 = MockPlugin("plugin1")
        plugin2 = MockPlugin("plugin2")

        plugin_manager.register_plugin(plugin1)
        plugin_manager.register_plugin(plugin2)

        plugins = plugin_manager.get_all_plugins()

        assert len(plugins) == 2
        assert plugin1 in plugins
        assert plugin2 in plugins

    def test_get_enabled_plugins(self, plugin_manager):
        """get_enabled_plugins should return only enabled."""
        plugin1 = MockPlugin("plugin1")
        plugin2 = MockPlugin("plugin2")

        plugin_manager.register_plugin(plugin1)
        plugin_manager.register_plugin(plugin2)

        plugin_manager.initialize_plugin("plugin1")
        plugin_manager.enable_plugin("plugin1")

        enabled = plugin_manager.get_enabled_plugins()

        assert len(enabled) == 1
        assert plugin1 in enabled
        assert plugin2 not in enabled


class TestPluginManagerLifecycle:
    """Test cases for plugin lifecycle."""

    @pytest.fixture
    def plugin_manager(self):
        """Create PluginManager."""
        return PluginManager()

    def test_initialize_plugin(self, plugin_manager):
        """initialize_plugin should initialize with config."""
        plugin = MockPlugin("test-plugin")
        plugin_manager.register_plugin(plugin)

        config = {"api_key": "test123"}
        plugin_manager.initialize_plugin("test-plugin", config)

        assert plugin.status == PluginStatus.INITIALIZED
        assert plugin.get_config("api_key") == "test123"

    def test_initialize_plugin_not_found(self, plugin_manager):
        """initialize_plugin should raise if plugin not found."""
        with pytest.raises(ValueError, match="not found"):
            plugin_manager.initialize_plugin("nonexistent")

    def test_enable_plugin(self, plugin_manager):
        """enable_plugin should enable plugin."""
        plugin = MockPlugin("test-plugin")
        plugin_manager.register_plugin(plugin)
        plugin_manager.initialize_plugin("test-plugin")

        plugin_manager.enable_plugin("test-plugin")

        assert plugin.status == PluginStatus.ENABLED

    def test_enable_plugin_not_initialized(self, plugin_manager):
        """enable_plugin should raise if not initialized."""
        plugin = MockPlugin("test-plugin")
        plugin_manager.register_plugin(plugin)

        with pytest.raises(ValueError, match="Cannot enable"):
            plugin_manager.enable_plugin("test-plugin")

    def test_enable_plugin_not_found(self, plugin_manager):
        """enable_plugin should raise if plugin not found."""
        with pytest.raises(ValueError, match="not found"):
            plugin_manager.enable_plugin("nonexistent")

    def test_disable_plugin(self, plugin_manager):
        """disable_plugin should disable plugin."""
        plugin = MockPlugin("test-plugin")
        plugin_manager.register_plugin(plugin)
        plugin_manager.initialize_plugin("test-plugin")
        plugin_manager.enable_plugin("test-plugin")

        plugin_manager.disable_plugin("test-plugin")

        assert plugin.status == PluginStatus.DISABLED

    def test_disable_plugin_not_found(self, plugin_manager):
        """disable_plugin should raise if plugin not found."""
        with pytest.raises(ValueError, match="not found"):
            plugin_manager.disable_plugin("nonexistent")


class TestPluginManagerDependencies:
    """Test cases for plugin dependencies."""

    @pytest.fixture
    def plugin_manager(self):
        """Create PluginManager."""
        return PluginManager()

    def test_enable_with_dependencies_met(self, plugin_manager):
        """enable_plugin should succeed when dependencies are met."""
        base_plugin = MockPlugin("base")
        dependent_plugin = MockPlugin("dependent", dependencies=["base"])

        plugin_manager.register_plugin(base_plugin)
        plugin_manager.register_plugin(dependent_plugin)

        plugin_manager.initialize_plugin("base")
        plugin_manager.enable_plugin("base")

        plugin_manager.initialize_plugin("dependent")
        plugin_manager.enable_plugin("dependent")

        assert dependent_plugin.status == PluginStatus.ENABLED

    def test_enable_with_dependencies_not_met(self, plugin_manager):
        """enable_plugin should raise if dependencies not met."""
        dependent_plugin = MockPlugin("dependent", dependencies=["missing"])

        plugin_manager.register_plugin(dependent_plugin)
        plugin_manager.initialize_plugin("dependent")

        with pytest.raises(ValueError, match="not enabled"):
            plugin_manager.enable_plugin("dependent")

    def test_enable_with_dependency_disabled(self, plugin_manager):
        """enable_plugin should raise if dependency is disabled."""
        base_plugin = MockPlugin("base")
        dependent_plugin = MockPlugin("dependent", dependencies=["base"])

        plugin_manager.register_plugin(base_plugin)
        plugin_manager.register_plugin(dependent_plugin)

        plugin_manager.initialize_plugin("base")
        # Don't enable base

        plugin_manager.initialize_plugin("dependent")

        with pytest.raises(ValueError, match="not enabled"):
            plugin_manager.enable_plugin("dependent")

    def test_disable_with_dependents_raises_error(self, plugin_manager):
        """disable_plugin should raise if other plugins depend on it."""
        base_plugin = MockPlugin("base")
        dependent_plugin = MockPlugin("dependent", dependencies=["base"])

        plugin_manager.register_plugin(base_plugin)
        plugin_manager.register_plugin(dependent_plugin)

        plugin_manager.initialize_plugin("base")
        plugin_manager.enable_plugin("base")
        plugin_manager.initialize_plugin("dependent")
        plugin_manager.enable_plugin("dependent")

        with pytest.raises(ValueError, match="depend on it"):
            plugin_manager.disable_plugin("base")

    def test_disable_after_dependent_disabled(self, plugin_manager):
        """disable_plugin should succeed after dependent is disabled."""
        base_plugin = MockPlugin("base")
        dependent_plugin = MockPlugin("dependent", dependencies=["base"])

        plugin_manager.register_plugin(base_plugin)
        plugin_manager.register_plugin(dependent_plugin)

        plugin_manager.initialize_plugin("base")
        plugin_manager.enable_plugin("base")
        plugin_manager.initialize_plugin("dependent")
        plugin_manager.enable_plugin("dependent")

        # Disable dependent first
        plugin_manager.disable_plugin("dependent")

        # Now can disable base
        plugin_manager.disable_plugin("base")

        assert base_plugin.status == PluginStatus.DISABLED


class TestPluginManagerEvents:
    """Test cases for plugin events."""

    @pytest.fixture
    def plugin_manager(self):
        """Create PluginManager with event dispatcher."""
        return PluginManager()

    def test_register_emits_event(self, plugin_manager):
        """register_plugin should emit plugin.registered event."""
        events = []

        def listener(event: Event):
            events.append(event.name)

        plugin_manager.event_dispatcher.add_listener("plugin.registered", listener)

        plugin = MockPlugin("test-plugin")
        plugin_manager.register_plugin(plugin)

        assert "plugin.registered" in events

    def test_initialize_emits_event(self, plugin_manager):
        """initialize_plugin should emit plugin.initialized event."""
        events = []

        def listener(event: Event):
            events.append(event.name)

        plugin_manager.event_dispatcher.add_listener("plugin.initialized", listener)

        plugin = MockPlugin("test-plugin")
        plugin_manager.register_plugin(plugin)
        plugin_manager.initialize_plugin("test-plugin")

        assert "plugin.initialized" in events

    def test_enable_emits_event(self, plugin_manager):
        """enable_plugin should emit plugin.enabled event."""
        events = []

        def listener(event: Event):
            events.append(event.name)

        plugin_manager.event_dispatcher.add_listener("plugin.enabled", listener)

        plugin = MockPlugin("test-plugin")
        plugin_manager.register_plugin(plugin)
        plugin_manager.initialize_plugin("test-plugin")
        plugin_manager.enable_plugin("test-plugin")

        assert "plugin.enabled" in events

    def test_disable_emits_event(self, plugin_manager):
        """disable_plugin should emit plugin.disabled event."""
        events = []

        def listener(event: Event):
            events.append(event.name)

        plugin_manager.event_dispatcher.add_listener("plugin.disabled", listener)

        plugin = MockPlugin("test-plugin")
        plugin_manager.register_plugin(plugin)
        plugin_manager.initialize_plugin("test-plugin")
        plugin_manager.enable_plugin("test-plugin")
        plugin_manager.disable_plugin("test-plugin")

        assert "plugin.disabled" in events
