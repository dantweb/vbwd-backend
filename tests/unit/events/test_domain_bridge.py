"""Unit tests — DomainEventDispatcher bridges to EventBus."""
from unittest.mock import MagicMock

from src.events.bus import EventBus
from src.events.domain import (
    DomainEvent,
    DomainEventDispatcher,
    IEventHandler,
    EventResult,
)


def _make_dispatcher(bus: EventBus) -> DomainEventDispatcher:
    return DomainEventDispatcher(event_bus=bus)


def _make_event(name: str, data: dict = None) -> DomainEvent:
    return DomainEvent(name=name, data=data or {})


class _AlwaysHandle(IEventHandler):
    def can_handle(self, event):
        return True

    def handle(self, event):
        return EventResult.success_result()


class TestDomainBridge:
    def test_emit_publishes_to_bus(self):
        bus = EventBus()
        cb = MagicMock()
        bus.subscribe("sub.activated", cb)

        dispatcher = _make_dispatcher(bus)
        dispatcher.emit(_make_event("sub.activated", {"user_email": "a@b.com"}))

        cb.assert_called_once_with("sub.activated", {"user_email": "a@b.com"})

    def test_emit_publishes_even_when_no_domain_handlers(self):
        """Bus receives event even if no IEventHandler is registered."""
        bus = EventBus()
        cb = MagicMock()
        bus.subscribe("custom.event", cb)

        dispatcher = _make_dispatcher(bus)
        dispatcher.emit(_make_event("custom.event", {"x": 1}))

        cb.assert_called_once_with("custom.event", {"x": 1})

    def test_emit_runs_domain_handlers_first(self):
        """IEventHandler runs; then bus callback runs."""
        call_order = []
        bus = EventBus()

        class OrderHandler(IEventHandler):
            def can_handle(self, event):
                return True

            def handle(self, event):
                call_order.append("domain")
                return EventResult.success_result()

        def bus_cb(_name, _data):
            call_order.append("bus")

        bus.subscribe("ev", bus_cb)
        dispatcher = _make_dispatcher(bus)
        dispatcher.register("ev", OrderHandler())
        dispatcher.emit(_make_event("ev"))

        assert call_order == ["domain", "bus"]

    def test_emit_with_no_bus_does_not_raise(self):
        """Passing event_bus=None disables bridge silently."""
        dispatcher = DomainEventDispatcher(event_bus=None)
        # Just confirm it doesn't raise (lazy import fallback used)
        dispatcher.emit(_make_event("x.y"))

    def test_emit_result_unaffected_by_bus_failure(self):
        """A crashing bus callback doesn't affect EventResult from domain handlers."""
        bus = EventBus()

        def bad_cb(_name, _data):
            raise RuntimeError("bus error")

        bus.subscribe("ev", bad_cb)
        dispatcher = _make_dispatcher(bus)
        dispatcher.register("ev", _AlwaysHandle())

        result = dispatcher.emit(_make_event("ev"))
        assert result.success is True

    def test_bus_none_disables_forwarding(self):
        """No forwarding when bus is explicitly None and lazy import also returns None."""
        dispatcher = DomainEventDispatcher(event_bus=None)
        # Just verify that no AttributeError is raised.
        dispatcher.emit(_make_event("no.bus.event"))
