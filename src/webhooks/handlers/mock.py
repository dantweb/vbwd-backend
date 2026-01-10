"""Mock webhook handler for testing."""
from decimal import Decimal
from typing import Dict, Any, List

from src.webhooks.handlers.base import IWebhookHandler
from src.webhooks.dto import NormalizedWebhookEvent, WebhookResult
from src.webhooks.enums import WebhookEventType


class MockWebhookHandler(IWebhookHandler):
    """Mock webhook handler for testing.

    Features:
    - Configurable success/failure mode
    - Tracks all handled events for assertions
    - Accepts 'valid_signature' as valid signature
    """

    def __init__(self, should_fail: bool = False):
        """Initialize mock handler.

        Args:
            should_fail: If True, handle() returns failure
        """
        self._should_fail = should_fail
        self._handled_events: List[NormalizedWebhookEvent] = []

    @property
    def provider(self) -> str:
        """Return 'mock' as provider name."""
        return "mock"

    @property
    def handled_events(self) -> List[NormalizedWebhookEvent]:
        """Return list of all handled events."""
        return self._handled_events

    def verify_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify signature - accepts 'valid_signature'.

        Args:
            payload: Raw payload bytes (ignored)
            signature: Signature string
            secret: Secret string (ignored)

        Returns:
            True if signature is 'valid_signature'
        """
        return signature == "valid_signature"

    def parse_event(self, payload: Dict[str, Any]) -> NormalizedWebhookEvent:
        """Parse payload to normalized event.

        Expected payload format:
        {
            'id': 'evt_123',
            'type': 'payment.succeeded',
            'data': {
                'payment_intent_id': 'pi_123',
                'amount': 2999,  # cents
                'currency': 'usd'
            }
        }
        """
        event_id = payload.get("id", "evt_unknown")
        event_type_str = payload.get("type", "unknown")
        data = payload.get("data", {})

        # Map event type string to enum
        event_type = self._map_event_type(event_type_str)

        # Extract amount (convert from cents to decimal)
        amount = None
        if "amount" in data:
            amount = Decimal(data["amount"]) / 100

        # Extract currency (uppercase)
        currency = data.get("currency", "").upper() if data.get("currency") else None

        return NormalizedWebhookEvent(
            provider="mock",
            event_id=event_id,
            event_type=event_type,
            payment_intent_id=data.get("payment_intent_id"),
            amount=amount,
            currency=currency,
            raw_payload=payload,
        )

    def handle(self, event: NormalizedWebhookEvent) -> WebhookResult:
        """Handle the event.

        Tracks event and returns success/failure based on configuration.
        """
        self._handled_events.append(event)

        if self._should_fail:
            return WebhookResult(success=False, error="Mock handler configured to fail")

        return WebhookResult(
            success=True, message=f"Successfully processed {event.event_type.value}"
        )

    def _map_event_type(self, event_type_str: str) -> WebhookEventType:
        """Map event type string to enum."""
        mapping = {
            "payment.succeeded": WebhookEventType.PAYMENT_SUCCEEDED,
            "payment.failed": WebhookEventType.PAYMENT_FAILED,
            "subscription.created": WebhookEventType.SUBSCRIPTION_CREATED,
            "subscription.updated": WebhookEventType.SUBSCRIPTION_UPDATED,
            "subscription.cancelled": WebhookEventType.SUBSCRIPTION_CANCELLED,
            "refund.created": WebhookEventType.REFUND_CREATED,
            "dispute.created": WebhookEventType.DISPUTE_CREATED,
        }
        return mapping.get(event_type_str, WebhookEventType.UNKNOWN)
