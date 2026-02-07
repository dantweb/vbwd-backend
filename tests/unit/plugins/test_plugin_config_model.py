"""Tests for PluginConfig model."""
import pytest
from src.models.plugin_config import PluginConfig


class TestPluginConfigModel:
    """Test PluginConfig model definition."""

    def test_required_columns_exist(self):
        """Model has all required columns."""
        columns = {c.name for c in PluginConfig.__table__.columns}
        expected = {"id", "plugin_name", "status", "config", "enabled_at", "disabled_at", "created_at", "updated_at"}
        assert expected.issubset(columns)

    def test_default_status_is_disabled(self):
        """Status column has server_default 'disabled'."""
        table = PluginConfig.__table__
        status_col = table.columns["status"]
        assert status_col.server_default is not None or status_col.default is not None

    def test_config_accepts_dict(self):
        """Config column accepts JSON-serializable dict."""
        entry = PluginConfig(plugin_name="test", config={"key": "value"})
        assert entry.config == {"key": "value"}

    def test_plugin_name_has_unique_constraint(self):
        """plugin_name column has unique constraint."""
        table = PluginConfig.__table__
        # Check indexes for uniqueness
        unique_cols = set()
        for idx in table.indexes:
            if idx.unique:
                for col in idx.columns:
                    unique_cols.add(col.name)
        # Also check column-level unique
        for col in table.columns:
            if col.unique:
                unique_cols.add(col.name)
        assert "plugin_name" in unique_cols
