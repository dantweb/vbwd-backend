"""Unit tests for EventBus."""
from unittest.mock import MagicMock

from vbwd.events.bus import EventBus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bus() -> EventBus:
    return EventBus()


# ---------------------------------------------------------------------------
# subscribe / has_subscribers
# ---------------------------------------------------------------------------


class TestSubscribe:
    def test_subscribe_registers_callback(self):
        bus = _bus()
        cb = MagicMock()
        bus.subscribe("test.event", cb)
        assert bus.has_subscribers("test.event")

    def test_no_subscribers_initially(self):
        bus = _bus()
        assert not bus.has_subscribers("test.event")

    def test_duplicate_subscribe_is_idempotent(self):
        bus = _bus()
        cb = MagicMock()
        bus.subscribe("x", cb)
        bus.subscribe("x", cb)
        bus.publish("x", {})
        cb.assert_called_once()

    def test_multiple_different_callbacks(self):
        bus = _bus()
        cb1 = MagicMock()
        cb2 = MagicMock()
        bus.subscribe("ev", cb1)
        bus.subscribe("ev", cb2)
        bus.publish("ev", {"k": 1})
        cb1.assert_called_once_with("ev", {"k": 1})
        cb2.assert_called_once_with("ev", {"k": 1})


# ---------------------------------------------------------------------------
# unsubscribe
# ---------------------------------------------------------------------------


class TestUnsubscribe:
    def test_unsubscribe_removes_callback(self):
        bus = _bus()
        cb = MagicMock()
        bus.subscribe("ev", cb)
        bus.unsubscribe("ev", cb)
        assert not bus.has_subscribers("ev")

    def test_unsubscribe_unknown_is_noop(self):
        bus = _bus()
        cb = MagicMock()
        # Should not raise
        bus.unsubscribe("never.subscribed", cb)

    def test_unsubscribe_only_removes_matching_callback(self):
        bus = _bus()
        cb1 = MagicMock()
        cb2 = MagicMock()
        bus.subscribe("ev", cb1)
        bus.subscribe("ev", cb2)
        bus.unsubscribe("ev", cb1)
        bus.publish("ev", {})
        cb1.assert_not_called()
        cb2.assert_called_once()


# ---------------------------------------------------------------------------
# publish
# ---------------------------------------------------------------------------


class TestPublish:
    def test_publish_calls_subscribers_with_name_and_data(self):
        bus = _bus()
        cb = MagicMock()
        bus.subscribe("order.placed", cb)
        bus.publish("order.placed", {"order_id": "42"})
        cb.assert_called_once_with("order.placed", {"order_id": "42"})

    def test_publish_with_no_subscribers_is_noop(self):
        bus = _bus()
        # Should not raise
        bus.publish("silent.event", {"x": 1})

    def test_publish_different_event_does_not_trigger_other_subscribers(self):
        bus = _bus()
        cb = MagicMock()
        bus.subscribe("a.event", cb)
        bus.publish("b.event", {})
        cb.assert_not_called()

    def test_failing_subscriber_does_not_stop_remaining_subscribers(self):
        bus = _bus()

        def bad_cb(_name, _data):
            raise RuntimeError("boom")

        good_cb = MagicMock()
        bus.subscribe("ev", bad_cb)
        bus.subscribe("ev", good_cb)
        # Should not raise
        bus.publish("ev", {})
        good_cb.assert_called_once()

    def test_publish_passes_empty_dict_when_no_data(self):
        bus = _bus()
        cb = MagicMock()
        bus.subscribe("ev", cb)
        bus.publish("ev", {})
        cb.assert_called_once_with("ev", {})


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_event_bus_singleton_importable(self):
        from vbwd.events.bus import event_bus

        assert isinstance(event_bus, EventBus)

    def test_event_bus_importable_from_events_init(self):
        from vbwd.events import event_bus

        assert isinstance(event_bus, EventBus)
