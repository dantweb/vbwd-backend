"""Event dispatcher for plugin system."""
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum


class EventPriority(Enum):
    """Event listener priority."""

    HIGHEST = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    LOWEST = 5


@dataclass
class Event:
    """Base event class."""

    name: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    propagation_stopped: bool = False

    def stop_propagation(self) -> None:
        """Stop event propagation to remaining listeners."""
        self.propagation_stopped = True


@dataclass
class EventListener:
    """Event listener registration."""

    callback: Callable[[Event], None]
    priority: EventPriority = EventPriority.NORMAL

    def __lt__(self, other):
        """Compare by priority for sorting."""
        return self.priority.value < other.priority.value


class EventDispatcher:
    """
    Event dispatcher for plugin system.

    Allows plugins to listen to and emit events.
    """

    def __init__(self):
        self._listeners: Dict[str, List[EventListener]] = {}

    def add_listener(
        self,
        event_name: str,
        callback: Callable[[Event], None],
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """
        Register event listener.

        Args:
            event_name: Name of event to listen for
            callback: Callback function to invoke
            priority: Listener priority (higher = earlier execution)
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []

        listener = EventListener(callback=callback, priority=priority)
        self._listeners[event_name].append(listener)

        # Sort by priority
        self._listeners[event_name].sort()

    def remove_listener(
        self,
        event_name: str,
        callback: Callable[[Event], None],
    ) -> None:
        """Remove event listener."""
        if event_name not in self._listeners:
            return

        self._listeners[event_name] = [
            listener
            for listener in self._listeners[event_name]
            if listener.callback != callback
        ]

    def dispatch(self, event: Event) -> Event:
        """
        Dispatch event to all registered listeners.

        Args:
            event: Event to dispatch

        Returns:
            The event (possibly modified by listeners)
        """
        if event.name not in self._listeners:
            return event

        for listener in self._listeners[event.name]:
            if event.propagation_stopped:
                break

            try:
                listener.callback(event)
            except Exception as e:
                # Log error but continue to other listeners
                print(f"Error in event listener: {e}")

        return event

    def has_listeners(self, event_name: str) -> bool:
        """Check if event has any listeners."""
        return event_name in self._listeners and len(self._listeners[event_name]) > 0

    def get_listeners(self, event_name: str) -> List[EventListener]:
        """Get all listeners for event."""
        return self._listeners.get(event_name, [])
