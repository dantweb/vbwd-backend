"""Event system for plugin communication."""
from vbwd.events.domain import (
    DomainEvent,
    EventResult,
    IEventHandler,
    DomainEventDispatcher,
)
from vbwd.events.checkout_events import (
    CheckoutRequestedEvent,
    CheckoutCompletedEvent,
    CheckoutFailedEvent,
)
from vbwd.events.payment_events import (
    PaymentCapturedEvent,
    PaymentFailedEvent,
)
from vbwd.events.bus import EventBus, event_bus

__all__ = [
    "DomainEvent",
    "EventResult",
    "IEventHandler",
    "DomainEventDispatcher",
    "CheckoutRequestedEvent",
    "CheckoutCompletedEvent",
    "CheckoutFailedEvent",
    "PaymentCapturedEvent",
    "PaymentFailedEvent",
    "EventBus",
    "event_bus",
]
