"""Abstract interface for plugin configuration persistence."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PluginConfigEntry:
    """DTO for plugin configuration state."""

    plugin_name: str
    status: str  # "enabled" | "disabled"
    config: Dict = field(default_factory=dict)


class PluginConfigStore(ABC):
    """Abstract store for plugin configuration persistence."""

    @abstractmethod
    def get_enabled(self) -> List[PluginConfigEntry]:
        """Get all enabled plugin config entries."""
        ...

    @abstractmethod
    def save(self, plugin_name: str, status: str, config: Optional[dict] = None) -> None:
        """Save plugin status and optional config."""
        ...

    @abstractmethod
    def get_by_name(self, plugin_name: str) -> Optional[PluginConfigEntry]:
        """Get plugin config by name."""
        ...

    @abstractmethod
    def get_all(self) -> List[PluginConfigEntry]:
        """Get all plugin config entries."""
        ...

    @abstractmethod
    def get_config(self, plugin_name: str) -> dict:
        """Get saved config values for a plugin."""
        ...

    @abstractmethod
    def save_config(self, plugin_name: str, config: dict) -> None:
        """Save config values for a plugin."""
        ...
