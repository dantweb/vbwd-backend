"""Webhook handlers."""

from src.webhooks.handlers.base import IWebhookHandler
from src.webhooks.handlers.mock import MockWebhookHandler

__all__ = [
    "IWebhookHandler",
    "MockWebhookHandler",
]
