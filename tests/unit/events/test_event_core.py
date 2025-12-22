"""Tests for event system core components (Sprint 13)."""
import pytest
from typing import Dict, Any
from unittest.mock import Mock, MagicMock


class TestEventInterface:
    """Tests for EventInterface protocol."""

    def test_event_interface_has_name(self):
        """EventInterface requires name property."""
        from src.events.core.interfaces import EventInterface
        from src.events.core.base import Event

        event = Event(name='test.event')
        # Should satisfy EventInterface protocol
        assert hasattr(event, 'name')
        assert event.name == 'test.event'

    def test_event_interface_has_data(self):
        """EventInterface requires data property."""
        from src.events.core.base import Event

        event = Event(name='test.event', data={'key': 'value'})
        assert hasattr(event, 'data')
        assert event.data == {'key': 'value'}

    def test_event_interface_has_stop_propagation(self):
        """EventInterface requires stop_propagation method."""
        from src.events.core.base import Event

        event = Event(name='test.event')
        assert hasattr(event, 'stop_propagation')
        assert callable(event.stop_propagation)

    def test_event_interface_has_is_propagation_stopped(self):
        """EventInterface requires is_propagation_stopped method."""
        from src.events.core.base import Event

        event = Event(name='test.event')
        assert hasattr(event, 'is_propagation_stopped')
        assert callable(event.is_propagation_stopped)
        assert event.is_propagation_stopped() is False

    def test_event_stop_propagation_works(self):
        """stop_propagation sets propagation stopped flag."""
        from src.events.core.base import Event

        event = Event(name='test.event')
        assert event.is_propagation_stopped() is False
        event.stop_propagation()
        assert event.is_propagation_stopped() is True


class TestEventContext:
    """Tests for EventContext request-scoped cache."""

    def test_context_stores_data(self):
        """Context stores data for current request."""
        from src.events.core.context import EventContext

        ctx = EventContext()
        ctx.set('user_id', '123')
        assert ctx.get('user_id') == '123'

    def test_context_get_returns_none_for_missing(self):
        """get() returns None for missing keys."""
        from src.events.core.context import EventContext

        ctx = EventContext()
        assert ctx.get('nonexistent') is None

    def test_context_get_returns_default(self):
        """get() returns default for missing keys."""
        from src.events.core.context import EventContext

        ctx = EventContext()
        assert ctx.get('nonexistent', 'default') == 'default'

    def test_context_get_or_compute_caches(self):
        """get_or_compute only calls factory once."""
        from src.events.core.context import EventContext

        ctx = EventContext()
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return 'computed_value'

        # First call - factory invoked
        result1 = ctx.get_or_compute('key', factory)
        assert result1 == 'computed_value'
        assert call_count == 1

        # Second call - cached
        result2 = ctx.get_or_compute('key', factory)
        assert result2 == 'computed_value'
        assert call_count == 1  # Factory not called again

    def test_context_clear_removes_all(self):
        """clear() removes all cached data."""
        from src.events.core.context import EventContext

        ctx = EventContext()
        ctx.set('key1', 'value1')
        ctx.set('key2', 'value2')

        ctx.clear()

        assert ctx.get('key1') is None
        assert ctx.get('key2') is None

    def test_context_has_key(self):
        """has() checks if key exists."""
        from src.events.core.context import EventContext

        ctx = EventContext()
        assert ctx.has('key') is False
        ctx.set('key', 'value')
        assert ctx.has('key') is True

    def test_context_delete_key(self):
        """delete() removes specific key."""
        from src.events.core.context import EventContext

        ctx = EventContext()
        ctx.set('key1', 'value1')
        ctx.set('key2', 'value2')

        ctx.delete('key1')

        assert ctx.get('key1') is None
        assert ctx.get('key2') == 'value2'


class TestHandlerPriority:
    """Tests for HandlerPriority constants."""

    def test_highest_is_100(self):
        """HIGHEST priority is 100."""
        from src.events.core.handler import HandlerPriority

        assert HandlerPriority.HIGHEST == 100

    def test_high_is_75(self):
        """HIGH priority is 75."""
        from src.events.core.handler import HandlerPriority

        assert HandlerPriority.HIGH == 75

    def test_normal_is_50(self):
        """NORMAL priority is 50."""
        from src.events.core.handler import HandlerPriority

        assert HandlerPriority.NORMAL == 50

    def test_low_is_25(self):
        """LOW priority is 25."""
        from src.events.core.handler import HandlerPriority

        assert HandlerPriority.LOW == 25

    def test_lowest_is_0(self):
        """LOWEST priority is 0."""
        from src.events.core.handler import HandlerPriority

        assert HandlerPriority.LOWEST == 0

    def test_priority_ordering(self):
        """HIGHEST > HIGH > NORMAL > LOW > LOWEST."""
        from src.events.core.handler import HandlerPriority

        assert HandlerPriority.HIGHEST > HandlerPriority.HIGH
        assert HandlerPriority.HIGH > HandlerPriority.NORMAL
        assert HandlerPriority.NORMAL > HandlerPriority.LOW
        assert HandlerPriority.LOW > HandlerPriority.LOWEST


class TestIEventHandler:
    """Tests for IEventHandler interface."""

    def test_handler_has_get_handled_event_class(self):
        """Handler must declare which event class it handles."""
        from src.events.core.handler import IEventHandler

        assert hasattr(IEventHandler, 'get_handled_event_class')

    def test_handler_has_get_priority(self):
        """Handler returns priority (default NORMAL)."""
        from src.events.core.handler import IEventHandler, HandlerPriority
        from src.events.core.base_handler import AbstractHandler
        from src.events.core.base import Event
        from src.events.domain import EventResult

        class TestHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                return EventResult.success_result()

        handler = TestHandler()
        assert handler.get_priority() == HandlerPriority.NORMAL

    def test_handler_has_can_handle(self):
        """Handler checks if it can handle specific event."""
        from src.events.core.handler import IEventHandler

        assert hasattr(IEventHandler, 'can_handle')

    def test_handler_has_handle(self):
        """Handler processes event and returns result."""
        from src.events.core.handler import IEventHandler

        assert hasattr(IEventHandler, 'handle')

    def test_concrete_handler_implements_interface(self):
        """Concrete handler implements IEventHandler interface."""
        from src.events.core.handler import IEventHandler, HandlerPriority
        from src.events.core.base_handler import AbstractHandler
        from src.events.core.base import Event
        from src.events.domain import EventResult

        class ConcreteHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'user.created'

            @staticmethod
            def get_priority() -> int:
                return HandlerPriority.HIGH

            def can_handle(self, event) -> bool:
                return event.name == 'user.created'

            def handle(self, event) -> EventResult:
                return EventResult.success_result({'handled': True})

        handler = ConcreteHandler()
        assert isinstance(handler, IEventHandler)
        assert handler.get_handled_event_class() == 'user.created'
        assert handler.get_priority() == HandlerPriority.HIGH


class TestAbstractHandler:
    """Tests for AbstractHandler base class."""

    def test_abstract_handler_default_priority(self):
        """Default priority is NORMAL."""
        from src.events.core.handler import HandlerPriority
        from src.events.core.base_handler import AbstractHandler
        from src.events.domain import EventResult

        class TestHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                return EventResult.success_result()

        handler = TestHandler()
        assert handler.get_priority() == HandlerPriority.NORMAL

    def test_abstract_handler_provides_emit(self):
        """AbstractHandler provides emit() for event chaining."""
        from src.events.core.base_handler import AbstractHandler
        from src.events.domain import EventResult

        class TestHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                return EventResult.success_result()

        handler = TestHandler()
        assert hasattr(handler, 'emit')
        assert callable(handler.emit)

    def test_abstract_handler_emit_without_dispatcher(self):
        """emit() returns no_handler when no dispatcher set."""
        from src.events.core.base_handler import AbstractHandler
        from src.events.core.base import Event
        from src.events.domain import EventResult

        class TestHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                return EventResult.success_result()

        handler = TestHandler()  # No dispatcher
        event = Event(name='other.event')
        result = handler.emit(event)

        assert result.success is False
        assert result.error_type == 'no_handler'

    def test_abstract_handler_emit_uses_dispatcher(self):
        """emit() delegates to injected dispatcher."""
        from src.events.core.base_handler import AbstractHandler
        from src.events.core.base import Event
        from src.events.domain import EventResult

        mock_dispatcher = Mock()
        mock_dispatcher.dispatch.return_value = EventResult.success_result({'dispatched': True})

        class TestHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                return EventResult.success_result()

        handler = TestHandler(dispatcher=mock_dispatcher)
        event = Event(name='other.event')
        result = handler.emit(event)

        mock_dispatcher.dispatch.assert_called_once_with(event)
        assert result.success is True
        assert result.data == {'dispatched': True}

    def test_abstract_handler_with_context(self):
        """AbstractHandler can use EventContext."""
        from src.events.core.base_handler import AbstractHandler
        from src.events.core.context import EventContext
        from src.events.domain import EventResult

        ctx = EventContext()
        ctx.set('request_id', 'req-123')

        class TestHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                return EventResult.success_result()

        handler = TestHandler(context=ctx)
        assert handler.context is not None
        assert handler.context.get('request_id') == 'req-123'


class TestEnhancedEventDispatcher:
    """Tests for enhanced EventDispatcher with priority support."""

    def test_dispatcher_register_handler(self):
        """Register handler with dispatcher."""
        from src.events.core.dispatcher import EnhancedEventDispatcher
        from src.events.core.base_handler import AbstractHandler
        from src.events.domain import EventResult

        class TestHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                return EventResult.success_result()

        dispatcher = EnhancedEventDispatcher()
        handler = TestHandler()

        dispatcher.register(handler)

        assert dispatcher.has_handlers('test.event')

    def test_dispatcher_dispatch_to_handler(self):
        """Dispatch event to registered handler."""
        from src.events.core.dispatcher import EnhancedEventDispatcher
        from src.events.core.base_handler import AbstractHandler
        from src.events.core.base import Event
        from src.events.domain import EventResult

        class TestHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                return EventResult.success_result({'handled': True})

        dispatcher = EnhancedEventDispatcher()
        dispatcher.register(TestHandler())

        event = Event(name='test.event')
        result = dispatcher.dispatch(event)

        assert result.success is True

    def test_dispatch_sorts_by_priority(self):
        """Handlers execute in priority order (highest first)."""
        from src.events.core.dispatcher import EnhancedEventDispatcher
        from src.events.core.handler import HandlerPriority
        from src.events.core.base_handler import AbstractHandler
        from src.events.core.base import Event
        from src.events.domain import EventResult

        execution_order = []

        class LowPriorityHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            @staticmethod
            def get_priority() -> int:
                return HandlerPriority.LOW

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                execution_order.append('low')
                return EventResult.success_result()

        class HighPriorityHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            @staticmethod
            def get_priority() -> int:
                return HandlerPriority.HIGH

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                execution_order.append('high')
                return EventResult.success_result()

        class NormalPriorityHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            @staticmethod
            def get_priority() -> int:
                return HandlerPriority.NORMAL

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                execution_order.append('normal')
                return EventResult.success_result()

        dispatcher = EnhancedEventDispatcher()
        # Register in random order
        dispatcher.register(LowPriorityHandler())
        dispatcher.register(HighPriorityHandler())
        dispatcher.register(NormalPriorityHandler())

        event = Event(name='test.event')
        dispatcher.dispatch(event)

        # Should execute in priority order: high, normal, low
        assert execution_order == ['high', 'normal', 'low']

    def test_dispatch_stops_on_propagation_stopped(self):
        """Stops calling handlers after stop_propagation()."""
        from src.events.core.dispatcher import EnhancedEventDispatcher
        from src.events.core.handler import HandlerPriority
        from src.events.core.base_handler import AbstractHandler
        from src.events.core.base import Event
        from src.events.domain import EventResult

        execution_order = []

        class FirstHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            @staticmethod
            def get_priority() -> int:
                return HandlerPriority.HIGHEST

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                execution_order.append('first')
                event.stop_propagation()  # Stop here
                return EventResult.success_result()

        class SecondHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            @staticmethod
            def get_priority() -> int:
                return HandlerPriority.NORMAL

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                execution_order.append('second')  # Should not be called
                return EventResult.success_result()

        dispatcher = EnhancedEventDispatcher()
        dispatcher.register(FirstHandler())
        dispatcher.register(SecondHandler())

        event = Event(name='test.event')
        dispatcher.dispatch(event)

        # Second handler should not have executed
        assert execution_order == ['first']

    def test_dispatch_with_context(self):
        """Dispatcher passes context to handlers."""
        from src.events.core.dispatcher import EnhancedEventDispatcher
        from src.events.core.context import EventContext
        from src.events.core.base_handler import AbstractHandler
        from src.events.core.base import Event
        from src.events.domain import EventResult

        ctx = EventContext()
        ctx.set('request_id', 'req-456')

        class ContextAwareHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                request_id = self.context.get('request_id') if self.context else None
                return EventResult.success_result({'request_id': request_id})

        dispatcher = EnhancedEventDispatcher(context=ctx)
        handler = ContextAwareHandler()
        dispatcher.register(handler)

        event = Event(name='test.event')
        result = dispatcher.dispatch(event)

        assert result.success is True

    def test_dispatch_handles_exceptions(self):
        """Handler exceptions don't crash dispatcher."""
        from src.events.core.dispatcher import EnhancedEventDispatcher
        from src.events.core.handler import HandlerPriority
        from src.events.core.base_handler import AbstractHandler
        from src.events.core.base import Event
        from src.events.domain import EventResult

        class FailingHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            @staticmethod
            def get_priority() -> int:
                return HandlerPriority.HIGH

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                raise ValueError("Handler failed!")

        class SuccessHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            @staticmethod
            def get_priority() -> int:
                return HandlerPriority.NORMAL

            def can_handle(self, event) -> bool:
                return True

            def handle(self, event) -> EventResult:
                return EventResult.success_result({'second': True})

        dispatcher = EnhancedEventDispatcher()
        dispatcher.register(FailingHandler())
        dispatcher.register(SuccessHandler())

        event = Event(name='test.event')
        result = dispatcher.dispatch(event)

        # Should have error from failing handler
        assert result.success is False
        assert 'Handler failed!' in result.error

    def test_dispatch_no_handlers(self):
        """Dispatch returns no_handler when no handlers registered."""
        from src.events.core.dispatcher import EnhancedEventDispatcher
        from src.events.core.base import Event

        dispatcher = EnhancedEventDispatcher()
        event = Event(name='unhandled.event')
        result = dispatcher.dispatch(event)

        assert result.success is False
        assert result.error_type == 'no_handler'

    def test_dispatch_can_handle_filtering(self):
        """Only handlers that can_handle are called."""
        from src.events.core.dispatcher import EnhancedEventDispatcher
        from src.events.core.base_handler import AbstractHandler
        from src.events.core.base import Event
        from src.events.domain import EventResult

        executed = []

        class SelectiveHandler(AbstractHandler):
            @staticmethod
            def get_handled_event_class() -> str:
                return 'test.event'

            def can_handle(self, event) -> bool:
                # Only handle events with specific data
                return event.data.get('process') is True

            def handle(self, event) -> EventResult:
                executed.append(True)
                return EventResult.success_result()

        dispatcher = EnhancedEventDispatcher()
        dispatcher.register(SelectiveHandler())

        # Event without 'process' flag - should not be handled
        event1 = Event(name='test.event', data={})
        result1 = dispatcher.dispatch(event1)
        assert len(executed) == 0

        # Event with 'process' flag - should be handled
        event2 = Event(name='test.event', data={'process': True})
        result2 = dispatcher.dispatch(event2)
        assert len(executed) == 1
