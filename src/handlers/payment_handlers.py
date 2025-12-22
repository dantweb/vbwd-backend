"""Payment event handlers."""
from typing import List, Optional, TYPE_CHECKING

from src.events.domain import IEventHandler, EventResult
from src.events.payment_events import (
    CheckoutInitiatedEvent,
    PaymentCapturedEvent,
    PaymentFailedEvent,
    RefundRequestedEvent
)

if TYPE_CHECKING:
    from src.sdk.registry import SDKAdapterRegistry


class CheckoutInitiatedHandler(IEventHandler):
    """Handle checkout initiation.

    Creates payment intent via SDK adapter.
    """

    def __init__(self, sdk_registry: 'SDKAdapterRegistry'):
        """Initialize handler.

        Args:
            sdk_registry: Registry of SDK adapters
        """
        self._sdk_registry = sdk_registry

    @staticmethod
    def get_handled_event_class() -> str:
        """Return handled event name."""
        return 'checkout.initiated'

    def can_handle(self, event) -> bool:
        """Check if can handle event."""
        return isinstance(event, CheckoutInitiatedEvent)

    def handle(self, event: CheckoutInitiatedEvent) -> EventResult:
        """Handle checkout initiation.

        Creates payment intent via SDK adapter.
        """
        try:
            adapter = self._sdk_registry.get(event.provider)
        except ValueError as e:
            return EventResult.error_result(str(e))

        # Call SDK to create payment intent
        sdk_result = adapter.create_payment_intent(
            amount=event.amount,
            currency=event.currency or 'USD',
            metadata={
                'user_id': str(event.user_id),
                'tarif_plan_id': str(event.tarif_plan_id)
            }
        )

        if sdk_result.success:
            return EventResult.success_result({
                'payment_intent_id': sdk_result.data.get('payment_intent_id'),
                'client_secret': sdk_result.data.get('client_secret'),
                'checkout_url': sdk_result.data.get('checkout_url')
            })
        else:
            return EventResult.error_result(sdk_result.error)


class PaymentCapturedHandler(IEventHandler):
    """Handle successful payment capture.

    Updates subscription and invoice status.
    """

    def __init__(self):
        """Initialize handler."""
        self._processed_events: List[PaymentCapturedEvent] = []

    @staticmethod
    def get_handled_event_class() -> str:
        """Return handled event name."""
        return 'payment.captured'

    @property
    def processed_events(self) -> List[PaymentCapturedEvent]:
        """Return list of processed events."""
        return self._processed_events

    def can_handle(self, event) -> bool:
        """Check if can handle event."""
        return isinstance(event, PaymentCapturedEvent)

    def handle(self, event: PaymentCapturedEvent) -> EventResult:
        """Handle payment captured.

        Activates subscription and marks invoice as paid.
        """
        self._processed_events.append(event)

        # In a real implementation, this would:
        # 1. Activate subscription via SubscriptionService
        # 2. Mark invoice as paid via InvoiceService
        # 3. Send confirmation notification

        return EventResult.success_result({
            'subscription_id': str(event.subscription_id),
            'transaction_id': event.transaction_id,
            'activated': True
        })


class PaymentFailedHandler(IEventHandler):
    """Handle payment failure.

    Updates subscription status and notifies user.
    """

    def __init__(self):
        """Initialize handler."""
        self._processed_events: List[PaymentFailedEvent] = []

    @staticmethod
    def get_handled_event_class() -> str:
        """Return handled event name."""
        return 'payment.failed'

    @property
    def processed_events(self) -> List[PaymentFailedEvent]:
        """Return list of processed events."""
        return self._processed_events

    def can_handle(self, event) -> bool:
        """Check if can handle event."""
        return isinstance(event, PaymentFailedEvent)

    def handle(self, event: PaymentFailedEvent) -> EventResult:
        """Handle payment failure.

        Updates subscription status.
        """
        self._processed_events.append(event)

        # In a real implementation, this would:
        # 1. Update subscription status via SubscriptionService
        # 2. Send failure notification to user

        return EventResult.success_result({
            'subscription_id': str(event.subscription_id),
            'error_code': event.error_code,
            'notified': True
        })


class RefundRequestedHandler(IEventHandler):
    """Handle refund request.

    Calls SDK adapter to process refund.
    """

    def __init__(self, sdk_registry: 'SDKAdapterRegistry'):
        """Initialize handler.

        Args:
            sdk_registry: Registry of SDK adapters
        """
        self._sdk_registry = sdk_registry

    @staticmethod
    def get_handled_event_class() -> str:
        """Return handled event name."""
        return 'refund.requested'

    def can_handle(self, event) -> bool:
        """Check if can handle event."""
        return isinstance(event, RefundRequestedEvent)

    def handle(self, event: RefundRequestedEvent) -> EventResult:
        """Handle refund request.

        Calls SDK adapter to process refund.
        """
        try:
            adapter = self._sdk_registry.get(event.provider)
        except (ValueError, AttributeError) as e:
            return EventResult.error_result(f"Provider error: {e}")

        # Call SDK to refund payment
        sdk_result = adapter.refund_payment(
            payment_intent_id=event.transaction_id,
            amount=event.amount
        )

        if sdk_result.success:
            return EventResult.success_result({
                'refund_id': sdk_result.data.get('refund_id'),
                'amount': str(event.amount) if event.amount else 'full',
                'reason': event.reason
            })
        else:
            return EventResult.error_result(sdk_result.error)
