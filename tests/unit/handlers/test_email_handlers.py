"""Tests for email-integrated event handlers."""
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime

from src.events.user_events import UserCreatedEvent
from src.events.subscription_events import (
    SubscriptionActivatedEvent,
    SubscriptionCancelledEvent,
    PaymentCompletedEvent,
    PaymentFailedEvent,
)
from src.services.email_service import EmailResult


class TestUserCreatedHandlerWithEmail:
    """Tests for UserCreatedHandler with email integration."""

    def test_user_created_sends_welcome_email(self):
        """UserCreatedHandler sends welcome email on user creation."""
        from src.handlers.user_handlers import UserCreatedHandler

        # Mock email service
        mock_email_service = MagicMock()
        mock_email_service.send_welcome_email.return_value = EmailResult(success=True)

        # Create handler with email service
        handler = UserCreatedHandler(email_service=mock_email_service)

        # Create event
        event = UserCreatedEvent(
            user_id=uuid4(), email="newuser@example.com", role="user", first_name="John"
        )

        # Handle event
        result = handler.handle(event)

        # Assert email was sent
        assert result.success is True
        mock_email_service.send_welcome_email.assert_called_once_with(
            to_email="newuser@example.com", first_name="John"
        )

    def test_user_created_handles_email_failure(self):
        """UserCreatedHandler handles email failure gracefully."""
        from src.handlers.user_handlers import UserCreatedHandler

        # Mock email service that fails
        mock_email_service = MagicMock()
        mock_email_service.send_welcome_email.return_value = EmailResult(
            success=False, error="SMTP error"
        )

        handler = UserCreatedHandler(email_service=mock_email_service)

        event = UserCreatedEvent(
            user_id=uuid4(), email="newuser@example.com", role="user"
        )

        # Should still succeed even if email fails
        result = handler.handle(event)

        assert result.success is True
        assert result.data.get("email_sent") is False


class TestSubscriptionActivatedHandlerWithEmail:
    """Tests for SubscriptionActivatedHandler with email integration."""

    def test_subscription_activated_sends_email(self):
        """SubscriptionActivatedHandler sends activation email."""
        from src.handlers.subscription_handlers import SubscriptionActivatedHandler

        mock_email_service = MagicMock()
        mock_email_service.send_subscription_activated.return_value = EmailResult(
            success=True
        )

        handler = SubscriptionActivatedHandler(email_service=mock_email_service)

        event = SubscriptionActivatedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            plan_id=uuid4(),
            plan_name="Premium",
            user_email="user@example.com",
            first_name="John",
            expires_at=datetime(2025, 12, 31),
        )

        result = handler.handle(event)

        assert result.success is True
        mock_email_service.send_subscription_activated.assert_called_once()


class TestSubscriptionCancelledHandlerWithEmail:
    """Tests for SubscriptionCancelledHandler with email integration."""

    def test_subscription_cancelled_sends_email(self):
        """SubscriptionCancelledHandler sends cancellation email."""
        from src.handlers.subscription_handlers import SubscriptionCancelledHandler

        mock_email_service = MagicMock()
        mock_email_service.send_subscription_cancelled.return_value = EmailResult(
            success=True
        )

        handler = SubscriptionCancelledHandler(email_service=mock_email_service)

        event = SubscriptionCancelledEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            plan_name="Premium",
            user_email="user@example.com",
            first_name="John",
        )

        result = handler.handle(event)

        assert result.success is True
        mock_email_service.send_subscription_cancelled.assert_called_once()


class TestPaymentCompletedHandlerWithEmail:
    """Tests for PaymentCompletedHandler with email integration."""

    def test_payment_completed_sends_receipt(self):
        """PaymentCompletedHandler sends payment receipt email."""
        from src.handlers.subscription_handlers import PaymentCompletedHandler

        mock_email_service = MagicMock()
        mock_email_service.send_payment_receipt.return_value = EmailResult(success=True)

        handler = PaymentCompletedHandler(email_service=mock_email_service)

        event = PaymentCompletedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            transaction_id="txn_123",
            amount="99.99",
            currency="EUR",
            invoice_number="INV-2025-001",
            user_email="user@example.com",
            first_name="John",
        )

        result = handler.handle(event)

        assert result.success is True
        mock_email_service.send_payment_receipt.assert_called_once()


class TestPaymentFailedHandlerWithEmail:
    """Tests for PaymentFailedHandler with email integration."""

    def test_payment_failed_sends_notification(self):
        """PaymentFailedHandler sends payment failure notification."""
        from src.handlers.subscription_handlers import PaymentFailedHandler

        mock_email_service = MagicMock()
        mock_email_service.send_payment_failed.return_value = EmailResult(success=True)

        handler = PaymentFailedHandler(email_service=mock_email_service)

        event = PaymentFailedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            error_message="Card declined",
            plan_name="Premium",
            user_email="user@example.com",
            first_name="John",
            retry_url="https://vbwd.com/retry",
        )

        result = handler.handle(event)

        assert result.success is True
        mock_email_service.send_payment_failed.assert_called_once()
