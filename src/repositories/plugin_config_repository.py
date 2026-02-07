"""Repository for plugin configuration persistence."""
from datetime import datetime
from typing import Optional, List
from src.models.plugin_config import PluginConfig


class PluginConfigRepository:
    """CRUD repository for PluginConfig entries."""

    def __init__(self, session):
        self._session = session

    def get_by_name(self, plugin_name: str) -> Optional[PluginConfig]:
        """Get plugin config by name."""
        return (
            self._session.query(PluginConfig)
            .filter(PluginConfig.plugin_name == plugin_name)
            .first()
        )

    def get_all(self) -> List[PluginConfig]:
        """Get all plugin configs."""
        return self._session.query(PluginConfig).all()

    def get_enabled(self) -> List[PluginConfig]:
        """Get all enabled plugin configs."""
        return (
            self._session.query(PluginConfig)
            .filter(PluginConfig.status == "enabled")
            .all()
        )

    def save(self, plugin_name: str, status: str, config: Optional[dict] = None) -> PluginConfig:
        """Create or update plugin config entry."""
        existing = self.get_by_name(plugin_name)
        now = datetime.utcnow()

        if existing:
            existing.status = status
            existing.updated_at = now
            if config is not None:
                existing.config = config
            if status == "enabled":
                existing.enabled_at = now
            elif status == "disabled":
                existing.disabled_at = now
            self._session.commit()
            return existing

        entry = PluginConfig(
            plugin_name=plugin_name,
            status=status,
            config=config or {},
            created_at=now,
            updated_at=now,
        )
        if status == "enabled":
            entry.enabled_at = now
        elif status == "disabled":
            entry.disabled_at = now

        self._session.add(entry)
        self._session.commit()
        return entry

    def delete(self, plugin_name: str) -> bool:
        """Delete plugin config by name."""
        existing = self.get_by_name(plugin_name)
        if existing:
            self._session.delete(existing)
            self._session.commit()
            return True
        return False
