"""Refund reversal event handler — restores invoice and items."""
from src.events.domain import DomainEvent, EventResult, IEventHandler
from src.events.payment_events import RefundReversedEvent
from src.services.restore_service import RestoreService


class RefundReversedHandler(IEventHandler):
    """
    Handler for refund reversal events.

    Delegates to RestoreService which re-activates:
    - Invoice → PAID
    - Subscription → ACTIVE
    - Token bundles → tokens re-credited
    - Add-ons → ACTIVE
    """

    def __init__(self, container):
        self._container = container

    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, RefundReversedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        if not isinstance(event, RefundReversedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            if event.invoice_id is None:
                return EventResult.error_result("Invoice ID is required")
            service = RestoreService(self._container)
            result = service.process_restore(
                invoice_id=event.invoice_id,
                reason=event.reason,
            )

            if not result.success:
                return EventResult.error_result(result.error or "Unknown error")

            return EventResult.success_result(
                {
                    "invoice_id": str(result.invoice.id),
                    "status": "paid",
                    "items_restored": result.items_restored,
                }
            )
        except Exception as e:
            return EventResult.error_result(str(e))
