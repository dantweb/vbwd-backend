"""Webhook data transfer objects."""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID

from src.webhooks.enums import WebhookEventType


@dataclass
class NormalizedWebhookEvent:
    """Provider-agnostic webhook event.

    Normalizes webhook payloads from different providers
    into a consistent format for processing.
    """

    provider: str
    event_id: str
    event_type: WebhookEventType
    payment_intent_id: Optional[str] = None
    subscription_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookResult:
    """Result of webhook processing.

    Returned by webhook handlers to indicate success or failure.
    """

    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
