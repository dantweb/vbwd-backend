"""Enhanced event dispatcher with priority support."""
from typing import Dict, List, Tuple, Optional, TYPE_CHECKING

from src.events.domain import EventResult

if TYPE_CHECKING:
    from src.events.core.interfaces import EventInterface
    from src.events.core.handler import IEventHandler
    from src.events.core.context import EventContext


class EnhancedEventDispatcher:
    """
    Priority-based event dispatcher.

    Handlers are executed in priority order (highest first).
    Supports event propagation control and context passing.
    """

    def __init__(self, context: Optional['EventContext'] = None):
        """
        Initialize dispatcher.

        Args:
            context: Optional shared context for handlers
        """
        # Dict[event_name, List[Tuple[priority, handler]]]
        self._handlers: Dict[str, List[Tuple[int, 'IEventHandler']]] = {}
        self._context = context

    def register(self, handler: 'IEventHandler') -> None:
        """
        Register handler (sorted by priority).

        Args:
            handler: Handler instance implementing IEventHandler
        """
        event_class = handler.get_handled_event_class()
        priority = handler.get_priority()

        if event_class not in self._handlers:
            self._handlers[event_class] = []

        # Set context on handler if it has the attribute
        if hasattr(handler, '_context') and self._context:
            handler._context = self._context

        # Insert maintaining sorted order (descending priority)
        self._handlers[event_class].append((priority, handler))
        self._handlers[event_class].sort(key=lambda x: x[0], reverse=True)

    def unregister(self, handler: 'IEventHandler') -> None:
        """
        Unregister handler.

        Args:
            handler: Handler to remove
        """
        event_class = handler.get_handled_event_class()
        if event_class in self._handlers:
            self._handlers[event_class] = [
                (p, h) for p, h in self._handlers[event_class]
                if h is not handler
            ]

    def has_handlers(self, event_name: str) -> bool:
        """
        Check if event has any handlers.

        Args:
            event_name: Event name to check

        Returns:
            True if handlers registered for this event
        """
        return event_name in self._handlers and len(self._handlers[event_name]) > 0

    def dispatch(self, event: 'EventInterface') -> EventResult:
        """
        Dispatch event to registered handlers.

        Handlers are called in priority order (highest first).
        Execution stops if event.stop_propagation() is called.

        Args:
            event: Event to dispatch

        Returns:
            Combined EventResult from all handlers
        """
        if event.name not in self._handlers:
            return EventResult.no_handler()

        results: List[EventResult] = []

        for priority, handler in self._handlers[event.name]:
            # Check propagation stopped
            if event.is_propagation_stopped():
                break

            try:
                if handler.can_handle(event):
                    result = handler.handle(event)
                    results.append(result)
            except Exception as e:
                results.append(EventResult.error_result(
                    error=str(e),
                    error_type='handler_exception'
                ))

        if not results:
            return EventResult.no_handler()

        return EventResult.combine(results)

    def get_handlers(self, event_name: str) -> List['IEventHandler']:
        """
        Get all handlers for event.

        Args:
            event_name: Event name

        Returns:
            List of handlers (in priority order)
        """
        if event_name not in self._handlers:
            return []
        return [handler for _, handler in self._handlers[event_name]]
