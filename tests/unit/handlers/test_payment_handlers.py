"""Tests for payment handlers and events (Sprint 18)."""
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4


class TestCheckoutInitiatedEvent:
    """Tests for CheckoutInitiatedEvent."""

    def test_event_has_user_id(self):
        """CheckoutInitiatedEvent has user_id field."""
        from src.events.payment_events import CheckoutInitiatedEvent

        user_id = uuid4()
        event = CheckoutInitiatedEvent(
            user_id=user_id, tarif_plan_id=uuid4(), provider="stripe"
        )

        assert event.user_id == user_id

    def test_event_has_tarif_plan_id(self):
        """CheckoutInitiatedEvent has tarif_plan_id field."""
        from src.events.payment_events import CheckoutInitiatedEvent

        plan_id = uuid4()
        event = CheckoutInitiatedEvent(
            user_id=uuid4(), tarif_plan_id=plan_id, provider="stripe"
        )

        assert event.tarif_plan_id == plan_id

    def test_event_has_provider(self):
        """CheckoutInitiatedEvent has provider field."""
        from src.events.payment_events import CheckoutInitiatedEvent

        event = CheckoutInitiatedEvent(
            user_id=uuid4(), tarif_plan_id=uuid4(), provider="paypal"
        )

        assert event.provider == "paypal"

    def test_event_has_name(self):
        """CheckoutInitiatedEvent has correct name."""
        from src.events.payment_events import CheckoutInitiatedEvent

        event = CheckoutInitiatedEvent(
            user_id=uuid4(), tarif_plan_id=uuid4(), provider="stripe"
        )

        assert event.name == "checkout.initiated"

    def test_event_has_optional_urls(self):
        """CheckoutInitiatedEvent has optional return/cancel URLs."""
        from src.events.payment_events import CheckoutInitiatedEvent

        event = CheckoutInitiatedEvent(
            user_id=uuid4(),
            tarif_plan_id=uuid4(),
            provider="stripe",
            return_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )

        assert event.return_url == "https://example.com/success"
        assert event.cancel_url == "https://example.com/cancel"


class TestPaymentCapturedEvent:
    """Tests for PaymentCapturedEvent."""

    def test_event_has_subscription_id(self):
        """PaymentCapturedEvent has subscription_id."""
        from src.events.payment_events import PaymentCapturedEvent

        sub_id = uuid4()
        event = PaymentCapturedEvent(
            subscription_id=sub_id,
            user_id=uuid4(),
            transaction_id="pi_123",
            amount=Decimal("29.99"),
            currency="USD",
            provider="stripe",
        )

        assert event.subscription_id == sub_id

    def test_event_has_transaction_data(self):
        """PaymentCapturedEvent has transaction data."""
        from src.events.payment_events import PaymentCapturedEvent

        event = PaymentCapturedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            transaction_id="pi_test_123",
            amount=Decimal("49.99"),
            currency="EUR",
            provider="stripe",
        )

        assert event.transaction_id == "pi_test_123"
        assert event.amount == Decimal("49.99")
        assert event.currency == "EUR"

    def test_event_has_name(self):
        """PaymentCapturedEvent has correct name."""
        from src.events.payment_events import PaymentCapturedEvent

        event = PaymentCapturedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            transaction_id="pi_123",
            amount=Decimal("29.99"),
            currency="USD",
            provider="stripe",
        )

        assert event.name == "payment.captured"


class TestPaymentFailedEvent:
    """Tests for PaymentFailedEvent."""

    def test_event_has_error_info(self):
        """PaymentFailedEvent has error info."""
        from src.events.payment_events import PaymentFailedEvent

        event = PaymentFailedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            error_code="card_declined",
            error_message="Your card was declined.",
            provider="stripe",
        )

        assert event.error_code == "card_declined"
        assert event.error_message == "Your card was declined."

    def test_event_has_name(self):
        """PaymentFailedEvent has correct name."""
        from src.events.payment_events import PaymentFailedEvent

        event = PaymentFailedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            error_code="card_declined",
            error_message="Declined",
            provider="stripe",
        )

        assert event.name == "payment.failed"


class TestRefundRequestedEvent:
    """Tests for RefundRequestedEvent."""

    def test_event_has_transaction_id(self):
        """RefundRequestedEvent has transaction_id."""
        from src.events.payment_events import RefundRequestedEvent

        event = RefundRequestedEvent(
            transaction_id="pi_123",
            subscription_id=uuid4(),
            amount=Decimal("15.00"),
            reason="Customer request",
        )

        assert event.transaction_id == "pi_123"

    def test_event_has_optional_amount(self):
        """RefundRequestedEvent has optional amount for partial refund."""
        from src.events.payment_events import RefundRequestedEvent

        event = RefundRequestedEvent(
            transaction_id="pi_123", subscription_id=uuid4(), reason="Partial refund"
        )

        assert event.amount is None

    def test_event_has_name(self):
        """RefundRequestedEvent has correct name."""
        from src.events.payment_events import RefundRequestedEvent

        event = RefundRequestedEvent(
            transaction_id="pi_123", subscription_id=uuid4(), reason="Refund"
        )

        assert event.name == "refund.requested"


class TestCheckoutInitiatedHandler:
    """Tests for CheckoutInitiatedHandler."""

    def test_handler_has_handled_event_class(self):
        """Handler declares handled event class."""
        from src.handlers.payment_handlers import CheckoutInitiatedHandler

        assert (
            CheckoutInitiatedHandler.get_handled_event_class() == "checkout.initiated"
        )

    def test_handler_can_handle_checkout_event(self):
        """Handler can handle CheckoutInitiatedEvent."""
        from src.handlers.payment_handlers import CheckoutInitiatedHandler
        from src.events.payment_events import CheckoutInitiatedEvent

        handler = CheckoutInitiatedHandler(sdk_registry=Mock())
        event = CheckoutInitiatedEvent(
            user_id=uuid4(), tarif_plan_id=uuid4(), provider="mock"
        )

        assert handler.can_handle(event) is True

    def test_handler_calls_sdk_adapter(self):
        """Handler uses SDK adapter to create payment intent."""
        from src.handlers.payment_handlers import CheckoutInitiatedHandler
        from src.events.payment_events import CheckoutInitiatedEvent
        from src.sdk.interface import SDKResponse

        mock_adapter = Mock()
        mock_adapter.create_payment_intent.return_value = SDKResponse(
            success=True,
            data={"payment_intent_id": "pi_test", "client_secret": "cs_test"},
        )

        mock_registry = Mock()
        mock_registry.get.return_value = mock_adapter

        handler = CheckoutInitiatedHandler(sdk_registry=mock_registry)
        event = CheckoutInitiatedEvent(
            user_id=uuid4(),
            tarif_plan_id=uuid4(),
            provider="mock",
            amount=Decimal("29.99"),
            currency="USD",
        )

        result = handler.handle(event)

        mock_registry.get.assert_called_once_with("mock")
        mock_adapter.create_payment_intent.assert_called_once()
        assert result.success is True

    def test_handler_returns_checkout_url(self):
        """Handler returns checkout URL in result."""
        from src.handlers.payment_handlers import CheckoutInitiatedHandler
        from src.events.payment_events import CheckoutInitiatedEvent
        from src.sdk.interface import SDKResponse

        mock_adapter = Mock()
        mock_adapter.create_payment_intent.return_value = SDKResponse(
            success=True,
            data={"payment_intent_id": "pi_test", "client_secret": "cs_test_secret"},
        )

        mock_registry = Mock()
        mock_registry.get.return_value = mock_adapter

        handler = CheckoutInitiatedHandler(sdk_registry=mock_registry)
        event = CheckoutInitiatedEvent(
            user_id=uuid4(),
            tarif_plan_id=uuid4(),
            provider="mock",
            amount=Decimal("29.99"),
            currency="USD",
        )

        result = handler.handle(event)

        assert "client_secret" in result.data or "checkout_url" in result.data

    def test_handler_returns_error_on_sdk_failure(self):
        """Handler returns error when SDK fails."""
        from src.handlers.payment_handlers import CheckoutInitiatedHandler
        from src.events.payment_events import CheckoutInitiatedEvent
        from src.sdk.interface import SDKResponse

        mock_adapter = Mock()
        mock_adapter.create_payment_intent.return_value = SDKResponse(
            success=False, error="Card declined"
        )

        mock_registry = Mock()
        mock_registry.get.return_value = mock_adapter

        handler = CheckoutInitiatedHandler(sdk_registry=mock_registry)
        event = CheckoutInitiatedEvent(
            user_id=uuid4(),
            tarif_plan_id=uuid4(),
            provider="mock",
            amount=Decimal("29.99"),
            currency="USD",
        )

        result = handler.handle(event)

        assert result.success is False
        assert result.error is not None

    def test_handler_returns_error_for_unknown_provider(self):
        """Handler returns error for unknown provider."""
        from src.handlers.payment_handlers import CheckoutInitiatedHandler
        from src.events.payment_events import CheckoutInitiatedEvent

        mock_registry = Mock()
        mock_registry.get.side_effect = ValueError("Unknown provider")

        handler = CheckoutInitiatedHandler(sdk_registry=mock_registry)
        event = CheckoutInitiatedEvent(
            user_id=uuid4(),
            tarif_plan_id=uuid4(),
            provider="unknown",
            amount=Decimal("29.99"),
            currency="USD",
        )

        result = handler.handle(event)

        assert result.success is False


class TestPaymentCapturedHandler:
    """Tests for PaymentCapturedHandler."""

    def test_handler_has_handled_event_class(self):
        """Handler declares handled event class."""
        from src.handlers.payment_handlers import PaymentCapturedHandler

        assert PaymentCapturedHandler.get_handled_event_class() == "payment.captured"

    def test_handler_can_handle_payment_captured_event(self):
        """Handler can handle PaymentCapturedEvent."""
        from src.handlers.payment_handlers import PaymentCapturedHandler
        from src.events.payment_events import PaymentCapturedEvent

        handler = PaymentCapturedHandler()
        event = PaymentCapturedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            transaction_id="pi_123",
            amount=Decimal("29.99"),
            currency="USD",
            provider="stripe",
        )

        assert handler.can_handle(event) is True

    def test_handler_returns_success(self):
        """Handler returns success for valid event."""
        from src.handlers.payment_handlers import PaymentCapturedHandler
        from src.events.payment_events import PaymentCapturedEvent

        handler = PaymentCapturedHandler()
        event = PaymentCapturedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            transaction_id="pi_123",
            amount=Decimal("29.99"),
            currency="USD",
            provider="stripe",
        )

        result = handler.handle(event)

        assert result.success is True

    def test_handler_tracks_processed_events(self):
        """Handler tracks all processed events."""
        from src.handlers.payment_handlers import PaymentCapturedHandler
        from src.events.payment_events import PaymentCapturedEvent

        handler = PaymentCapturedHandler()
        event1 = PaymentCapturedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            transaction_id="pi_1",
            amount=Decimal("29.99"),
            currency="USD",
            provider="stripe",
        )
        event2 = PaymentCapturedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            transaction_id="pi_2",
            amount=Decimal("49.99"),
            currency="USD",
            provider="stripe",
        )

        handler.handle(event1)
        handler.handle(event2)

        assert len(handler.processed_events) == 2


class TestPaymentFailedHandler:
    """Tests for PaymentFailedHandler."""

    def test_handler_has_handled_event_class(self):
        """Handler declares handled event class."""
        from src.handlers.payment_handlers import PaymentFailedHandler

        assert PaymentFailedHandler.get_handled_event_class() == "payment.failed"

    def test_handler_can_handle_payment_failed_event(self):
        """Handler can handle PaymentFailedEvent."""
        from src.handlers.payment_handlers import PaymentFailedHandler
        from src.events.payment_events import PaymentFailedEvent

        handler = PaymentFailedHandler()
        event = PaymentFailedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            error_code="card_declined",
            error_message="Declined",
            provider="stripe",
        )

        assert handler.can_handle(event) is True

    def test_handler_returns_success(self):
        """Handler returns success (event processed, even if payment failed)."""
        from src.handlers.payment_handlers import PaymentFailedHandler
        from src.events.payment_events import PaymentFailedEvent

        handler = PaymentFailedHandler()
        event = PaymentFailedEvent(
            subscription_id=uuid4(),
            user_id=uuid4(),
            error_code="card_declined",
            error_message="Declined",
            provider="stripe",
        )

        result = handler.handle(event)

        assert result.success is True


class TestRefundRequestedHandler:
    """Tests for RefundRequestedHandler."""

    def test_handler_has_handled_event_class(self):
        """Handler declares handled event class."""
        from src.handlers.payment_handlers import RefundRequestedHandler

        assert RefundRequestedHandler.get_handled_event_class() == "refund.requested"

    def test_handler_calls_sdk_refund(self):
        """Handler calls SDK adapter refund_payment."""
        from src.handlers.payment_handlers import RefundRequestedHandler
        from src.events.payment_events import RefundRequestedEvent
        from src.sdk.interface import SDKResponse

        mock_adapter = Mock()
        mock_adapter.refund_payment.return_value = SDKResponse(
            success=True, data={"refund_id": "re_test"}
        )

        mock_registry = Mock()
        mock_registry.get.return_value = mock_adapter

        handler = RefundRequestedHandler(sdk_registry=mock_registry)
        event = RefundRequestedEvent(
            transaction_id="pi_123",
            subscription_id=uuid4(),
            amount=Decimal("15.00"),
            reason="Customer request",
            provider="mock",
        )

        result = handler.handle(event)

        mock_adapter.refund_payment.assert_called_once()
        assert result.success is True

    def test_handler_returns_error_on_refund_failure(self):
        """Handler returns error when refund fails."""
        from src.handlers.payment_handlers import RefundRequestedHandler
        from src.events.payment_events import RefundRequestedEvent
        from src.sdk.interface import SDKResponse

        mock_adapter = Mock()
        mock_adapter.refund_payment.return_value = SDKResponse(
            success=False, error="Refund failed"
        )

        mock_registry = Mock()
        mock_registry.get.return_value = mock_adapter

        handler = RefundRequestedHandler(sdk_registry=mock_registry)
        event = RefundRequestedEvent(
            transaction_id="pi_123",
            subscription_id=uuid4(),
            amount=Decimal("15.00"),
            reason="Customer request",
            provider="mock",
        )

        result = handler.handle(event)

        assert result.success is False
