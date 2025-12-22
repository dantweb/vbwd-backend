"""Tests for EventDispatcher."""
import pytest
from src.events.dispatcher import EventDispatcher, Event, EventPriority


class TestEventDispatcherBasic:
    """Test cases for basic event dispatcher functionality."""

    @pytest.fixture
    def dispatcher(self):
        """Create EventDispatcher."""
        return EventDispatcher()

    def test_add_and_dispatch_listener(self, dispatcher):
        """add_listener should register and dispatch calls it."""
        called = []

        def listener(event: Event):
            called.append(event.name)

        dispatcher.add_listener("test.event", listener)

        event = Event(name="test.event")
        dispatcher.dispatch(event)

        assert called == ["test.event"]

    def test_dispatch_with_event_data(self, dispatcher):
        """dispatch should pass event data to listeners."""
        received_data = {}

        def listener(event: Event):
            received_data.update(event.data)

        dispatcher.add_listener("test.event", listener)

        event = Event(name="test.event", data={"key": "value"})
        dispatcher.dispatch(event)

        assert received_data == {"key": "value"}

    def test_dispatch_multiple_listeners(self, dispatcher):
        """dispatch should call all registered listeners."""
        called = []

        def listener1(event: Event):
            called.append("listener1")

        def listener2(event: Event):
            called.append("listener2")

        dispatcher.add_listener("test.event", listener1)
        dispatcher.add_listener("test.event", listener2)

        event = Event(name="test.event")
        dispatcher.dispatch(event)

        assert "listener1" in called
        assert "listener2" in called
        assert len(called) == 2

    def test_dispatch_no_listeners(self, dispatcher):
        """dispatch should handle events with no listeners."""
        event = Event(name="test.event")
        result = dispatcher.dispatch(event)

        assert result == event


class TestEventDispatcherPriority:
    """Test cases for event priority handling."""

    @pytest.fixture
    def dispatcher(self):
        """Create EventDispatcher."""
        return EventDispatcher()

    def test_dispatch_with_priority_order(self, dispatcher):
        """dispatch should call listeners in priority order."""
        order = []

        def listener_low(event: Event):
            order.append("low")

        def listener_high(event: Event):
            order.append("high")

        def listener_normal(event: Event):
            order.append("normal")

        dispatcher.add_listener("test.event", listener_low, EventPriority.LOW)
        dispatcher.add_listener("test.event", listener_high, EventPriority.HIGH)
        dispatcher.add_listener("test.event", listener_normal, EventPriority.NORMAL)

        event = Event(name="test.event")
        dispatcher.dispatch(event)

        assert order == ["high", "normal", "low"]

    def test_dispatch_highest_priority_first(self, dispatcher):
        """dispatch should call HIGHEST priority before all others."""
        order = []

        def listener_highest(event: Event):
            order.append("highest")

        def listener_lowest(event: Event):
            order.append("lowest")

        dispatcher.add_listener("test.event", listener_lowest, EventPriority.LOWEST)
        dispatcher.add_listener("test.event", listener_highest, EventPriority.HIGHEST)

        event = Event(name="test.event")
        dispatcher.dispatch(event)

        assert order == ["highest", "lowest"]


class TestEventDispatcherPropagation:
    """Test cases for event propagation."""

    @pytest.fixture
    def dispatcher(self):
        """Create EventDispatcher."""
        return EventDispatcher()

    def test_stop_propagation(self, dispatcher):
        """stop_propagation should prevent remaining listeners."""
        called = []

        def listener1(event: Event):
            called.append("listener1")
            event.stop_propagation()

        def listener2(event: Event):
            called.append("listener2")

        dispatcher.add_listener("test.event", listener1)
        dispatcher.add_listener("test.event", listener2)

        event = Event(name="test.event")
        dispatcher.dispatch(event)

        assert called == ["listener1"]

    def test_stop_propagation_respects_priority(self, dispatcher):
        """stop_propagation should work with priority ordering."""
        called = []

        def listener_high(event: Event):
            called.append("high")
            event.stop_propagation()

        def listener_low(event: Event):
            called.append("low")

        dispatcher.add_listener("test.event", listener_low, EventPriority.LOW)
        dispatcher.add_listener("test.event", listener_high, EventPriority.HIGH)

        event = Event(name="test.event")
        dispatcher.dispatch(event)

        assert called == ["high"]


class TestEventDispatcherListenerManagement:
    """Test cases for listener management."""

    @pytest.fixture
    def dispatcher(self):
        """Create EventDispatcher."""
        return EventDispatcher()

    def test_remove_listener(self, dispatcher):
        """remove_listener should unregister listener."""
        called = []

        def listener(event: Event):
            called.append(event.name)

        dispatcher.add_listener("test.event", listener)
        dispatcher.remove_listener("test.event", listener)

        event = Event(name="test.event")
        dispatcher.dispatch(event)

        assert called == []

    def test_remove_nonexistent_listener(self, dispatcher):
        """remove_listener should handle nonexistent listener."""
        def listener(event: Event):
            pass

        # Should not raise
        dispatcher.remove_listener("test.event", listener)

    def test_has_listeners(self, dispatcher):
        """has_listeners should return True if listeners exist."""
        def listener(event: Event):
            pass

        assert dispatcher.has_listeners("test.event") is False

        dispatcher.add_listener("test.event", listener)
        assert dispatcher.has_listeners("test.event") is True

    def test_get_listeners(self, dispatcher):
        """get_listeners should return all listeners for event."""
        def listener1(event: Event):
            pass

        def listener2(event: Event):
            pass

        dispatcher.add_listener("test.event", listener1)
        dispatcher.add_listener("test.event", listener2)

        listeners = dispatcher.get_listeners("test.event")

        assert len(listeners) == 2


class TestEventDispatcherErrorHandling:
    """Test cases for error handling."""

    @pytest.fixture
    def dispatcher(self):
        """Create EventDispatcher."""
        return EventDispatcher()

    def test_listener_exception_does_not_stop_others(self, dispatcher):
        """Exception in one listener should not prevent others from running."""
        called = []

        def listener_error(event: Event):
            raise ValueError("Test error")

        def listener_ok(event: Event):
            called.append("ok")

        dispatcher.add_listener("test.event", listener_error)
        dispatcher.add_listener("test.event", listener_ok)

        event = Event(name="test.event")
        dispatcher.dispatch(event)

        assert called == ["ok"]
