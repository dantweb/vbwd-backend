"""Webhook service for processing incoming webhooks."""
import json
from typing import Dict, Optional

from src.webhooks.handlers.base import IWebhookHandler
from src.webhooks.dto import WebhookResult


class WebhookService:
    """Core webhook processing service.

    Manages webhook handlers and coordinates webhook processing.
    """

    def __init__(
        self,
        handlers: Optional[Dict[str, IWebhookHandler]] = None,
        webhook_secrets: Optional[Dict[str, str]] = None,
    ):
        """Initialize webhook service.

        Args:
            handlers: Dictionary of provider -> handler
            webhook_secrets: Dictionary of provider -> webhook secret
        """
        self._handlers: Dict[str, IWebhookHandler] = handlers or {}
        self._secrets: Dict[str, str] = webhook_secrets or {}

    def register_handler(self, handler: IWebhookHandler, webhook_secret: str) -> None:
        """Register a webhook handler.

        Args:
            handler: Handler implementing IWebhookHandler
            webhook_secret: Webhook signing secret for this provider
        """
        self._handlers[handler.provider] = handler
        self._secrets[handler.provider] = webhook_secret

    def has_handler(self, provider: str) -> bool:
        """Check if handler exists for provider.

        Args:
            provider: Provider name

        Returns:
            True if handler is registered
        """
        return provider in self._handlers

    def get_handler(self, provider: str) -> Optional[IWebhookHandler]:
        """Get handler for provider.

        Args:
            provider: Provider name

        Returns:
            Handler or None if not found
        """
        return self._handlers.get(provider)

    def process(
        self, provider: str, payload: bytes, signature: str, headers: Dict[str, str]
    ) -> WebhookResult:
        """Process incoming webhook.

        Args:
            provider: Provider name (e.g., 'stripe', 'paypal')
            payload: Raw webhook payload bytes
            signature: Signature from webhook headers
            headers: All webhook headers

        Returns:
            WebhookResult indicating success or failure
        """
        # Get handler for provider
        handler = self._handlers.get(provider)
        if not handler:
            return WebhookResult(success=False, error=f"Unknown provider: {provider}")

        # Get webhook secret
        secret = self._secrets.get(provider, "")

        # Verify signature
        if not handler.verify_signature(payload, signature, secret):
            return WebhookResult(success=False, error="Invalid signature")

        # Parse JSON payload
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            return WebhookResult(success=False, error=f"Failed to parse JSON: {str(e)}")

        # Parse to normalized event
        try:
            event = handler.parse_event(data)
        except Exception as e:
            return WebhookResult(
                success=False, error=f"Failed to parse event: {str(e)}"
            )

        # Process via handler
        try:
            result = handler.handle(event)
            return result
        except Exception as e:
            return WebhookResult(success=False, error=f"Handler error: {str(e)}")
