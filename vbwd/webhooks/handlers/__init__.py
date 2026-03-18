"""Webhook handlers."""

from vbwd.webhooks.handlers.base import IWebhookHandler
from vbwd.webhooks.handlers.mock import MockWebhookHandler

__all__ = [
    "IWebhookHandler",
    "MockWebhookHandler",
]
