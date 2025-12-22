"""Mock payment provider plugin for testing."""
from typing import Dict, Any, Optional
from decimal import Decimal
from uuid import UUID, uuid4
from src.plugins.payment_provider import (
    PaymentProviderPlugin,
    PaymentResult,
    PaymentStatus,
)
from src.plugins.base import PluginMetadata


class MockPaymentPlugin(PaymentProviderPlugin):
    """
    Mock payment provider plugin for testing.

    Always succeeds unless configured to fail.
    """

    def __init__(self):
        super().__init__()
        self._should_fail = False
        self._transactions: Dict[str, Dict] = {}

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="mock_payment",
            version="1.0.0",
            author="VBWD Team",
            description="Mock payment provider for testing",
            dependencies=[],
        )

    def set_should_fail(self, should_fail: bool) -> None:
        """Configure whether payment should fail."""
        self._should_fail = should_fail

    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str,
        subscription_id: UUID,
        user_id: UUID,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentResult:
        """Create mock payment intent."""
        if self._should_fail:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                error_message="Mock payment failure",
            )

        transaction_id = f"mock_pi_{uuid4().hex[:16]}"

        self._transactions[transaction_id] = {
            "amount": amount,
            "currency": currency,
            "subscription_id": str(subscription_id),
            "user_id": str(user_id),
            "status": "created",
            "metadata": metadata or {},
        }

        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            status=PaymentStatus.PENDING,
            metadata={
                "client_secret": f"{transaction_id}_secret",
            },
        )

    def process_payment(
        self,
        payment_intent_id: str,
        payment_method: str,
    ) -> PaymentResult:
        """Process mock payment."""
        if payment_intent_id not in self._transactions:
            return PaymentResult(
                success=False,
                status=PaymentStatus.FAILED,
                error_message="Payment intent not found",
            )

        if self._should_fail:
            self._transactions[payment_intent_id]["status"] = "failed"
            return PaymentResult(
                success=False,
                transaction_id=payment_intent_id,
                status=PaymentStatus.FAILED,
                error_message="Mock payment failure",
            )

        self._transactions[payment_intent_id]["status"] = "succeeded"
        self._transactions[payment_intent_id]["payment_method"] = payment_method

        return PaymentResult(
            success=True,
            transaction_id=payment_intent_id,
            status=PaymentStatus.COMPLETED,
            metadata={"payment_method": payment_method},
        )

    def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
    ) -> PaymentResult:
        """Create mock refund."""
        if transaction_id not in self._transactions:
            return PaymentResult(
                success=False,
                error_message="Transaction not found",
            )

        if self._should_fail:
            return PaymentResult(
                success=False,
                error_message="Mock refund failure",
            )

        refund_id = f"mock_ref_{uuid4().hex[:16]}"
        refund_amount = amount or self._transactions[transaction_id]["amount"]

        self._transactions[transaction_id]["refunded"] = True
        self._transactions[transaction_id]["refund_amount"] = refund_amount

        return PaymentResult(
            success=True,
            transaction_id=refund_id,
            status=PaymentStatus.REFUNDED,
            metadata={
                "refund_amount": str(refund_amount),
                "original_transaction": transaction_id,
            },
        )

    def verify_webhook(
        self,
        payload: bytes,
        signature: str,
    ) -> bool:
        """Verify mock webhook signature."""
        # For testing, accept a specific signature
        expected_signature = self.get_config("webhook_secret", "test_secret")
        return signature == expected_signature

    def handle_webhook(
        self,
        payload: Dict[str, Any],
    ) -> None:
        """Handle mock webhook event."""
        event_type = payload.get("type")

        if event_type == "payment_intent.succeeded":
            intent_id = payload.get("data", {}).get("id")
            if intent_id and intent_id in self._transactions:
                self._transactions[intent_id]["status"] = "succeeded"

        elif event_type == "payment_intent.failed":
            intent_id = payload.get("data", {}).get("id")
            if intent_id and intent_id in self._transactions:
                self._transactions[intent_id]["status"] = "failed"
