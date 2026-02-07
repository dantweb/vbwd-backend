"""Tests for plugin blueprint registration."""
import pytest
from unittest.mock import MagicMock
from src.plugins.base import BasePlugin, PluginMetadata
from src.plugins.manager import PluginManager
from src.plugins.providers.analytics_plugin import AnalyticsPlugin


class MockPluginNoBlueprint(BasePlugin):
    """Plugin without blueprint."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="no-blueprint",
            version="1.0.0",
            author="Test",
            description="Plugin with no blueprint",
        )


class TestBasePluginBlueprint:
    """Test base plugin blueprint defaults."""

    def test_get_blueprint_returns_none_by_default(self):
        """Base plugin get_blueprint() returns None."""
        plugin = MockPluginNoBlueprint()
        assert plugin.get_blueprint() is None

    def test_get_url_prefix_returns_none_by_default(self):
        """Base plugin get_url_prefix() returns None."""
        plugin = MockPluginNoBlueprint()
        assert plugin.get_url_prefix() is None


class TestAnalyticsPluginBlueprint:
    """Test analytics plugin blueprint."""

    def test_analytics_returns_blueprint(self):
        """Analytics plugin returns its blueprint."""
        plugin = AnalyticsPlugin()
        bp = plugin.get_blueprint()
        assert bp is not None
        assert bp.name == "analytics_plugin"

    def test_analytics_returns_url_prefix(self):
        """Analytics plugin returns URL prefix."""
        plugin = AnalyticsPlugin()
        prefix = plugin.get_url_prefix()
        assert prefix == "/api/v1/plugins/analytics"


class TestManagerGetPluginBlueprints:
    """Test PluginManager.get_plugin_blueprints()."""

    @pytest.fixture
    def plugin_manager(self):
        return PluginManager()

    def test_collects_blueprints_from_enabled_plugins(self, plugin_manager):
        """get_plugin_blueprints returns blueprints from enabled plugins."""
        plugin = AnalyticsPlugin()
        plugin_manager.register_plugin(plugin)
        plugin_manager.initialize_plugin("analytics")
        plugin_manager.enable_plugin("analytics")

        blueprints = plugin_manager.get_plugin_blueprints()
        assert len(blueprints) == 1
        bp, prefix = blueprints[0]
        assert bp.name == "analytics_plugin"
        assert prefix == "/api/v1/plugins/analytics"

    def test_skips_plugins_without_blueprint(self, plugin_manager):
        """get_plugin_blueprints skips plugins that return None."""
        plugin = MockPluginNoBlueprint()
        plugin_manager.register_plugin(plugin)
        plugin_manager.initialize_plugin("no-blueprint")
        plugin_manager.enable_plugin("no-blueprint")

        blueprints = plugin_manager.get_plugin_blueprints()
        assert len(blueprints) == 0

    def test_skips_disabled_plugins(self, plugin_manager):
        """get_plugin_blueprints only includes enabled plugins."""
        plugin = AnalyticsPlugin()
        plugin_manager.register_plugin(plugin)
        plugin_manager.initialize_plugin("analytics")
        # Not enabled

        blueprints = plugin_manager.get_plugin_blueprints()
        assert len(blueprints) == 0

    def test_empty_when_no_plugins(self, plugin_manager):
        """get_plugin_blueprints returns empty list when no plugins."""
        blueprints = plugin_manager.get_plugin_blueprints()
        assert blueprints == []
