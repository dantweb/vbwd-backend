"""Payment provider plugin interface."""
from abc import abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal
from uuid import UUID
from enum import Enum
from src.plugins.base import BasePlugin


class PaymentStatus(Enum):
    """Payment status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentResult:
    """Payment transaction result."""

    def __init__(
        self,
        success: bool,
        transaction_id: Optional[str] = None,
        status: PaymentStatus = PaymentStatus.PENDING,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.transaction_id = transaction_id
        self.status = status
        self.error_message = error_message
        self.metadata = metadata or {}


class PaymentProviderPlugin(BasePlugin):
    """
    Abstract base class for payment provider plugins.

    Payment providers (Stripe, PayPal, etc.) must inherit from this class.
    """

    @abstractmethod
    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        subscription_id: UUID,
        user_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentResult:
        """
        Create payment intent/session.

        Args:
            amount: Payment amount
            currency: Currency code (ISO 4217)
            subscription_id: Subscription UUID
            user_id: User UUID
            metadata: Optional metadata

        Returns:
            PaymentResult with transaction details
        """
        pass

    @abstractmethod
    def process_payment(
        self,
        payment_intent_id: str,
        payment_method: str,
    ) -> PaymentResult:
        """
        Process payment with given method.

        Args:
            payment_intent_id: Payment intent/session ID
            payment_method: Payment method identifier

        Returns:
            PaymentResult with status
        """
        pass

    @abstractmethod
    def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
    ) -> PaymentResult:
        """
        Refund a payment.

        Args:
            transaction_id: Original transaction ID
            amount: Optional partial refund amount (None = full refund)

        Returns:
            PaymentResult with refund status
        """
        pass

    @abstractmethod
    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Webhook payload
            signature: Webhook signature header

        Returns:
            True if signature is valid
        """
        pass

    @abstractmethod
    def handle_webhook(
        self,
        payload: Dict[str, Any],
    ) -> None:
        """
        Handle webhook event from payment provider.

        Args:
            payload: Parsed webhook payload
        """
        pass
