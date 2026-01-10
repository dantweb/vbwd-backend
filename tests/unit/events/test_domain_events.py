"""Tests for domain event system."""
import pytest
from src.events.domain import (
    DomainEvent,
    EventResult,
    IEventHandler,
    DomainEventDispatcher,
)


class TestEventResult:
    """Test cases for EventResult."""

    def test_success_result_creates_successful(self):
        """success_result should create result with success=True."""
        result = EventResult.success_result({"user_id": "test"})

        assert result.success is True
        assert result.data == {"user_id": "test"}
        assert result.error is None

    def test_error_result_creates_failed(self):
        """error_result should create result with success=False."""
        result = EventResult.error_result("Something went wrong")

        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.error_type == "handler_error"

    def test_no_handler_creates_no_handler_result(self):
        """no_handler should create result with no_handler error type."""
        result = EventResult.no_handler()

        assert result.success is False
        assert result.error_type == "no_handler"

    def test_combine_merges_multiple_successes(self):
        """combine should merge multiple successful results."""
        result1 = EventResult.success_result({"count": 1})
        result2 = EventResult.success_result({"count": 2})

        combined = EventResult.combine([result1, result2])

        assert combined.success is True
        assert isinstance(combined.data, list)
        assert len(combined.data) == 2

    def test_combine_fails_if_any_result_fails(self):
        """combine should fail if any result fails."""
        result1 = EventResult.success_result({"count": 1})
        result2 = EventResult.error_result("Failed")

        combined = EventResult.combine([result1, result2])

        assert combined.success is False
        assert "Failed" in combined.error

    def test_to_dict_serializes_result(self):
        """to_dict should serialize result to dictionary."""
        result = EventResult.success_result({"key": "value"})

        result_dict = result.to_dict()

        assert result_dict["success"] is True
        assert result_dict["data"] == {"key": "value"}
        assert result_dict["error"] is None


class MockEventHandler(IEventHandler):
    """Mock event handler for testing."""

    def __init__(self, can_handle_result=True, handle_result=None):
        self.can_handle_result = can_handle_result
        self.handle_result = handle_result or EventResult.success_result()
        self.handled_events = []

    def can_handle(self, event: DomainEvent) -> bool:
        return self.can_handle_result

    def handle(self, event: DomainEvent) -> EventResult:
        self.handled_events.append(event)
        return self.handle_result


class TestDomainEventDispatcher:
    """Test cases for DomainEventDispatcher."""

    @pytest.fixture
    def dispatcher(self):
        """Create DomainEventDispatcher."""
        return DomainEventDispatcher()

    def test_register_adds_handler(self, dispatcher):
        """register should add handler for event type."""
        handler = MockEventHandler()

        dispatcher.register("test.event", handler)

        assert dispatcher.has_handler("test.event")

    def test_has_handler_returns_false_for_unregistered(self, dispatcher):
        """has_handler should return False for unregistered events."""
        assert dispatcher.has_handler("nonexistent.event") is False

    def test_emit_calls_handler(self, dispatcher):
        """emit should call registered handler."""
        handler = MockEventHandler()
        dispatcher.register("test.event", handler)

        event = DomainEvent(name="test.event")
        result = dispatcher.emit(event)

        assert result.success is True
        assert len(handler.handled_events) == 1
        assert handler.handled_events[0] == event

    def test_emit_calls_multiple_handlers(self, dispatcher):
        """emit should call all registered handlers for an event."""
        handler1 = MockEventHandler()
        handler2 = MockEventHandler()

        dispatcher.register("test.event", handler1)
        dispatcher.register("test.event", handler2)

        event = DomainEvent(name="test.event")
        result = dispatcher.emit(event)

        assert result.success is True
        assert len(handler1.handled_events) == 1
        assert len(handler2.handled_events) == 1

    def test_emit_returns_no_handler_if_no_handlers(self, dispatcher):
        """emit should return no_handler result if no handlers registered."""
        event = DomainEvent(name="unknown.event")

        result = dispatcher.emit(event)

        assert result.success is False
        assert result.error_type == "no_handler"

    def test_emit_handles_handler_exceptions(self, dispatcher):
        """emit should catch and return error for handler exceptions."""
        handler = MockEventHandler()
        handler.handle_result = None  # Will cause exception

        def failing_handle(event):
            raise ValueError("Handler error")

        handler.handle = failing_handle

        dispatcher.register("test.event", handler)

        event = DomainEvent(name="test.event")
        result = dispatcher.emit(event)

        assert result.success is False
        assert result.error_type == "handler_exception"

    def test_emit_skips_handlers_that_cannot_handle(self, dispatcher):
        """emit should skip handlers where can_handle returns False."""
        handler = MockEventHandler(can_handle_result=False)
        dispatcher.register("test.event", handler)

        event = DomainEvent(name="test.event")
        result = dispatcher.emit(event)

        assert len(handler.handled_events) == 0
        # Should return no_handler since no handler could handle it
        assert result.success is False

    def test_emit_combines_results_from_multiple_handlers(self, dispatcher):
        """emit should combine results from all handlers."""
        handler1 = MockEventHandler(handle_result=EventResult.success_result({"id": 1}))
        handler2 = MockEventHandler(handle_result=EventResult.success_result({"id": 2}))

        dispatcher.register("test.event", handler1)
        dispatcher.register("test.event", handler2)

        event = DomainEvent(name="test.event")
        result = dispatcher.emit(event)

        assert result.success is True
        assert isinstance(result.data, list)
        assert len(result.data) == 2
