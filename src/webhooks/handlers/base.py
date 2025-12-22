"""Base webhook handler interface."""
from abc import ABC, abstractmethod
from typing import Dict, Any

from src.webhooks.dto import NormalizedWebhookEvent, WebhookResult


class IWebhookHandler(ABC):
    """Interface for webhook handlers.

    All payment provider webhook handlers must implement this interface.
    Liskov Substitution: Any IWebhookHandler can be used interchangeably.
    """

    @property
    @abstractmethod
    def provider(self) -> str:
        """Return provider name this handler supports.

        Returns:
            Provider name (e.g., 'stripe', 'paypal', 'mock')
        """
        ...

    @abstractmethod
    def verify_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature.

        Args:
            payload: Raw webhook payload bytes
            signature: Signature from webhook headers
            secret: Webhook signing secret

        Returns:
            True if signature is valid
        """
        ...

    @abstractmethod
    def parse_event(self, payload: Dict[str, Any]) -> NormalizedWebhookEvent:
        """Parse raw payload to normalized event.

        Args:
            payload: Parsed JSON payload

        Returns:
            Normalized webhook event
        """
        ...

    @abstractmethod
    def handle(self, event: NormalizedWebhookEvent) -> WebhookResult:
        """Process the normalized event.

        Args:
            event: Normalized webhook event

        Returns:
            Result of processing
        """
        ...
