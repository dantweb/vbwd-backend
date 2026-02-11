"""JSON file-based plugin configuration store."""
import json
import logging
import os
import tempfile
from typing import List, Optional

from src.plugins.config_store import PluginConfigStore, PluginConfigEntry

logger = logging.getLogger(__name__)


class JsonFilePluginConfigStore(PluginConfigStore):
    """
    Persists plugin state to JSON files on disk.

    Uses two files:
      - plugins_dir/plugins.json  — plugin registry (name → {enabled, version, ...})
      - plugins_dir/config.json   — saved config values per plugin
    """

    def __init__(self, plugins_dir: str):
        self._plugins_dir = plugins_dir
        self._plugins_path = os.path.join(plugins_dir, "plugins.json")
        self._config_path = os.path.join(plugins_dir, "config.json")

    def _read_plugins(self) -> dict:
        """Read plugins.json, returning the 'plugins' dict."""
        try:
            with open(self._plugins_path, "r") as f:
                data = json.load(f)
            return data.get("plugins", {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_plugins(self, plugins: dict) -> None:
        """Atomically write plugins.json."""
        os.makedirs(self._plugins_dir, exist_ok=True)
        data = {"plugins": plugins}
        fd, tmp_path = tempfile.mkstemp(dir=self._plugins_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f, indent=2)
            os.chmod(tmp_path, 0o666)
            os.replace(tmp_path, self._plugins_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _read_config(self) -> dict:
        """Read config.json."""
        try:
            with open(self._config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_config(self, config: dict) -> None:
        """Atomically write config.json."""
        os.makedirs(self._plugins_dir, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self._plugins_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(config, f, indent=2)
            os.chmod(tmp_path, 0o666)
            os.replace(tmp_path, self._config_path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def get_enabled(self) -> List[PluginConfigEntry]:
        """Get all enabled plugin config entries."""
        plugins = self._read_plugins()
        configs = self._read_config()
        result = []
        for name, info in plugins.items():
            if info.get("enabled"):
                result.append(
                    PluginConfigEntry(
                        plugin_name=name,
                        status="enabled",
                        config=configs.get(name, {}),
                    )
                )
        return result

    def save(
        self, plugin_name: str, status: str, config: Optional[dict] = None
    ) -> None:
        """Save plugin status and optional config."""
        plugins = self._read_plugins()

        if plugin_name not in plugins:
            plugins[plugin_name] = {
                "enabled": False,
                "version": "1.0.0",
                "installedAt": "",
                "source": "local",
            }

        plugins[plugin_name]["enabled"] = status == "enabled"
        self._write_plugins(plugins)

        if config is not None:
            configs = self._read_config()
            configs[plugin_name] = config
            self._write_config(configs)

    def get_by_name(self, plugin_name: str) -> Optional[PluginConfigEntry]:
        """Get plugin config by name."""
        plugins = self._read_plugins()
        info = plugins.get(plugin_name)
        if not info:
            return None
        configs = self._read_config()
        return PluginConfigEntry(
            plugin_name=plugin_name,
            status="enabled" if info.get("enabled") else "disabled",
            config=configs.get(plugin_name, {}),
        )

    def get_all(self) -> List[PluginConfigEntry]:
        """Get all plugin config entries."""
        plugins = self._read_plugins()
        configs = self._read_config()
        return [
            PluginConfigEntry(
                plugin_name=name,
                status="enabled" if info.get("enabled") else "disabled",
                config=configs.get(name, {}),
            )
            for name, info in plugins.items()
        ]

    def get_config(self, plugin_name: str) -> dict:
        """Get saved config values for a plugin."""
        configs = self._read_config()
        return configs.get(plugin_name, {})

    def save_config(self, plugin_name: str, config: dict) -> None:
        """Save config values for a plugin."""
        configs = self._read_config()
        configs[plugin_name] = config
        self._write_config(configs)
