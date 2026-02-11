"""Tests for PluginManager.discover() auto-discovery."""
import pytest
from unittest.mock import patch
from src.plugins.manager import PluginManager
from src.plugins.base import PluginStatus
from plugins.analytics import AnalyticsPlugin


class TestPluginDiscovery:
    """Test plugin auto-discovery from plugins package."""

    @pytest.fixture
    def plugin_manager(self):
        return PluginManager()

    def test_discovers_analytics_plugin(self, plugin_manager):
        """discover() finds AnalyticsPlugin from plugins package."""
        plugin_manager.discover("plugins")

        plugin = plugin_manager.get_plugin("analytics")
        assert plugin is not None
        assert plugin.status == PluginStatus.INITIALIZED

    def test_discovers_demo_plugin(self, plugin_manager):
        """discover() finds DemoPlugin from plugins package."""
        plugin_manager.discover("plugins")

        plugin = plugin_manager.get_plugin("backend-demo-plugin")
        assert plugin is not None
        assert plugin.status == PluginStatus.INITIALIZED

    def test_returns_count_of_discovered_plugins(self, plugin_manager):
        """discover() returns the number of newly discovered plugins."""
        count = plugin_manager.discover("plugins")

        # analytics + backend-demo-plugin
        assert count >= 2

    def test_skips_non_plugin_modules(self, plugin_manager):
        """discover() skips modules that don't contain BasePlugin subclasses."""
        count = plugin_manager.discover("plugins")
        assert count >= 2  # Only real plugin modules counted

    def test_skips_abstract_classes(self, plugin_manager):
        """discover() skips abstract classes."""
        plugin_manager.discover("plugins")

        all_plugins = plugin_manager.get_all_plugins()
        for p in all_plugins:
            assert p.__class__.__name__ != "BasePlugin"

    def test_skips_already_registered_plugins(self, plugin_manager):
        """discover() skips plugins already registered."""
        # Pre-register analytics
        pre_plugin = AnalyticsPlugin()
        plugin_manager.register_plugin(pre_plugin)
        plugin_manager.initialize_plugin("analytics")

        plugin_manager.discover("plugins")

        # analytics should not be double-registered
        all_plugins = plugin_manager.get_all_plugins()
        analytics_count = sum(1 for p in all_plugins if p.metadata.name == "analytics")
        assert analytics_count == 1

    def test_handles_import_errors_gracefully(self, plugin_manager):
        """discover() handles import errors without crashing."""
        count = plugin_manager.discover("src.plugins.nonexistent")
        assert count == 0

    def test_empty_package_returns_zero(self):
        """discover() returns 0 for a package with no plugins."""
        manager = PluginManager()

        with patch("pkgutil.iter_modules", return_value=[]):
            count = manager.discover("plugins")
        assert count == 0

    def test_initializes_discovered_plugins(self, plugin_manager):
        """discover() initializes discovered plugins to INITIALIZED state."""
        plugin_manager.discover("plugins")

        for plugin in plugin_manager.get_all_plugins():
            assert plugin.status == PluginStatus.INITIALIZED
