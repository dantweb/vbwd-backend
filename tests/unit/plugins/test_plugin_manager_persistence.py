"""Tests for PluginManager persistence (config_repo integration)."""
import pytest
from unittest.mock import MagicMock
from src.plugins.manager import PluginManager
from src.plugins.base import BasePlugin, PluginMetadata, PluginStatus


class MockPlugin(BasePlugin):
    """Mock plugin for testing."""

    def __init__(self, name: str):
        super().__init__()
        self._name = name

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self._name,
            version="1.0.0",
            author="Test",
            description="Test plugin",
        )


class MockPluginConfig:
    """Mimics PluginConfig model row."""

    def __init__(self, plugin_name, status="enabled"):
        self.plugin_name = plugin_name
        self.status = status


class TestPluginManagerPersistence:
    """Test persistence via config_repo."""

    @pytest.fixture
    def config_repo(self):
        return MagicMock()

    def test_enable_persists_to_repo(self, config_repo):
        """enable_plugin calls config_repo.save with 'enabled'."""
        manager = PluginManager(config_repo=config_repo)
        plugin = MockPlugin("test")
        manager.register_plugin(plugin)
        manager.initialize_plugin("test")

        manager.enable_plugin("test")

        config_repo.save.assert_called_once_with("test", "enabled", plugin._config)

    def test_disable_persists_to_repo(self, config_repo):
        """disable_plugin calls config_repo.save with 'disabled'."""
        manager = PluginManager(config_repo=config_repo)
        plugin = MockPlugin("test")
        manager.register_plugin(plugin)
        manager.initialize_plugin("test")
        manager.enable_plugin("test")
        config_repo.save.reset_mock()

        manager.disable_plugin("test")

        config_repo.save.assert_called_once_with("test", "disabled", plugin._config)

    def test_load_persisted_state_enables_plugins(self, config_repo):
        """load_persisted_state enables plugins that are 'enabled' in DB."""
        config_repo.get_enabled.return_value = [MockPluginConfig("test", "enabled")]

        manager = PluginManager(config_repo=config_repo)
        plugin = MockPlugin("test")
        manager.register_plugin(plugin)
        manager.initialize_plugin("test")

        manager.load_persisted_state()

        assert plugin.status == PluginStatus.ENABLED

    def test_load_persisted_state_skips_unknown_plugins(self, config_repo):
        """load_persisted_state skips plugins not in registry."""
        config_repo.get_enabled.return_value = [MockPluginConfig("unknown", "enabled")]

        manager = PluginManager(config_repo=config_repo)
        # No plugins registered

        # Should not raise
        manager.load_persisted_state()

    def test_works_without_config_repo(self):
        """PluginManager works without config_repo (backward compatible)."""
        manager = PluginManager()  # No config_repo
        plugin = MockPlugin("test")
        manager.register_plugin(plugin)
        manager.initialize_plugin("test")
        manager.enable_plugin("test")

        assert plugin.status == PluginStatus.ENABLED

        manager.disable_plugin("test")
        assert plugin.status == PluginStatus.DISABLED

        # load_persisted_state is a no-op
        manager.load_persisted_state()
