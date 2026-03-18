"""Event system core components."""
from vbwd.events.core.interfaces import EventInterface
from vbwd.events.core.base import Event
from vbwd.events.core.context import EventContext
from vbwd.events.core.handler import HandlerPriority, IEventHandler
from vbwd.events.core.base_handler import AbstractHandler
from vbwd.events.core.dispatcher import EnhancedEventDispatcher

__all__ = [
    "EventInterface",
    "Event",
    "EventContext",
    "HandlerPriority",
    "IEventHandler",
    "AbstractHandler",
    "EnhancedEventDispatcher",
]
