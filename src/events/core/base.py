"""Event base class."""
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Event:
    """
    Base event class implementing EventInterface.

    This is the foundation for all domain events in the system.
    """

    name: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    _propagation_stopped: bool = field(default=False, repr=False)

    def stop_propagation(self) -> None:
        """Stop event propagation to remaining handlers."""
        self._propagation_stopped = True

    def is_propagation_stopped(self) -> bool:
        """Check if propagation has been stopped."""
        return self._propagation_stopped
