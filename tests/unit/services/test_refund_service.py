"""Tests for RefundService."""
import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from vbwd.events.line_item_registry import LineItemHandlerRegistry
from vbwd.handlers.core_line_item_handler import CoreLineItemHandler

try:
    from plugins.subscription.subscription.handlers.line_item_handler import (
        SubscriptionLineItemHandler,
    )
except ImportError:
    pytest.skip("Subscription plugin not installed", allow_module_level=True)
from vbwd.models.enums import (
    InvoiceStatus,
    LineItemType,
    SubscriptionStatus,
    PurchaseStatus,
)


def _make_line_item(item_type, item_id=None):
    """Create a mock line item."""
    line_item = MagicMock()
    line_item.item_type = item_type
    line_item.item_id = item_id or uuid4()
    return line_item


def _make_invoice(status=InvoiceStatus.PAID, line_items=None, user_id=None):
    """Create a mock invoice."""
    invoice = MagicMock()
    invoice.id = uuid4()
    invoice.user_id = user_id or uuid4()
    invoice.status = status
    invoice.line_items = line_items or []
    invoice.to_dict.return_value = {"id": str(invoice.id), "status": status.value}
    return invoice


def _make_service(
    invoice=None,
    subscription_repo=None,
    purchase_repo=None,
    addon_sub_repo=None,
    token_service=None,
):
    """Create RefundService with a properly wired registry."""
    from vbwd.services.refund_service import RefundService

    invoice_repo = MagicMock()
    invoice_repo.find_by_id.return_value = invoice

    subscription_repo = subscription_repo or MagicMock()
    purchase_repo = purchase_repo or MagicMock()
    addon_sub_repo = addon_sub_repo or MagicMock()
    token_service = token_service or MagicMock()

    container = MagicMock()
    container.subscription_repository.return_value = subscription_repo
    container.token_bundle_purchase_repository.return_value = purchase_repo
    container.addon_subscription_repository.return_value = addon_sub_repo
    container.token_balance_repository.return_value = MagicMock()
    container.token_transaction_repository.return_value = MagicMock()
    container.token_service.return_value = token_service

    registry = LineItemHandlerRegistry()
    registry.register(CoreLineItemHandler(container))
    registry.register(SubscriptionLineItemHandler(container))

    return RefundService(
        invoice_repo=invoice_repo,
        token_service=token_service,
        purchase_repo=purchase_repo,
        container=container,
        registry=registry,
    )


class TestRefundServiceProcessRefund:
    """Tests for RefundService.process_refund()."""

    def test_refund_paid_invoice(self):
        """Refund a paid invoice marks it as REFUNDED."""
        invoice = _make_invoice(InvoiceStatus.PAID)
        service = _make_service(invoice=invoice)

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_001"
        )

        assert result.success is True
        assert result.invoice == invoice
        invoice.mark_refunded.assert_called_once()

    def test_refund_reverses_subscription(self):
        """Refund cancels an active subscription and debits default tokens."""
        sub_id = uuid4()
        line_item = _make_line_item(LineItemType.SUBSCRIPTION, sub_id)
        invoice = _make_invoice(InvoiceStatus.PAID, [line_item])

        tarif_plan = MagicMock()
        tarif_plan.features = {"default_tokens": 50}
        tarif_plan.name = "Basic"
        subscription = MagicMock()
        subscription.id = sub_id
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.tarif_plan = tarif_plan

        sub_repo = MagicMock()
        sub_repo.find_by_id.return_value = subscription

        token_service = MagicMock()
        token_service.get_balance.return_value = 50

        service = _make_service(
            invoice=invoice,
            subscription_repo=sub_repo,
            token_service=token_service,
        )

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_002"
        )

        assert result.success is True
        assert subscription.status == SubscriptionStatus.CANCELLED
        assert subscription.cancelled_at is not None
        sub_repo.save.assert_called_with(subscription)
        assert result.items_reversed["subscription"] == str(sub_id)
        assert result.items_reversed["tokens_debited"] == 50

    def test_refund_rejects_insufficient_token_balance(self):
        """Refund is rejected when user has insufficient tokens to cover bundle refund."""
        purchase_id = uuid4()
        line_item = _make_line_item(LineItemType.TOKEN_BUNDLE, purchase_id)
        invoice = _make_invoice(InvoiceStatus.PAID, [line_item])

        purchase = MagicMock()
        purchase.id = purchase_id
        purchase.status = PurchaseStatus.COMPLETED
        purchase.token_amount = 500

        purchase_repo = MagicMock()
        purchase_repo.find_by_id.return_value = purchase

        token_service = MagicMock()
        token_service.get_balance.return_value = 100  # less than 500 needed

        service = _make_service(
            invoice=invoice,
            purchase_repo=purchase_repo,
            token_service=token_service,
        )

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_FAIL"
        )

        assert result.success is False
        assert "insufficient token balance" in result.error.lower()
        invoice.mark_refunded.assert_not_called()

    def test_refund_debits_tokens(self):
        """Refund debits tokens for token bundle purchase."""
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
        token_service.get_balance.return_value = 500
        token_service.refund_tokens.return_value = 500

        service = _make_service(
            invoice=invoice,
            purchase_repo=purchase_repo,
            token_service=token_service,
        )

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_003"
        )

        assert result.success is True
        assert purchase.status == PurchaseStatus.REFUNDED
        assert result.items_reversed["tokens_debited"] == 500
        assert str(purchase_id) in result.items_reversed["token_bundles"]

    def test_refund_cancels_addon(self):
        """Refund cancels an active add-on subscription."""
        addon_id = uuid4()
        line_item = _make_line_item(LineItemType.ADD_ON, addon_id)
        invoice = _make_invoice(InvoiceStatus.PAID, [line_item])

        addon_sub = MagicMock()
        addon_sub.id = addon_id
        addon_sub.status = SubscriptionStatus.ACTIVE

        addon_repo = MagicMock()
        addon_repo.find_by_id.return_value = addon_sub

        service = _make_service(invoice=invoice, addon_sub_repo=addon_repo)

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
        invoice = _make_invoice(InvoiceStatus.PENDING)
        service = _make_service(invoice=invoice)

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_005"
        )

        assert result.success is False
        assert "cannot refund" in result.error.lower()

    def test_refund_rejects_missing_invoice(self):
        """Refund rejects when invoice not found."""
        service = _make_service(invoice=None)

        result = service.process_refund(invoice_id=uuid4(), refund_reference="REF_006")

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_refund_handles_token_only_invoice(self):
        """Refund handles invoice with only token bundles."""
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
        token_service.get_balance.return_value = 1000
        token_service.refund_tokens.return_value = 800

        service = _make_service(
            invoice=invoice,
            purchase_repo=purchase_repo,
            token_service=token_service,
        )

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_007"
        )

        assert result.success is True
        assert result.items_reversed["tokens_debited"] == 800
        assert result.items_reversed["subscription"] is None
        assert result.items_reversed["add_ons"] == []

    def test_refund_handles_mixed_items(self):
        """Refund handles invoice with subscription + tokens + add-on."""
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

        tarif_plan = MagicMock()
        tarif_plan.features = {"default_tokens": 100}
        tarif_plan.name = "Pro"
        subscription = MagicMock(
            id=sub_id, status=SubscriptionStatus.ACTIVE, tarif_plan=tarif_plan
        )
        purchase = MagicMock(
            id=purchase_id, status=PurchaseStatus.COMPLETED, token_amount=200
        )
        addon_sub = MagicMock(id=addon_id, status=SubscriptionStatus.ACTIVE)

        sub_repo = MagicMock(find_by_id=MagicMock(return_value=subscription))
        purchase_repo = MagicMock(find_by_id=MagicMock(return_value=purchase))
        addon_repo = MagicMock(find_by_id=MagicMock(return_value=addon_sub))
        token_service = MagicMock()
        token_service.get_balance.return_value = 500
        token_service.refund_tokens.return_value = 200

        service = _make_service(
            invoice=invoice,
            subscription_repo=sub_repo,
            purchase_repo=purchase_repo,
            addon_sub_repo=addon_repo,
            token_service=token_service,
        )

        result = service.process_refund(
            invoice_id=invoice.id, refund_reference="REF_008"
        )

        assert result.success is True
        assert result.items_reversed["subscription"] == str(sub_id)
        assert str(purchase_id) in result.items_reversed["token_bundles"]
        assert str(addon_id) in result.items_reversed["add_ons"]
        assert result.items_reversed["tokens_debited"] == 300
