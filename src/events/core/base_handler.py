"""Abstract base handler with common functionality."""
from typing import Optional, TYPE_CHECKING, Any

from src.events.core.handler import IEventHandler, HandlerPriority
from src.events.domain import EventResult

if TYPE_CHECKING:
    from src.events.core.interfaces import EventInterface
    from src.events.core.context import EventContext


class AbstractHandler(IEventHandler):
    """
    Base handler with common functionality.

    Provides:
    - Default NORMAL priority
    - emit() for event chaining
    - Context access for request-scoped data
    """

    def __init__(
        self,
        dispatcher: Optional[Any] = None,
        context: Optional['EventContext'] = None
    ):
        """
        Initialize handler.

        Args:
            dispatcher: Optional dispatcher for emitting events
            context: Optional context for request-scoped data
        """
        self._dispatcher = dispatcher
        self._context = context

    @property
    def context(self) -> Optional['EventContext']:
        """Get event context."""
        return self._context

    @staticmethod
    def get_priority() -> int:
        """Return default NORMAL priority."""
        return HandlerPriority.NORMAL

    def emit(self, event: 'EventInterface') -> EventResult:
        """
        Emit event via dispatcher (for event chaining).

        Allows handlers to trigger additional events as part
        of their processing.

        Args:
            event: Event to emit

        Returns:
            EventResult from dispatcher, or no_handler if no dispatcher
        """
        if self._dispatcher:
            return self._dispatcher.dispatch(event)
        return EventResult.no_handler()
