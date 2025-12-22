"""Tests for subscription event handlers."""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from src.handlers.subscription_handlers import (
    SubscriptionActivatedHandler,
    SubscriptionCancelledHandler,
    PaymentCompletedHandler,
    PaymentFailedHandler,
)
from src.events.subscription_events import (
    SubscriptionActivatedEvent,
    SubscriptionCancelledEvent,
    PaymentCompletedEvent,
    PaymentFailedEvent,
)


class TestSubscriptionActivatedHandler:
    """Test cases for SubscriptionActivatedHandler."""

    @pytest.fixture
    def handler(self):
        """Create SubscriptionActivatedHandler."""
        return SubscriptionActivatedHandler()

    def test_can_handle_returns_true_for_subscription_activated_event(self, handler):
        """can_handle should return True for SubscriptionActivatedEvent."""
        event = SubscriptionActivatedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            tarif_plan_id=uuid4(),
            started_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        assert handler.can_handle(event) is True

    def test_handle_processes_activation_event(self, handler):
        """handle should process SubscriptionActivatedEvent successfully."""
        subscription_id = uuid4()
        user_id = uuid4()
        event = SubscriptionActivatedEvent(
            subscription_id=subscription_id,
            user_id=user_id,
            tarif_plan_id=uuid4(),
            started_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        result = handler.handle(event)

        assert result.success is True
        assert result.data["subscription_id"] == str(subscription_id)
        assert result.data["user_id"] == str(user_id)
        assert len(handler.handled_events) == 1


class TestSubscriptionCancelledHandler:
    """Test cases for SubscriptionCancelledHandler."""

    @pytest.fixture
    def handler(self):
        """Create SubscriptionCancelledHandler."""
        return SubscriptionCancelledHandler()

    def test_can_handle_returns_true_for_subscription_cancelled_event(self, handler):
        """can_handle should return True for SubscriptionCancelledEvent."""
        event = SubscriptionCancelledEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            cancelled_by=uuid4()
        )

        assert handler.can_handle(event) is True

    def test_handle_processes_cancellation_event(self, handler):
        """handle should process SubscriptionCancelledEvent successfully."""
        subscription_id = uuid4()
        event = SubscriptionCancelledEvent(
            subscription_id=subscription_id,
            user_id=uuid4(),
            cancelled_by=uuid4(),
            reason="User request"
        )

        result = handler.handle(event)

        assert result.success is True
        assert result.data["subscription_id"] == str(subscription_id)
        assert len(handler.handled_events) == 1


class TestPaymentCompletedHandler:
    """Test cases for PaymentCompletedHandler."""

    @pytest.fixture
    def handler(self):
        """Create PaymentCompletedHandler."""
        return PaymentCompletedHandler()

    def test_can_handle_returns_true_for_payment_completed_event(self, handler):
        """can_handle should return True for PaymentCompletedEvent."""
        event = PaymentCompletedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            transaction_id="tx_123",
            amount=Decimal("29.99"),
            currency="USD"
        )

        assert handler.can_handle(event) is True

    def test_handle_processes_payment_completed_event(self, handler):
        """handle should process PaymentCompletedEvent successfully."""
        subscription_id = uuid4()
        event = PaymentCompletedEvent(
            subscription_id=subscription_id,
            user_id=uuid4(),
            transaction_id="tx_123",
            amount=Decimal("29.99"),
            currency="USD"
        )

        result = handler.handle(event)

        assert result.success is True
        assert result.data["subscription_id"] == str(subscription_id)
        assert result.data["transaction_id"] == "tx_123"
        assert len(handler.handled_events) == 1

    def test_handle_activates_subscription_with_service(self):
        """handle should activate subscription if service provided."""
        from unittest.mock import Mock

        mock_service = Mock()
        handler = PaymentCompletedHandler(subscription_service=mock_service)

        subscription_id = uuid4()
        event = PaymentCompletedEvent(
            subscription_id=subscription_id,
            user_id=uuid4(),
            transaction_id="tx_123",
            amount=Decimal("29.99"),
            currency="USD"
        )

        result = handler.handle(event)

        assert result.success is True
        mock_service.activate_subscription.assert_called_once_with(subscription_id)


class TestPaymentFailedHandler:
    """Test cases for PaymentFailedHandler."""

    @pytest.fixture
    def handler(self):
        """Create PaymentFailedHandler."""
        return PaymentFailedHandler()

    def test_can_handle_returns_true_for_payment_failed_event(self, handler):
        """can_handle should return True for PaymentFailedEvent."""
        event = PaymentFailedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            error_message="Insufficient funds"
        )

        assert handler.can_handle(event) is True

    def test_handle_processes_payment_failed_event(self, handler):
        """handle should process PaymentFailedEvent successfully."""
        subscription_id = uuid4()
        event = PaymentFailedEvent(
            subscription_id=subscription_id,
            user_id=uuid4(),
            error_message="Insufficient funds"
        )

        result = handler.handle(event)

        assert result.success is True
        assert result.data["subscription_id"] == str(subscription_id)
        assert len(handler.handled_events) == 1
