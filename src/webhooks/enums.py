"""Webhook enums."""
import enum


class WebhookStatus(enum.Enum):
    """Webhook processing status."""

    RECEIVED = 'received'
    PROCESSING = 'processing'
    PROCESSED = 'processed'
    FAILED = 'failed'
    SKIPPED = 'skipped'


class WebhookEventType(enum.Enum):
    """Normalized webhook event types.

    Provider-agnostic event types for consistent handling
    across different payment providers.
    """

    PAYMENT_SUCCEEDED = 'payment.succeeded'
    PAYMENT_FAILED = 'payment.failed'
    SUBSCRIPTION_CREATED = 'subscription.created'
    SUBSCRIPTION_UPDATED = 'subscription.updated'
    SUBSCRIPTION_CANCELLED = 'subscription.cancelled'
    REFUND_CREATED = 'refund.created'
    DISPUTE_CREATED = 'dispute.created'
    UNKNOWN = 'unknown'
