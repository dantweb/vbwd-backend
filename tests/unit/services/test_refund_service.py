"""Tests for RefundService."""
from datetime import datetime
from unittest.mock import MagicMock, PropertyMock
from uuid import uuid4

from src.models.enums import (
    InvoiceStatus,
    LineItemType,
    SubscriptionStatus,
    PurchaseStatus,
)


def _make_line_item(item_type, item_id=None):
    """Create a mock line item."""
    li = MagicMock()
    li.item_type = item_type
    li.item_id = item_id or uuid4()
    return li


def _make_invoice(status=InvoiceStatus.PAID, line_items=None, user_id=None):
    """Create a mock invoice."""
    inv = MagicMock()
    inv.id = uuid4()
    inv.user_id = user_id or uuid4()
    inv.status = status
    inv.line_items = line_items or []
    inv.to_dict.return_value = {
        "id": str(inv.id),
        "status": status.value,
    }
    return inv


class TestRefundServiceProcessRefund:
    """Tests for RefundService.process_refund()."""

    def test_refund_paid_invoice(self):
        """Refund a paid invoice marks it as REFUNDED."""
        from src.services.refund_service import RefundService

        invoice = _make_invoice(InvoiceStatus.PAID)
        invoice_repo = MagicMock()
        invoice_repo.find_by_id.return_value = invoice

        service = RefundService(
            invoice_repo=invoice_repo,
            subscription_repo=MagicMock(),
            token_service=MagicMock(),
            purchase_repo=MagicMock(),
            addon_sub_repo=MagicMock(),
        )

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_001"
        )

        assert result.success is True
        assert result.invoice == invoice
        invoice.mark_refunded.assert_called_once()
        invoice_repo.save.assert_called_once_with(invoice)

    def test_refund_reverses_subscription(self):
        """Refund cancels an active subscription."""
        from src.services.refund_service import RefundService

        sub_id = uuid4()
        line_item = _make_line_item(LineItemType.SUBSCRIPTION, sub_id)
        invoice = _make_invoice(InvoiceStatus.PAID, [line_item])

        subscription = MagicMock()
        subscription.id = sub_id
        subscription.status = SubscriptionStatus.ACTIVE

        sub_repo = MagicMock()
        sub_repo.find_by_id.return_value = subscription

        service = RefundService(
            invoice_repo=MagicMock(find_by_id=MagicMock(return_value=invoice)),
            subscription_repo=sub_repo,
            token_service=MagicMock(),
            purchase_repo=MagicMock(),
            addon_sub_repo=MagicMock(),
        )

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_002"
        )

        assert result.success is True
        assert subscription.status == SubscriptionStatus.CANCELLED
        assert subscription.cancelled_at is not None
        sub_repo.save.assert_called_with(subscription)
        assert result.items_reversed["subscription"] == str(sub_id)

    def test_refund_debits_tokens(self):
        """Refund debits tokens for token bundle purchase."""
        from src.services.refund_service import RefundService

        purchase_id = uuid4()
        line_item = _make_line_item(LineItemType.TOKEN_BUNDLE, purchase_id)
        user_id = uuid4()
        invoice = _make_invoice(InvoiceStatus.PAID, [line_item], user_id=user_id)

        purchase = MagicMock()
        purchase.id = purchase_id
        purchase.status = PurchaseStatus.COMPLETED
        purchase.token_amount = 500

        purchase_repo = MagicMock()
        purchase_repo.find_by_id.return_value = purchase

        token_service = MagicMock()
        token_service.refund_tokens.return_value = 500

        service = RefundService(
            invoice_repo=MagicMock(find_by_id=MagicMock(return_value=invoice)),
            subscription_repo=MagicMock(),
            token_service=token_service,
            purchase_repo=purchase_repo,
            addon_sub_repo=MagicMock(),
        )

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_003"
        )

        assert result.success is True
        assert purchase.status == PurchaseStatus.REFUNDED
        purchase_repo.save.assert_called_with(purchase)
        token_service.refund_tokens.assert_called_once_with(
            user_id=user_id,
            amount=500,
            reference_id=purchase_id,
            description="Refund: 500 tokens",
        )
        assert result.items_reversed["tokens_debited"] == 500
        assert str(purchase_id) in result.items_reversed["token_bundles"]

    def test_refund_cancels_addon(self):
        """Refund cancels an active add-on subscription."""
        from src.services.refund_service import RefundService

        addon_id = uuid4()
        line_item = _make_line_item(LineItemType.ADD_ON, addon_id)
        invoice = _make_invoice(InvoiceStatus.PAID, [line_item])

        addon_sub = MagicMock()
        addon_sub.id = addon_id
        addon_sub.status = SubscriptionStatus.ACTIVE

        addon_repo = MagicMock()
        addon_repo.find_by_id.return_value = addon_sub

        service = RefundService(
            invoice_repo=MagicMock(find_by_id=MagicMock(return_value=invoice)),
            subscription_repo=MagicMock(),
            token_service=MagicMock(),
            purchase_repo=MagicMock(),
            addon_sub_repo=addon_repo,
        )

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_004"
        )

        assert result.success is True
        assert addon_sub.status == SubscriptionStatus.CANCELLED
        assert addon_sub.cancelled_at is not None
        addon_repo.save.assert_called_with(addon_sub)
        assert str(addon_id) in result.items_reversed["add_ons"]

    def test_refund_rejects_non_paid_invoice(self):
        """Refund rejects invoice that is not PAID."""
        from src.services.refund_service import RefundService

        invoice = _make_invoice(InvoiceStatus.PENDING)

        service = RefundService(
            invoice_repo=MagicMock(find_by_id=MagicMock(return_value=invoice)),
            subscription_repo=MagicMock(),
            token_service=MagicMock(),
            purchase_repo=MagicMock(),
            addon_sub_repo=MagicMock(),
        )

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_005"
        )

        assert result.success is False
        assert "cannot refund" in result.error.lower()

    def test_refund_rejects_missing_invoice(self):
        """Refund rejects when invoice not found."""
        from src.services.refund_service import RefundService

        service = RefundService(
            invoice_repo=MagicMock(find_by_id=MagicMock(return_value=None)),
            subscription_repo=MagicMock(),
            token_service=MagicMock(),
            purchase_repo=MagicMock(),
            addon_sub_repo=MagicMock(),
        )

        result = service.process_refund(
            invoice_id=uuid4(), refund_reference="REF_006"
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_refund_handles_token_only_invoice(self):
        """Refund handles invoice with only token bundles (the original bug)."""
        from src.services.refund_service import RefundService

        purchase_id = uuid4()
        line_item = _make_line_item(LineItemType.TOKEN_BUNDLE, purchase_id)
        user_id = uuid4()
        invoice = _make_invoice(InvoiceStatus.PAID, [line_item], user_id=user_id)

        purchase = MagicMock()
        purchase.id = purchase_id
        purchase.status = PurchaseStatus.COMPLETED
        purchase.token_amount = 1000

        purchase_repo = MagicMock()
        purchase_repo.find_by_id.return_value = purchase

        token_service = MagicMock()
        token_service.refund_tokens.return_value = 800  # user spent 200

        service = RefundService(
            invoice_repo=MagicMock(find_by_id=MagicMock(return_value=invoice)),
            subscription_repo=MagicMock(),
            token_service=token_service,
            purchase_repo=purchase_repo,
            addon_sub_repo=MagicMock(),
        )

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_007"
        )

        assert result.success is True
        assert result.items_reversed["tokens_debited"] == 800
        assert result.items_reversed["subscription"] is None
        assert result.items_reversed["add_ons"] == []
        token_service.refund_tokens.assert_called_once()

    def test_refund_handles_mixed_items(self):
        """Refund handles invoice with subscription + tokens + add-on."""
        from src.services.refund_service import RefundService

        sub_id = uuid4()
        purchase_id = uuid4()
        addon_id = uuid4()
        user_id = uuid4()

        li_sub = _make_line_item(LineItemType.SUBSCRIPTION, sub_id)
        li_token = _make_line_item(LineItemType.TOKEN_BUNDLE, purchase_id)
        li_addon = _make_line_item(LineItemType.ADD_ON, addon_id)
        invoice = _make_invoice(
            InvoiceStatus.PAID, [li_sub, li_token, li_addon], user_id=user_id
        )

        subscription = MagicMock(id=sub_id, status=SubscriptionStatus.ACTIVE)
        purchase = MagicMock(
            id=purchase_id, status=PurchaseStatus.COMPLETED, token_amount=200
        )
        addon_sub = MagicMock(id=addon_id, status=SubscriptionStatus.ACTIVE)

        sub_repo = MagicMock(find_by_id=MagicMock(return_value=subscription))
        purchase_repo = MagicMock(find_by_id=MagicMock(return_value=purchase))
        addon_repo = MagicMock(find_by_id=MagicMock(return_value=addon_sub))
        token_service = MagicMock(refund_tokens=MagicMock(return_value=200))

        service = RefundService(
            invoice_repo=MagicMock(find_by_id=MagicMock(return_value=invoice)),
            subscription_repo=sub_repo,
            token_service=token_service,
            purchase_repo=purchase_repo,
            addon_sub_repo=addon_repo,
        )

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_008"
        )

        assert result.success is True
        assert result.items_reversed["subscription"] == str(sub_id)
        assert str(purchase_id) in result.items_reversed["token_bundles"]
        assert str(addon_id) in result.items_reversed["add_ons"]
        assert result.items_reversed["tokens_debited"] == 200
