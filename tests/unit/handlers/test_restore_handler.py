"""Tests for RefundReversedHandler."""
from unittest.mock import MagicMock
from uuid import uuid4


class TestRefundReversedHandler:
    """Tests for the thin RefundReversedHandler."""

    def test_handler_calls_restore_service(self):
        """Handler delegates to RestoreService.process_restore()."""
        from src.handlers.restore_handler import RefundReversedHandler
        from src.events.payment_events import RefundReversedEvent

        invoice_id = uuid4()
        mock_invoice = MagicMock()
        mock_invoice.id = invoice_id

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.invoice = mock_invoice
        mock_result.items_restored = {
            "subscription": None,
            "token_bundles": [],
            "add_ons": [],
            "tokens_credited": 0,
        }

        # RestoreService is instantiated inside the handler with container
        container = MagicMock()
        handler = RefundReversedHandler(container)

        event = RefundReversedEvent(
            invoice_id=invoice_id,
            reason="stripe_refund_canceled",
        )

        # Patch the RestoreService to return mock result
        from unittest.mock import patch

        with patch("src.handlers.restore_handler.RestoreService") as MockRestoreService:
            mock_service = MagicMock()
            mock_service.process_restore.return_value = mock_result
            MockRestoreService.return_value = mock_service

            result = handler.handle(event)

            MockRestoreService.assert_called_once_with(container)
            mock_service.process_restore.assert_called_once_with(
                invoice_id=invoice_id,
                reason="stripe_refund_canceled",
            )
            assert result.success is True

    def test_handler_returns_error_on_service_failure(self):
        """Handler returns error when RestoreService reports failure."""
        from src.handlers.restore_handler import RefundReversedHandler
        from src.events.payment_events import RefundReversedEvent

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Cannot restore: invoice status is paid, expected refunded"

        container = MagicMock()
        handler = RefundReversedHandler(container)

        event = RefundReversedEvent(
            invoice_id=uuid4(),
            reason="test",
        )

        from unittest.mock import patch

        with patch("src.handlers.restore_handler.RestoreService") as MockRestoreService:
            mock_service = MagicMock()
            mock_service.process_restore.return_value = mock_result
            MockRestoreService.return_value = mock_service

            result = handler.handle(event)

            assert result.success is False
            assert "cannot restore" in result.error.lower()

    def test_handler_returns_success_with_data(self):
        """Handler returns success result with invoice and items_restored."""
        from src.handlers.restore_handler import RefundReversedHandler
        from src.events.payment_events import RefundReversedEvent

        invoice_id = uuid4()
        mock_invoice = MagicMock()
        mock_invoice.id = invoice_id

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.invoice = mock_invoice
        mock_result.items_restored = {
            "subscription": str(uuid4()),
            "token_bundles": [str(uuid4())],
            "add_ons": [],
            "tokens_credited": 500,
        }

        container = MagicMock()
        handler = RefundReversedHandler(container)

        event = RefundReversedEvent(
            invoice_id=invoice_id,
            reason="refund_canceled",
        )

        from unittest.mock import patch

        with patch("src.handlers.restore_handler.RestoreService") as MockRestoreService:
            mock_service = MagicMock()
            mock_service.process_restore.return_value = mock_result
            MockRestoreService.return_value = mock_service

            result = handler.handle(event)

            assert result.success is True
            assert result.data["invoice_id"] == str(invoice_id)
            assert result.data["status"] == "paid"
            assert result.data["items_restored"]["tokens_credited"] == 500

    def test_handler_handles_exception(self):
        """Handler catches exception and returns error result."""
        from src.handlers.restore_handler import RefundReversedHandler
        from src.events.payment_events import RefundReversedEvent

        container = MagicMock()
        handler = RefundReversedHandler(container)

        event = RefundReversedEvent(
            invoice_id=uuid4(),
            reason="test",
        )

        from unittest.mock import patch

        with patch("src.handlers.restore_handler.RestoreService") as MockRestoreService:
            MockRestoreService.side_effect = RuntimeError("Container wiring error")

            result = handler.handle(event)

            assert result.success is False
            assert "Container wiring error" in result.error

    def test_handler_rejects_invalid_event_type(self):
        """Handler rejects events that are not RefundReversedEvent."""
        from src.handlers.restore_handler import RefundReversedHandler
        from src.events.payment_events import PaymentCapturedEvent

        container = MagicMock()
        handler = RefundReversedHandler(container)

        wrong_event = PaymentCapturedEvent(
            invoice_id=uuid4(),
            payment_reference="REF",
        )

        result = handler.handle(wrong_event)

        assert result.success is False
        assert "invalid event type" in result.error.lower()
