"""Tests for PluginConfigRepository."""
import pytest
from unittest.mock import MagicMock, patch
from src.repositories.plugin_config_repository import PluginConfigRepository
from src.models.plugin_config import PluginConfig


class FakeQuery:
    """Fake query that simulates SQLAlchemy query chain."""

    def __init__(self, results=None):
        self._results = results or []

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._results[0] if self._results else None

    def all(self):
        return self._results


class TestPluginConfigRepository:
    """Test PluginConfigRepository."""

    @pytest.fixture
    def session(self):
        return MagicMock()

    @pytest.fixture
    def repo(self, session):
        return PluginConfigRepository(session)

    def test_get_by_name_found(self, repo, session):
        """get_by_name returns entry when found."""
        entry = PluginConfig(plugin_name="analytics", status="enabled")
        session.query.return_value = FakeQuery([entry])

        result = repo.get_by_name("analytics")
        assert result == entry

    def test_get_by_name_not_found(self, repo, session):
        """get_by_name returns None when not found."""
        session.query.return_value = FakeQuery([])

        result = repo.get_by_name("nonexistent")
        assert result is None

    def test_get_all(self, repo, session):
        """get_all returns all entries."""
        entries = [
            PluginConfig(plugin_name="a", status="enabled"),
            PluginConfig(plugin_name="b", status="disabled"),
        ]
        session.query.return_value = FakeQuery(entries)

        result = repo.get_all()
        assert len(result) == 2

    def test_get_enabled(self, repo, session):
        """get_enabled returns only enabled entries."""
        enabled = PluginConfig(plugin_name="a", status="enabled")
        session.query.return_value = FakeQuery([enabled])

        result = repo.get_enabled()
        assert len(result) == 1
        assert result[0].plugin_name == "a"

    def test_save_creates_new_entry(self, repo, session):
        """save creates entry when not existing."""
        session.query.return_value = FakeQuery([])

        result = repo.save("analytics", "enabled", {"key": "val"})

        session.add.assert_called_once()
        session.commit.assert_called_once()
        added = session.add.call_args[0][0]
        assert added.plugin_name == "analytics"
        assert added.status == "enabled"
        assert added.config == {"key": "val"}

    def test_save_updates_existing_entry(self, repo, session):
        """save updates entry when already existing."""
        existing = PluginConfig(plugin_name="analytics", status="disabled")
        session.query.return_value = FakeQuery([existing])

        repo.save("analytics", "enabled")

        assert existing.status == "enabled"
        session.commit.assert_called_once()

    def test_save_sets_enabled_at(self, repo, session):
        """save sets enabled_at when enabling."""
        session.query.return_value = FakeQuery([])

        repo.save("analytics", "enabled")

        added = session.add.call_args[0][0]
        assert added.enabled_at is not None

    def test_save_sets_disabled_at(self, repo, session):
        """save sets disabled_at when disabling."""
        session.query.return_value = FakeQuery([])

        repo.save("analytics", "disabled")

        added = session.add.call_args[0][0]
        assert added.disabled_at is not None

    def test_delete(self, repo, session):
        """delete removes entry by name."""
        existing = PluginConfig(plugin_name="analytics", status="enabled")
        session.query.return_value = FakeQuery([existing])

        result = repo.delete("analytics")

        assert result is True
        session.delete.assert_called_once_with(existing)
        session.commit.assert_called_once()
