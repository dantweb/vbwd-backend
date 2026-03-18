"""Event system interfaces and protocols."""
from typing import Protocol, Dict, Any, runtime_checkable


@runtime_checkable
class EventInterface(Protocol):
    """
    Protocol for all events (Liskov-compliant).

    All events must implement this interface to be
    compatible with the event system.
    """

    @property
    def name(self) -> str:
        """Event name/type identifier."""
        ...

    @property
    def data(self) -> Dict[str, Any]:
        """Event payload data."""
        ...

    def stop_propagation(self) -> None:
        """Stop event propagation to remaining handlers."""
        ...

    def is_propagation_stopped(self) -> bool:
        """Check if propagation has been stopped."""
        ...
