"""Tests for PluginManager.discover() auto-discovery."""
import pytest
from unittest.mock import patch, MagicMock
from src.plugins.manager import PluginManager
from src.plugins.base import BasePlugin, PluginMetadata, PluginStatus


class TestPluginDiscovery:
    """Test plugin auto-discovery from providers package."""

    @pytest.fixture
    def plugin_manager(self):
        return PluginManager()

    def test_discovers_analytics_plugin(self, plugin_manager):
        """discover() finds AnalyticsPlugin from src.plugins.providers."""
        count = plugin_manager.discover("src.plugins.providers")

        plugin = plugin_manager.get_plugin("analytics")
        assert plugin is not None
        assert plugin.status == PluginStatus.INITIALIZED

    def test_discovers_mock_payment_plugin(self, plugin_manager):
        """discover() finds MockPaymentPlugin from src.plugins.providers."""
        count = plugin_manager.discover("src.plugins.providers")

        plugin = plugin_manager.get_plugin("mock_payment")
        assert plugin is not None
        assert plugin.status == PluginStatus.INITIALIZED

    def test_returns_count_of_discovered_plugins(self, plugin_manager):
        """discover() returns the number of newly discovered plugins."""
        count = plugin_manager.discover("src.plugins.providers")

        # At least analytics and mock_payment
        assert count >= 2

    def test_skips_non_plugin_modules(self, plugin_manager):
        """discover() skips modules that don't contain BasePlugin subclasses."""
        # __init__.py has no plugin classes — should not cause errors
        count = plugin_manager.discover("src.plugins.providers")
        assert count >= 2  # Only real plugin modules counted

    def test_skips_abstract_classes(self, plugin_manager):
        """discover() skips abstract classes like PaymentProviderPlugin."""
        plugin_manager.discover("src.plugins.providers")

        # PaymentProviderPlugin is abstract and should not be registered
        all_plugins = plugin_manager.get_all_plugins()
        for p in all_plugins:
            # No plugin should have the raw abstract class name
            assert p.__class__.__name__ != "PaymentProviderPlugin"

    def test_skips_already_registered_plugins(self, plugin_manager):
        """discover() skips plugins already registered."""
        from src.plugins.providers.analytics_plugin import AnalyticsPlugin

        # Pre-register analytics
        pre_plugin = AnalyticsPlugin()
        plugin_manager.register_plugin(pre_plugin)
        plugin_manager.initialize_plugin("analytics")

        count = plugin_manager.discover("src.plugins.providers")

        # analytics should not be double-registered, count should be less
        all_plugins = plugin_manager.get_all_plugins()
        analytics_count = sum(
            1 for p in all_plugins if p.metadata.name == "analytics"
        )
        assert analytics_count == 1

    def test_handles_import_errors_gracefully(self, plugin_manager):
        """discover() handles import errors without crashing."""
        # Non-existent package
        count = plugin_manager.discover("src.plugins.nonexistent")
        assert count == 0

    def test_empty_package_returns_zero(self):
        """discover() returns 0 for a package with no plugins."""
        manager = PluginManager()

        # src.plugins has no direct plugin classes (only subpackages)
        with patch("pkgutil.iter_modules", return_value=[]):
            count = manager.discover("src.plugins.providers")
        assert count == 0

    def test_initializes_discovered_plugins(self, plugin_manager):
        """discover() initializes discovered plugins to INITIALIZED state."""
        plugin_manager.discover("src.plugins.providers")

        for plugin in plugin_manager.get_all_plugins():
            assert plugin.status == PluginStatus.INITIALIZED
