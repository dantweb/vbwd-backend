"""Unit tests — BasePlugin.register_event_handlers + PluginManager wiring."""
from unittest.mock import MagicMock, patch

from src.plugins.base import BasePlugin, PluginMetadata, PluginStatus
from src.plugins.manager import PluginManager
from src.events.bus import EventBus


# ---------------------------------------------------------------------------
# Minimal plugin fixtures
# ---------------------------------------------------------------------------


class _SimplePlugin(BasePlugin):
    """Plugin that tracks register_event_handlers calls."""

    def __init__(self):
        super().__init__()
        self.registered_bus = None
        self.handler_called_with = []

    @property
    def metadata(self):
        return PluginMetadata(
            name="simple", version="1.0", author="Test", description=""
        )

    def register_event_handlers(self, bus):
        self.registered_bus = bus

        def _handler(name, data):
            self.handler_called_with.append((name, data))

        bus.subscribe("simple.event", _handler)


class _NoHookPlugin(BasePlugin):
    """Plugin that does NOT override register_event_handlers (uses base no-op)."""

    @property
    def metadata(self):
        return PluginMetadata(
            name="nohook", version="1.0", author="Test", description=""
        )


# ---------------------------------------------------------------------------
# BasePlugin default hook
# ---------------------------------------------------------------------------


class TestBasPluginDefaultHook:
    def test_default_register_event_handlers_is_noop(self):
        plugin = _NoHookPlugin()
        bus = MagicMock()
        # Should not raise and should not call anything on bus
        plugin.register_event_handlers(bus)
        bus.subscribe.assert_not_called()


# ---------------------------------------------------------------------------
# PluginManager calls hook after enable
# ---------------------------------------------------------------------------


class TestPluginManagerCallsHook:
    def _make_manager(self, plugin: BasePlugin):
        manager = PluginManager()
        manager.register_plugin(plugin)
        manager.initialize_plugin(plugin.metadata.name)
        return manager

    def test_enable_plugin_calls_register_event_handlers(self):
        plugin = _SimplePlugin()
        manager = self._make_manager(plugin)

        # manager.enable_plugin does `from src.events.bus import event_bus`
        # so patch the module-level singleton that gets imported
        real_bus = EventBus()
        with patch("src.events.bus.event_bus", real_bus):
            manager.enable_plugin("simple")

        assert plugin.registered_bus is not None
        assert plugin.status == PluginStatus.ENABLED

    def test_enabled_plugin_can_receive_events_via_manager(self):
        plugin = _SimplePlugin()
        manager = self._make_manager(plugin)
        real_bus = EventBus()

        with patch("src.events.bus.event_bus", real_bus):
            manager.enable_plugin("simple")

        real_bus.publish("simple.event", {"x": 42})
        assert plugin.handler_called_with == [("simple.event", {"x": 42})]

    def test_hook_failure_does_not_prevent_plugin_enable(self):
        """A crashing register_event_handlers doesn't block enable."""

        class _CrashPlugin(_NoHookPlugin):
            @property
            def metadata(self):
                return PluginMetadata(
                    name="crash", version="1.0", author="T", description=""
                )

            def register_event_handlers(self, bus):
                raise RuntimeError("hook crashed")

        plugin = _CrashPlugin()
        manager = PluginManager()
        manager.register_plugin(plugin)
        manager.initialize_plugin("crash")
        # Should not raise
        manager.enable_plugin("crash")
        assert plugin.status == PluginStatus.ENABLED
