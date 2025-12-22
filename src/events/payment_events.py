"""Payment domain events."""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID


@dataclass
class CheckoutInitiatedEvent:
    """User initiated checkout for a tariff plan.

    Emitted when user starts the checkout process.
    Handler should create payment intent via SDK adapter.
    """

    user_id: UUID
    tarif_plan_id: UUID
    provider: str
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    name: str = field(default='checkout.initiated', init=False)


@dataclass
class PaymentCapturedEvent:
    """Payment successfully captured.

    Emitted when payment provider confirms successful payment.
    Handler should activate subscription and mark invoice as paid.
    """

    subscription_id: UUID
    user_id: UUID
    transaction_id: str
    amount: Decimal
    currency: str
    provider: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    name: str = field(default='payment.captured', init=False)


@dataclass
class PaymentFailedEvent:
    """Payment failed.

    Emitted when payment provider reports payment failure.
    Handler should update subscription status and notify user.
    """

    subscription_id: UUID
    user_id: UUID
    error_code: str
    error_message: str
    provider: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    name: str = field(default='payment.failed', init=False)


@dataclass
class RefundRequestedEvent:
    """Refund requested.

    Emitted when a refund is requested for a transaction.
    Handler should call SDK adapter to process refund.
    """

    transaction_id: str
    subscription_id: UUID
    reason: str
    provider: Optional[str] = None
    amount: Optional[Decimal] = None  # None for full refund
    metadata: Dict[str, Any] = field(default_factory=dict)
    name: str = field(default='refund.requested', init=False)
