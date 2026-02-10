"""Tests for PluginConfigStore abstract interface and PluginConfigEntry DTO."""
import pytest
from src.plugins.config_store import PluginConfigStore, PluginConfigEntry


class TestPluginConfigEntry:
    """Test PluginConfigEntry dataclass."""

    def test_create_with_required_fields(self):
        """PluginConfigEntry can be created with required fields."""
        entry = PluginConfigEntry(plugin_name="test", status="enabled")
        assert entry.plugin_name == "test"
        assert entry.status == "enabled"
        assert entry.config == {}

    def test_create_with_config(self):
        """PluginConfigEntry stores config dict."""
        entry = PluginConfigEntry(
            plugin_name="demo", status="disabled", config={"key": "value"}
        )
        assert entry.plugin_name == "demo"
        assert entry.status == "disabled"
        assert entry.config == {"key": "value"}

    def test_default_config_is_empty_dict(self):
        """Default config is an empty dict."""
        entry = PluginConfigEntry(plugin_name="x", status="enabled")
        assert entry.config == {}

    def test_each_instance_has_own_config(self):
        """Each instance gets its own default dict (not shared)."""
        e1 = PluginConfigEntry(plugin_name="a", status="enabled")
        e2 = PluginConfigEntry(plugin_name="b", status="enabled")
        e1.config["key"] = "val"
        assert "key" not in e2.config


class TestPluginConfigStoreInterface:
    """Test PluginConfigStore is abstract and cannot be instantiated."""

    def test_cannot_instantiate_abc(self):
        """PluginConfigStore cannot be instantiated directly."""
        with pytest.raises(TypeError):
            PluginConfigStore()

    def test_subclass_must_implement_all_methods(self):
        """Subclass that doesn't implement all methods cannot be instantiated."""

        class IncompleteStore(PluginConfigStore):
            pass

        with pytest.raises(TypeError):
            IncompleteStore()

    def test_complete_subclass_can_instantiate(self):
        """Subclass implementing all methods can be instantiated."""

        class CompleteStore(PluginConfigStore):
            def get_enabled(self):
                return []

            def save(self, plugin_name, status, config=None):
                pass

            def get_by_name(self, plugin_name):
                return None

            def get_all(self):
                return []

            def get_config(self, plugin_name):
                return {}

            def save_config(self, plugin_name, config):
                pass

        store = CompleteStore()
        assert isinstance(store, PluginConfigStore)
