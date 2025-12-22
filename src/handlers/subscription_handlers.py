"""Subscription event handlers."""
from src.events.domain import IEventHandler, DomainEvent, EventResult
from src.events.subscription_events import (
    SubscriptionCreatedEvent,
    SubscriptionActivatedEvent,
    SubscriptionCancelledEvent,
    SubscriptionExpiredEvent,
    PaymentCompletedEvent,
    PaymentFailedEvent,
)


class SubscriptionActivatedHandler(IEventHandler):
    """
    Handler for subscription activation events.

    This handler performs actions when a subscription is activated.
    """

    def __init__(self):
        """Initialize handler."""
        self.handled_events = []

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler handles subscription.activated events."""
        return isinstance(event, SubscriptionActivatedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle subscription activation event.

        Args:
            event: SubscriptionActivatedEvent

        Returns:
            EventResult indicating success or failure
        """
        if not isinstance(event, SubscriptionActivatedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            # Track handled events
            self.handled_events.append(event)

            # Here you would:
            # - Send activation confirmation email
            # - Grant access to paid features
            # - Log activation
            # - Update user status

            return EventResult.success_result({
                "subscription_id": str(event.subscription_id),
                "user_id": str(event.user_id),
                "handled": True
            })

        except Exception as e:
            return EventResult.error_result(str(e))


class SubscriptionCancelledHandler(IEventHandler):
    """
    Handler for subscription cancellation events.

    This handler performs actions when a subscription is cancelled.
    """

    def __init__(self):
        """Initialize handler."""
        self.handled_events = []

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler handles subscription.cancelled events."""
        return isinstance(event, SubscriptionCancelledEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle subscription cancellation event.

        Args:
            event: SubscriptionCancelledEvent

        Returns:
            EventResult indicating success or failure
        """
        if not isinstance(event, SubscriptionCancelledEvent):
            return EventResult.error_result("Invalid event type")

        try:
            # Track handled events
            self.handled_events.append(event)

            # Here you would:
            # - Send cancellation confirmation
            # - Schedule access removal
            # - Log cancellation
            # - Trigger retention workflow

            return EventResult.success_result({
                "subscription_id": str(event.subscription_id),
                "user_id": str(event.user_id),
                "handled": True
            })

        except Exception as e:
            return EventResult.error_result(str(e))


class PaymentCompletedHandler(IEventHandler):
    """
    Handler for payment completion events.

    This handler activates subscriptions when payment is completed.
    """

    def __init__(self, subscription_service=None):
        """
        Initialize handler.

        Args:
            subscription_service: Optional SubscriptionService for activation
        """
        self.handled_events = []
        self.subscription_service = subscription_service

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler handles payment.completed events."""
        return isinstance(event, PaymentCompletedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle payment completion event.

        Args:
            event: PaymentCompletedEvent

        Returns:
            EventResult indicating success or failure
        """
        if not isinstance(event, PaymentCompletedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            # Track handled events
            self.handled_events.append(event)

            # Activate subscription if service available
            if self.subscription_service:
                self.subscription_service.activate_subscription(event.subscription_id)

            # Here you would also:
            # - Send payment receipt
            # - Create invoice record
            # - Log transaction
            # - Send activation email

            return EventResult.success_result({
                "subscription_id": str(event.subscription_id),
                "transaction_id": event.transaction_id,
                "activated": self.subscription_service is not None,
                "handled": True
            })

        except Exception as e:
            return EventResult.error_result(str(e))


class PaymentFailedHandler(IEventHandler):
    """
    Handler for payment failure events.

    This handler performs actions when payment fails.
    """

    def __init__(self):
        """Initialize handler."""
        self.handled_events = []

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler handles payment.failed events."""
        return isinstance(event, PaymentFailedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle payment failure event.

        Args:
            event: PaymentFailedEvent

        Returns:
            EventResult indicating success or failure
        """
        if not isinstance(event, PaymentFailedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            # Track handled events
            self.handled_events.append(event)

            # Here you would:
            # - Send payment failure notification
            # - Log failure
            # - Trigger retry workflow
            # - Update subscription status

            return EventResult.success_result({
                "subscription_id": str(event.subscription_id),
                "user_id": str(event.user_id),
                "handled": True
            })

        except Exception as e:
            return EventResult.error_result(str(e))
