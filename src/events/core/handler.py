"""Event handler interface and priority constants."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.events.core.interfaces import EventInterface
    from src.events.domain import EventResult


class HandlerPriority:
    """
    Handler priority constants.

    Higher values execute first.
    """

    HIGHEST = 100
    HIGH = 75
    NORMAL = 50
    LOW = 25
    LOWEST = 0


class IEventHandler(ABC):
    """
    Interface for event handlers (Liskov-compliant).

    All domain event handlers must implement this interface.
    Handlers are executed in priority order (highest first).
    """

    @staticmethod
    @abstractmethod
    def get_handled_event_class() -> str:
        """
        Return event class name this handler handles.

        Returns:
            Event name/type string (e.g., 'user.created')
        """
        pass

    @staticmethod
    def get_priority() -> int:
        """
        Return handler priority.

        Higher values execute first. Default is NORMAL (50).

        Returns:
            Priority value (0-100)
        """
        return HandlerPriority.NORMAL

    @abstractmethod
    def can_handle(self, event: 'EventInterface') -> bool:
        """
        Check if handler can process this event.

        Called before handle() to allow conditional handling
        based on event data.

        Args:
            event: Event to check

        Returns:
            True if handler should process this event
        """
        pass

    @abstractmethod
    def handle(self, event: 'EventInterface') -> 'EventResult':
        """
        Process event and return result.

        Args:
            event: Event to process

        Returns:
            EventResult with success/failure status
        """
        pass
