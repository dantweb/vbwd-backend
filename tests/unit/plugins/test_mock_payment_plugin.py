"""Tests for MockPaymentPlugin."""
import pytest
from decimal import Decimal
from uuid import uuid4
from src.plugins.providers.mock_payment_plugin import MockPaymentPlugin
from src.plugins.payment_provider import PaymentStatus


class TestMockPaymentPluginCreation:
    """Test cases for creating payment intents."""

    @pytest.fixture
    def plugin(self):
        """Create MockPaymentPlugin."""
        plugin = MockPaymentPlugin()
        plugin.initialize()
        return plugin

    def test_create_payment_intent_success(self, plugin):
        """create_payment_intent should create payment intent."""
        subscription_id = uuid4()
        user_id = uuid4()

        result = plugin.create_payment_intent(
            amount=Decimal("29.99"),
            currency="USD",
            subscription_id=subscription_id,
            user_id=user_id,
        )

        assert result.success is True
        assert result.transaction_id is not None
        assert result.status == PaymentStatus.PENDING
        assert "client_secret" in result.metadata

    def test_create_payment_intent_with_metadata(self, plugin):
        """create_payment_intent should accept metadata."""
        subscription_id = uuid4()
        user_id = uuid4()
        metadata = {"plan": "premium"}

        result = plugin.create_payment_intent(
            amount=Decimal("99.99"),
            currency="EUR",
            subscription_id=subscription_id,
            user_id=user_id,
            metadata=metadata,
        )

        assert result.success is True
        assert result.transaction_id is not None

    def test_create_payment_intent_failure(self, plugin):
        """create_payment_intent should fail when configured."""
        plugin.set_should_fail(True)

        subscription_id = uuid4()
        user_id = uuid4()

        result = plugin.create_payment_intent(
            amount=Decimal("29.99"),
            currency="USD",
            subscription_id=subscription_id,
            user_id=user_id,
        )

        assert result.success is False
        assert result.status == PaymentStatus.FAILED
        assert result.error_message is not None


class TestMockPaymentPluginProcessing:
    """Test cases for processing payments."""

    @pytest.fixture
    def plugin(self):
        """Create MockPaymentPlugin."""
        plugin = MockPaymentPlugin()
        plugin.initialize()
        return plugin

    def test_process_payment_success(self, plugin):
        """process_payment should complete payment."""
        subscription_id = uuid4()
        user_id = uuid4()

        # Create intent first
        create_result = plugin.create_payment_intent(
            amount=Decimal("29.99"),
            currency="USD",
            subscription_id=subscription_id,
            user_id=user_id,
        )

        # Process payment
        result = plugin.process_payment(
            payment_intent_id=create_result.transaction_id,
            payment_method="card",
        )

        assert result.success is True
        assert result.status == PaymentStatus.COMPLETED
        assert result.transaction_id == create_result.transaction_id

    def test_process_payment_not_found(self, plugin):
        """process_payment should fail for invalid intent."""
        result = plugin.process_payment(
            payment_intent_id="invalid_id",
            payment_method="card",
        )

        assert result.success is False
        assert result.status == PaymentStatus.FAILED

    def test_process_payment_failure(self, plugin):
        """process_payment should fail when configured."""
        subscription_id = uuid4()
        user_id = uuid4()

        # Create intent
        create_result = plugin.create_payment_intent(
            amount=Decimal("29.99"),
            currency="USD",
            subscription_id=subscription_id,
            user_id=user_id,
        )

        # Configure to fail
        plugin.set_should_fail(True)

        # Process payment
        result = plugin.process_payment(
            payment_intent_id=create_result.transaction_id,
            payment_method="card",
        )

        assert result.success is False
        assert result.status == PaymentStatus.FAILED


class TestMockPaymentPluginRefunds:
    """Test cases for refunds."""

    @pytest.fixture
    def plugin(self):
        """Create MockPaymentPlugin."""
        plugin = MockPaymentPlugin()
        plugin.initialize()
        return plugin

    def test_refund_payment_success(self, plugin):
        """refund_payment should refund transaction."""
        subscription_id = uuid4()
        user_id = uuid4()

        # Create and process payment
        create_result = plugin.create_payment_intent(
            amount=Decimal("29.99"),
            currency="USD",
            subscription_id=subscription_id,
            user_id=user_id,
        )

        plugin.process_payment(
            payment_intent_id=create_result.transaction_id,
            payment_method="card",
        )

        # Refund
        result = plugin.refund_payment(
            transaction_id=create_result.transaction_id,
        )

        assert result.success is True
        assert result.status == PaymentStatus.REFUNDED
        assert result.transaction_id is not None

    def test_refund_payment_partial(self, plugin):
        """refund_payment should handle partial refunds."""
        subscription_id = uuid4()
        user_id = uuid4()

        # Create and process payment
        create_result = plugin.create_payment_intent(
            amount=Decimal("100.00"),
            currency="USD",
            subscription_id=subscription_id,
            user_id=user_id,
        )

        plugin.process_payment(
            payment_intent_id=create_result.transaction_id,
            payment_method="card",
        )

        # Partial refund
        result = plugin.refund_payment(
            transaction_id=create_result.transaction_id,
            amount=Decimal("50.00"),
        )

        assert result.success is True
        assert result.metadata["refund_amount"] == "50.00"

    def test_refund_payment_not_found(self, plugin):
        """refund_payment should fail for invalid transaction."""
        result = plugin.refund_payment(
            transaction_id="invalid_id",
        )

        assert result.success is False


class TestMockPaymentPluginWebhooks:
    """Test cases for webhook handling."""

    @pytest.fixture
    def plugin(self):
        """Create MockPaymentPlugin."""
        plugin = MockPaymentPlugin()
        plugin.initialize({"webhook_secret": "test_secret"})
        return plugin

    def test_verify_webhook_valid(self, plugin):
        """verify_webhook should accept valid signature."""
        payload = b'{"type": "payment_intent.succeeded"}'
        signature = "test_secret"

        result = plugin.verify_webhook(payload, signature)

        assert result is True

    def test_verify_webhook_invalid(self, plugin):
        """verify_webhook should reject invalid signature."""
        payload = b'{"type": "payment_intent.succeeded"}'
        signature = "wrong_secret"

        result = plugin.verify_webhook(payload, signature)

        assert result is False

    def test_handle_webhook_payment_succeeded(self, plugin):
        """handle_webhook should process payment_intent.succeeded."""
        subscription_id = uuid4()
        user_id = uuid4()

        # Create intent
        create_result = plugin.create_payment_intent(
            amount=Decimal("29.99"),
            currency="USD",
            subscription_id=subscription_id,
            user_id=user_id,
        )

        # Handle webhook
        payload = {
            "type": "payment_intent.succeeded",
            "data": {"id": create_result.transaction_id},
        }

        plugin.handle_webhook(payload)

        # Verify internal state updated
        assert plugin._transactions[create_result.transaction_id]["status"] == "succeeded"

    def test_handle_webhook_payment_failed(self, plugin):
        """handle_webhook should process payment_intent.failed."""
        subscription_id = uuid4()
        user_id = uuid4()

        # Create intent
        create_result = plugin.create_payment_intent(
            amount=Decimal("29.99"),
            currency="USD",
            subscription_id=subscription_id,
            user_id=user_id,
        )

        # Handle webhook
        payload = {
            "type": "payment_intent.failed",
            "data": {"id": create_result.transaction_id},
        }

        plugin.handle_webhook(payload)

        # Verify internal state updated
        assert plugin._transactions[create_result.transaction_id]["status"] == "failed"
