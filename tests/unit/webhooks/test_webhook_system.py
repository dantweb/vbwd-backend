"""Tests for webhook system (Sprint 15)."""
from decimal import Decimal
from uuid import uuid4


class TestWebhookStatus:
    """Tests for WebhookStatus enum."""

    def test_webhook_status_has_received(self):
        """WebhookStatus has RECEIVED value."""
        from src.webhooks.enums import WebhookStatus

        assert WebhookStatus.RECEIVED.value == "received"

    def test_webhook_status_has_processing(self):
        """WebhookStatus has PROCESSING value."""
        from src.webhooks.enums import WebhookStatus

        assert WebhookStatus.PROCESSING.value == "processing"

    def test_webhook_status_has_processed(self):
        """WebhookStatus has PROCESSED value."""
        from src.webhooks.enums import WebhookStatus

        assert WebhookStatus.PROCESSED.value == "processed"

    def test_webhook_status_has_failed(self):
        """WebhookStatus has FAILED value."""
        from src.webhooks.enums import WebhookStatus

        assert WebhookStatus.FAILED.value == "failed"

    def test_webhook_status_has_skipped(self):
        """WebhookStatus has SKIPPED value."""
        from src.webhooks.enums import WebhookStatus

        assert WebhookStatus.SKIPPED.value == "skipped"


class TestWebhookEventType:
    """Tests for WebhookEventType enum."""

    def test_event_type_has_payment_succeeded(self):
        """WebhookEventType has PAYMENT_SUCCEEDED."""
        from src.webhooks.enums import WebhookEventType

        assert WebhookEventType.PAYMENT_SUCCEEDED.value == "payment.succeeded"

    def test_event_type_has_payment_failed(self):
        """WebhookEventType has PAYMENT_FAILED."""
        from src.webhooks.enums import WebhookEventType

        assert WebhookEventType.PAYMENT_FAILED.value == "payment.failed"

    def test_event_type_has_subscription_created(self):
        """WebhookEventType has SUBSCRIPTION_CREATED."""
        from src.webhooks.enums import WebhookEventType

        assert WebhookEventType.SUBSCRIPTION_CREATED.value == "subscription.created"

    def test_event_type_has_subscription_updated(self):
        """WebhookEventType has SUBSCRIPTION_UPDATED."""
        from src.webhooks.enums import WebhookEventType

        assert WebhookEventType.SUBSCRIPTION_UPDATED.value == "subscription.updated"

    def test_event_type_has_subscription_cancelled(self):
        """WebhookEventType has SUBSCRIPTION_CANCELLED."""
        from src.webhooks.enums import WebhookEventType

        assert WebhookEventType.SUBSCRIPTION_CANCELLED.value == "subscription.cancelled"

    def test_event_type_has_refund_created(self):
        """WebhookEventType has REFUND_CREATED."""
        from src.webhooks.enums import WebhookEventType

        assert WebhookEventType.REFUND_CREATED.value == "refund.created"

    def test_event_type_has_unknown(self):
        """WebhookEventType has UNKNOWN for unhandled events."""
        from src.webhooks.enums import WebhookEventType

        assert WebhookEventType.UNKNOWN.value == "unknown"


class TestNormalizedWebhookEvent:
    """Tests for NormalizedWebhookEvent DTO."""

    def test_normalized_event_has_provider(self):
        """NormalizedWebhookEvent has provider field."""
        from src.webhooks.dto import NormalizedWebhookEvent
        from src.webhooks.enums import WebhookEventType

        event = NormalizedWebhookEvent(
            provider="stripe",
            event_id="evt_123",
            event_type=WebhookEventType.PAYMENT_SUCCEEDED,
        )

        assert event.provider == "stripe"

    def test_normalized_event_has_event_id(self):
        """NormalizedWebhookEvent has event_id field."""
        from src.webhooks.dto import NormalizedWebhookEvent
        from src.webhooks.enums import WebhookEventType

        event = NormalizedWebhookEvent(
            provider="stripe",
            event_id="evt_123",
            event_type=WebhookEventType.PAYMENT_SUCCEEDED,
        )

        assert event.event_id == "evt_123"

    def test_normalized_event_has_event_type(self):
        """NormalizedWebhookEvent has event_type field."""
        from src.webhooks.dto import NormalizedWebhookEvent
        from src.webhooks.enums import WebhookEventType

        event = NormalizedWebhookEvent(
            provider="stripe",
            event_id="evt_123",
            event_type=WebhookEventType.PAYMENT_SUCCEEDED,
        )

        assert event.event_type == WebhookEventType.PAYMENT_SUCCEEDED

    def test_normalized_event_optional_fields(self):
        """NormalizedWebhookEvent has optional payment fields."""
        from src.webhooks.dto import NormalizedWebhookEvent
        from src.webhooks.enums import WebhookEventType

        user_id = uuid4()
        event = NormalizedWebhookEvent(
            provider="stripe",
            event_id="evt_123",
            event_type=WebhookEventType.PAYMENT_SUCCEEDED,
            payment_intent_id="pi_123",
            amount=Decimal("29.99"),
            currency="USD",
            user_id=user_id,
        )

        assert event.payment_intent_id == "pi_123"
        assert event.amount == Decimal("29.99")
        assert event.currency == "USD"
        assert event.user_id == user_id

    def test_normalized_event_default_metadata(self):
        """NormalizedWebhookEvent has empty default metadata."""
        from src.webhooks.dto import NormalizedWebhookEvent
        from src.webhooks.enums import WebhookEventType

        event = NormalizedWebhookEvent(
            provider="stripe",
            event_id="evt_123",
            event_type=WebhookEventType.PAYMENT_SUCCEEDED,
        )

        assert event.metadata == {}
        assert event.raw_payload == {}


class TestWebhookResult:
    """Tests for WebhookResult dataclass."""

    def test_webhook_result_success(self):
        """WebhookResult for successful processing."""
        from src.webhooks.dto import WebhookResult

        result = WebhookResult(success=True, message="Processed successfully")

        assert result.success is True
        assert result.message == "Processed successfully"
        assert result.error is None

    def test_webhook_result_failure(self):
        """WebhookResult for failed processing."""
        from src.webhooks.dto import WebhookResult

        result = WebhookResult(success=False, error="Signature verification failed")

        assert result.success is False
        assert result.error == "Signature verification failed"

    def test_webhook_result_with_data(self):
        """WebhookResult can include data."""
        from src.webhooks.dto import WebhookResult

        result = WebhookResult(
            success=True, message="Payment processed", data={"payment_id": "pay_123"}
        )

        assert result.data == {"payment_id": "pay_123"}


class TestIWebhookHandler:
    """Tests for IWebhookHandler interface."""

    def test_handler_has_provider_property(self):
        """IWebhookHandler has provider property."""
        from src.webhooks.handlers.base import IWebhookHandler

        assert hasattr(IWebhookHandler, "provider")

    def test_handler_has_verify_signature(self):
        """IWebhookHandler has verify_signature method."""
        from src.webhooks.handlers.base import IWebhookHandler

        assert hasattr(IWebhookHandler, "verify_signature")

    def test_handler_has_parse_event(self):
        """IWebhookHandler has parse_event method."""
        from src.webhooks.handlers.base import IWebhookHandler

        assert hasattr(IWebhookHandler, "parse_event")

    def test_handler_has_handle(self):
        """IWebhookHandler has handle method."""
        from src.webhooks.handlers.base import IWebhookHandler

        assert hasattr(IWebhookHandler, "handle")

    def test_concrete_handler_implements_interface(self):
        """Concrete handler can implement IWebhookHandler."""
        from src.webhooks.handlers.base import IWebhookHandler
        from src.webhooks.dto import NormalizedWebhookEvent, WebhookResult
        from src.webhooks.enums import WebhookEventType

        class TestHandler(IWebhookHandler):
            @property
            def provider(self) -> str:
                return "test"

            def verify_signature(
                self, payload: bytes, signature: str, secret: str
            ) -> bool:
                return True

            def parse_event(self, payload: dict) -> NormalizedWebhookEvent:
                return NormalizedWebhookEvent(
                    provider="test",
                    event_id="evt_test",
                    event_type=WebhookEventType.UNKNOWN,
                )

            def handle(self, event: NormalizedWebhookEvent) -> WebhookResult:
                return WebhookResult(success=True)

        handler = TestHandler()
        assert isinstance(handler, IWebhookHandler)
        assert handler.provider == "test"


class TestMockWebhookHandler:
    """Tests for MockWebhookHandler."""

    def test_mock_handler_implements_interface(self):
        """MockWebhookHandler implements IWebhookHandler."""
        from src.webhooks.handlers.mock import MockWebhookHandler
        from src.webhooks.handlers.base import IWebhookHandler

        handler = MockWebhookHandler()
        assert isinstance(handler, IWebhookHandler)

    def test_mock_handler_provider_name(self):
        """MockWebhookHandler has provider 'mock'."""
        from src.webhooks.handlers.mock import MockWebhookHandler

        handler = MockWebhookHandler()
        assert handler.provider == "mock"

    def test_mock_handler_verify_signature_valid(self):
        """MockWebhookHandler verifies 'valid_signature'."""
        from src.webhooks.handlers.mock import MockWebhookHandler

        handler = MockWebhookHandler()
        result = handler.verify_signature(b"payload", "valid_signature", "secret")

        assert result is True

    def test_mock_handler_verify_signature_invalid(self):
        """MockWebhookHandler rejects other signatures."""
        from src.webhooks.handlers.mock import MockWebhookHandler

        handler = MockWebhookHandler()
        result = handler.verify_signature(b"payload", "bad_signature", "secret")

        assert result is False

    def test_mock_handler_parse_event(self):
        """MockWebhookHandler parses payload to NormalizedWebhookEvent."""
        from src.webhooks.handlers.mock import MockWebhookHandler
        from src.webhooks.enums import WebhookEventType

        handler = MockWebhookHandler()
        payload = {
            "id": "evt_mock_123",
            "type": "payment.succeeded",
            "data": {"payment_intent_id": "pi_123", "amount": 2999, "currency": "usd"},
        }

        event = handler.parse_event(payload)

        assert event.provider == "mock"
        assert event.event_id == "evt_mock_123"
        assert event.event_type == WebhookEventType.PAYMENT_SUCCEEDED
        assert event.payment_intent_id == "pi_123"
        assert event.amount == Decimal("29.99")
        assert event.currency == "USD"

    def test_mock_handler_handle_succeeds(self):
        """MockWebhookHandler handle() returns success."""
        from src.webhooks.handlers.mock import MockWebhookHandler
        from src.webhooks.dto import NormalizedWebhookEvent
        from src.webhooks.enums import WebhookEventType

        handler = MockWebhookHandler()
        event = NormalizedWebhookEvent(
            provider="mock",
            event_id="evt_123",
            event_type=WebhookEventType.PAYMENT_SUCCEEDED,
        )

        result = handler.handle(event)

        assert result.success is True

    def test_mock_handler_can_fail(self):
        """MockWebhookHandler can be configured to fail."""
        from src.webhooks.handlers.mock import MockWebhookHandler
        from src.webhooks.dto import NormalizedWebhookEvent
        from src.webhooks.enums import WebhookEventType

        handler = MockWebhookHandler(should_fail=True)
        event = NormalizedWebhookEvent(
            provider="mock",
            event_id="evt_123",
            event_type=WebhookEventType.PAYMENT_SUCCEEDED,
        )

        result = handler.handle(event)

        assert result.success is False
        assert result.error is not None

    def test_mock_handler_tracks_handled_events(self):
        """MockWebhookHandler tracks all handled events."""
        from src.webhooks.handlers.mock import MockWebhookHandler
        from src.webhooks.dto import NormalizedWebhookEvent
        from src.webhooks.enums import WebhookEventType

        handler = MockWebhookHandler()
        event1 = NormalizedWebhookEvent(
            provider="mock",
            event_id="evt_1",
            event_type=WebhookEventType.PAYMENT_SUCCEEDED,
        )
        event2 = NormalizedWebhookEvent(
            provider="mock",
            event_id="evt_2",
            event_type=WebhookEventType.PAYMENT_FAILED,
        )

        handler.handle(event1)
        handler.handle(event2)

        assert len(handler.handled_events) == 2
        assert handler.handled_events[0].event_id == "evt_1"
        assert handler.handled_events[1].event_id == "evt_2"


class TestWebhookService:
    """Tests for WebhookService."""

    def test_service_rejects_unknown_provider(self):
        """Unknown provider returns error."""
        from src.webhooks.service import WebhookService

        service = WebhookService(handlers={})

        result = service.process(
            provider="unknown", payload=b"{}", signature="sig", headers={}
        )

        assert result.success is False
        assert "unknown" in result.error.lower()

    def test_service_verifies_signature(self):
        """Signature verified before processing."""
        from src.webhooks.service import WebhookService
        from src.webhooks.handlers.mock import MockWebhookHandler

        handler = MockWebhookHandler()
        service = WebhookService(
            handlers={"mock": handler}, webhook_secrets={"mock": "test_secret"}
        )

        result = service.process(
            provider="mock",
            payload=b'{"id": "evt_123", "type": "payment.succeeded", "data": {}}',
            signature="bad_signature",
            headers={},
        )

        assert result.success is False
        assert "signature" in result.error.lower()

    def test_service_processes_valid_webhook(self):
        """Valid webhook is processed successfully."""
        from src.webhooks.service import WebhookService
        from src.webhooks.handlers.mock import MockWebhookHandler

        handler = MockWebhookHandler()
        service = WebhookService(
            handlers={"mock": handler}, webhook_secrets={"mock": "test_secret"}
        )

        result = service.process(
            provider="mock",
            payload=b'{"id": "evt_123", "type": "payment.succeeded", "data": {}}',
            signature="valid_signature",
            headers={},
        )

        assert result.success is True

    def test_service_calls_handler_handle(self):
        """Service calls handler's handle method."""
        from src.webhooks.service import WebhookService
        from src.webhooks.handlers.mock import MockWebhookHandler

        handler = MockWebhookHandler()
        service = WebhookService(
            handlers={"mock": handler}, webhook_secrets={"mock": "test_secret"}
        )

        service.process(
            provider="mock",
            payload=b'{"id": "evt_123", "type": "payment.succeeded", "data": {}}',
            signature="valid_signature",
            headers={},
        )

        assert len(handler.handled_events) == 1
        assert handler.handled_events[0].event_id == "evt_123"

    def test_service_handles_handler_failure(self):
        """Handler failure is returned correctly."""
        from src.webhooks.service import WebhookService
        from src.webhooks.handlers.mock import MockWebhookHandler

        handler = MockWebhookHandler(should_fail=True)
        service = WebhookService(
            handlers={"mock": handler}, webhook_secrets={"mock": "test_secret"}
        )

        result = service.process(
            provider="mock",
            payload=b'{"id": "evt_123", "type": "payment.succeeded", "data": {}}',
            signature="valid_signature",
            headers={},
        )

        assert result.success is False

    def test_service_handles_invalid_json(self):
        """Invalid JSON returns error."""
        from src.webhooks.service import WebhookService
        from src.webhooks.handlers.mock import MockWebhookHandler

        handler = MockWebhookHandler()
        service = WebhookService(
            handlers={"mock": handler}, webhook_secrets={"mock": "test_secret"}
        )

        result = service.process(
            provider="mock",
            payload=b"not valid json",
            signature="valid_signature",
            headers={},
        )

        assert result.success is False
        assert "json" in result.error.lower() or "parse" in result.error.lower()

    def test_service_register_handler(self):
        """Service can register handlers dynamically."""
        from src.webhooks.service import WebhookService
        from src.webhooks.handlers.mock import MockWebhookHandler

        service = WebhookService(handlers={}, webhook_secrets={})
        handler = MockWebhookHandler()

        service.register_handler(handler, webhook_secret="secret")

        assert service.has_handler("mock")

    def test_service_get_handler(self):
        """Service returns registered handler."""
        from src.webhooks.service import WebhookService
        from src.webhooks.handlers.mock import MockWebhookHandler

        handler = MockWebhookHandler()
        service = WebhookService(
            handlers={"mock": handler}, webhook_secrets={"mock": "secret"}
        )

        retrieved = service.get_handler("mock")

        assert retrieved is handler
