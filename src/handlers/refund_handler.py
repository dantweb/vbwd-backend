"""Refund event handler — thin delegation to RefundService."""
from src.events.domain import DomainEvent, EventResult, IEventHandler
from src.events.payment_events import PaymentRefundedEvent


class PaymentRefundedHandler(IEventHandler):
    """
    Handler for payment refund events.

    Delegates to RefundService which orchestrates:
    - Subscription cancellation
    - Token balance debit
    - Add-on cancellation
    """

    def __init__(self, container):
        self._container = container

    def can_handle(self, event: DomainEvent) -> bool:
        return isinstance(event, PaymentRefundedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        if not isinstance(event, PaymentRefundedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            refund_service = self._container.refund_service()
            result = refund_service.process_refund(
                invoice_id=event.invoice_id,
                refund_reference=event.refund_reference,
            )

            if not result.success:
                return EventResult.error_result(result.error)

            return EventResult.success_result(
                {
                    "invoice_id": str(result.invoice.id),
                    "invoice": result.invoice.to_dict(),
                    "status": "refunded",
                    "refund_reference": event.refund_reference,
                    "items_reversed": result.items_reversed,
                }
            )
        except Exception as e:
            return EventResult.error_result(str(e))
