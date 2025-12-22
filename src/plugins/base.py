"""Plugin base classes and interfaces."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass


class PluginStatus(Enum):
    """Plugin status."""
    DISCOVERED = "discovered"
    REGISTERED = "registered"
    INITIALIZED = "initialized"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginMetadata:
    """Plugin metadata."""
    name: str
    version: str
    author: str
    description: str
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class BasePlugin(ABC):
    """
    Base class for all plugins.

    Plugins must inherit from this class and implement required methods.
    """

    def __init__(self):
        self._status = PluginStatus.DISCOVERED
        self._config: Dict[str, Any] = {}

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass

    @property
    def status(self) -> PluginStatus:
        """Get plugin status."""
        return self._status

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize plugin with configuration.

        Args:
            config: Optional configuration dictionary
        """
        if config:
            self._config = config
        self._status = PluginStatus.INITIALIZED

    def enable(self) -> None:
        """Enable the plugin."""
        if self._status != PluginStatus.INITIALIZED:
            raise ValueError(f"Cannot enable plugin in {self._status.value} state")
        self.on_enable()
        self._status = PluginStatus.ENABLED

    def disable(self) -> None:
        """Disable the plugin."""
        if self._status != PluginStatus.ENABLED:
            raise ValueError(f"Cannot disable plugin in {self._status.value} state")
        self.on_disable()
        self._status = PluginStatus.DISABLED

    def on_enable(self) -> None:
        """Hook called when plugin is enabled."""
        pass

    def on_disable(self) -> None:
        """Hook called when plugin is disabled."""
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value
