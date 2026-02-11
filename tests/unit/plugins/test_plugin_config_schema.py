"""Tests for PluginConfigSchemaReader."""
import json
import pytest
from src.plugins.config_schema import PluginConfigSchemaReader


class TestPluginConfigSchemaReader:
    """Test config schema and admin config reading."""

    @pytest.fixture
    def plugins_dir(self, tmp_path):
        """Create a temp plugins directory with a demo plugin."""
        demo_dir = tmp_path / "demoplugin"
        demo_dir.mkdir()

        # config.json
        config_schema = {
            "greeting": {
                "type": "string",
                "default": "Hello!",
                "description": "Greeting message",
            },
            "requireAdmin": {
                "type": "boolean",
                "default": False,
                "description": "Require admin role",
            },
        }
        (demo_dir / "config.json").write_text(json.dumps(config_schema))

        # admin-config.json
        admin_config = {
            "tabs": [
                {
                    "id": "general",
                    "label": "General",
                    "fields": [
                        {"key": "greeting", "label": "Greeting", "component": "input"},
                        {
                            "key": "requireAdmin",
                            "label": "Require Admin",
                            "component": "checkbox",
                        },
                    ],
                }
            ]
        }
        (demo_dir / "admin-config.json").write_text(json.dumps(admin_config))

        # __init__.py with plugin name
        (demo_dir / "__init__.py").write_text(
            'class DemoPlugin:\n    name="backend-demo-plugin"\n'
        )

        return str(tmp_path)

    def test_reads_config_schema_from_plugin_dir(self, plugins_dir):
        """Reads config.json from a plugin directory."""
        reader = PluginConfigSchemaReader([plugins_dir])

        schema = reader.get_config_schema("demoplugin")
        assert "greeting" in schema
        assert schema["greeting"]["type"] == "string"
        assert schema["greeting"]["default"] == "Hello!"

    def test_reads_admin_config_from_plugin_dir(self, plugins_dir):
        """Reads admin-config.json from a plugin directory."""
        reader = PluginConfigSchemaReader([plugins_dir])

        admin = reader.get_admin_config("demoplugin")
        assert "tabs" in admin
        assert len(admin["tabs"]) == 1
        assert admin["tabs"][0]["id"] == "general"
        assert len(admin["tabs"][0]["fields"]) == 2

    def test_returns_empty_when_no_config_file(self, tmp_path):
        """Returns empty dict when config.json doesn't exist."""
        empty_plugin = tmp_path / "emptyplugin"
        empty_plugin.mkdir()

        reader = PluginConfigSchemaReader([str(tmp_path)])

        assert reader.get_config_schema("emptyplugin") == {}
        assert reader.get_admin_config("emptyplugin") == {}

    def test_returns_empty_for_unknown_plugin(self, plugins_dir):
        """Returns empty dict for unknown plugin name."""
        reader = PluginConfigSchemaReader([plugins_dir])

        assert reader.get_config_schema("nonexistent") == {}
        assert reader.get_admin_config("nonexistent") == {}

    def test_searches_multiple_directories(self, tmp_path):
        """Searches across multiple directories."""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        dir2 = tmp_path / "dir2"
        dir2.mkdir()

        # Plugin in dir2
        plugin_dir = dir2 / "myplugin"
        plugin_dir.mkdir()
        (plugin_dir / "config.json").write_text(json.dumps({"key": {"type": "string"}}))

        reader = PluginConfigSchemaReader([str(dir1), str(dir2)])

        schema = reader.get_config_schema("myplugin")
        assert "key" in schema

    def test_finds_plugin_by_init_py_name(self, plugins_dir):
        """Finds plugin directory by matching name in __init__.py."""
        reader = PluginConfigSchemaReader([plugins_dir])

        # 'backend-demo-plugin' maps to 'demoplugin' via __init__.py scan
        schema = reader.get_config_schema("backend-demo-plugin")
        assert "greeting" in schema

    def test_handles_nonexistent_search_dir(self, tmp_path):
        """Handles nonexistent search directories gracefully."""
        reader = PluginConfigSchemaReader([str(tmp_path / "nonexistent")])

        assert reader.get_config_schema("anything") == {}

    def test_handles_malformed_json(self, tmp_path):
        """Handles malformed JSON gracefully."""
        plugin_dir = tmp_path / "badplugin"
        plugin_dir.mkdir()
        (plugin_dir / "config.json").write_text("not json")

        reader = PluginConfigSchemaReader([str(tmp_path)])

        assert reader.get_config_schema("badplugin") == {}
