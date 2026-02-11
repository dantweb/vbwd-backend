"""Tests for PaymentRefundedHandler."""
from unittest.mock import MagicMock
from uuid import uuid4


class TestPaymentRefundedHandler:
    """Tests for the thin PaymentRefundedHandler."""

    def test_handler_calls_refund_service(self):
        """Handler delegates to RefundService.process_refund()."""
        from src.handlers.refund_handler import PaymentRefundedHandler
        from src.events.payment_events import PaymentRefundedEvent

        invoice_id = uuid4()
        mock_invoice = MagicMock()
        mock_invoice.id = invoice_id
        mock_invoice.to_dict.return_value = {
            "id": str(invoice_id),
            "status": "refunded",
        }

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.invoice = mock_invoice
        mock_result.items_reversed = {
            "subscription": None,
            "token_bundles": [],
            "add_ons": [],
            "tokens_debited": 0,
        }

        mock_refund_service = MagicMock()
        mock_refund_service.process_refund.return_value = mock_result

        container = MagicMock()
        container.refund_service.return_value = mock_refund_service

        handler = PaymentRefundedHandler(container)
        event = PaymentRefundedEvent(
            invoice_id=invoice_id,
            refund_reference="REF_TEST",
        )

        result = handler.handle(event)

        mock_refund_service.process_refund.assert_called_once_with(
            invoice_id=invoice_id,
            refund_reference="REF_TEST",
        )
        assert result.success is True

    def test_handler_returns_error_on_service_failure(self):
        """Handler returns error when RefundService reports failure."""
        from src.handlers.refund_handler import PaymentRefundedHandler
        from src.events.payment_events import PaymentRefundedEvent

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.error = "Cannot refund: invoice status is pending"

        mock_refund_service = MagicMock()
        mock_refund_service.process_refund.return_value = mock_result

        container = MagicMock()
        container.refund_service.return_value = mock_refund_service

        handler = PaymentRefundedHandler(container)
        event = PaymentRefundedEvent(
            invoice_id=uuid4(),
            refund_reference="REF_FAIL",
        )

        result = handler.handle(event)

        assert result.success is False
        assert "cannot refund" in result.error.lower()

    def test_handler_returns_success_with_data(self):
        """Handler returns success result with invoice and items_reversed."""
        from src.handlers.refund_handler import PaymentRefundedHandler
        from src.events.payment_events import PaymentRefundedEvent

        invoice_id = uuid4()
        mock_invoice = MagicMock()
        mock_invoice.id = invoice_id
        mock_invoice.to_dict.return_value = {
            "id": str(invoice_id),
            "status": "refunded",
        }

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.invoice = mock_invoice
        mock_result.items_reversed = {
            "subscription": str(uuid4()),
            "token_bundles": [str(uuid4())],
            "add_ons": [],
            "tokens_debited": 500,
        }

        mock_refund_service = MagicMock()
        mock_refund_service.process_refund.return_value = mock_result

        container = MagicMock()
        container.refund_service.return_value = mock_refund_service

        handler = PaymentRefundedHandler(container)
        event = PaymentRefundedEvent(
            invoice_id=invoice_id,
            refund_reference="REF_DATA",
        )

        result = handler.handle(event)

        assert result.success is True
        assert result.data["invoice_id"] == str(invoice_id)
        assert result.data["status"] == "refunded"
        assert result.data["refund_reference"] == "REF_DATA"
        assert result.data["items_reversed"]["tokens_debited"] == 500
        assert "invoice" in result.data

    def test_handler_handles_exception(self):
        """Handler catches exception and returns error result."""
        from src.handlers.refund_handler import PaymentRefundedHandler
        from src.events.payment_events import PaymentRefundedEvent

        container = MagicMock()
        container.refund_service.side_effect = RuntimeError("Container wiring error")

        handler = PaymentRefundedHandler(container)
        event = PaymentRefundedEvent(
            invoice_id=uuid4(),
            refund_reference="REF_ERR",
        )

        result = handler.handle(event)

        assert result.success is False
        assert "Container wiring error" in result.error
