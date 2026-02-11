"""Tests for RestoreService."""
from datetime import datetime
from unittest.mock import MagicMock
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


def _make_invoice(status=InvoiceStatus.REFUNDED, line_items=None, user_id=None):
    """Create a mock invoice."""
    inv = MagicMock()
    inv.id = uuid4()
    inv.user_id = user_id or uuid4()
    inv.status = status
    inv.line_items = line_items or []
    return inv


def _make_container(**overrides):
    """Create a mock container with repo factories."""
    container = MagicMock()
    for name in [
        "invoice_repository",
        "subscription_repository",
        "token_balance_repository",
        "token_transaction_repository",
        "token_bundle_purchase_repository",
        "addon_subscription_repository",
    ]:
        if name not in overrides:
            getattr(container, name).return_value = MagicMock()
    for name, repo in overrides.items():
        getattr(container, name).return_value = repo
    return container


class TestRestoreServiceProcessRestore:
    """Tests for RestoreService.process_restore()."""

    def test_restore_refunded_invoice(self):
        """Restore a refunded invoice marks it as PAID."""
        from src.services.restore_service import RestoreService

        invoice = _make_invoice(InvoiceStatus.REFUNDED)
        invoice_repo = MagicMock()
        invoice_repo.find_by_id.return_value = invoice

        container = _make_container(invoice_repository=invoice_repo)
        service = RestoreService(container)

        result = service.process_restore(
            invoice_id=invoice.id, reason="refund_canceled"
        )

        assert result.success is True
        assert result.invoice == invoice
        assert invoice.status == InvoiceStatus.PAID
        invoice_repo.save.assert_called_with(invoice)

    def test_restore_reactivates_cancelled_subscription(self):
        """Restore re-activates a cancelled subscription."""
        from src.services.restore_service import RestoreService

        sub_id = uuid4()
        line_item = _make_line_item(LineItemType.SUBSCRIPTION, sub_id)
        invoice = _make_invoice(InvoiceStatus.REFUNDED, [line_item])

        subscription = MagicMock()
        subscription.id = sub_id
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime(2026, 2, 10)
        plan = MagicMock()
        plan.billing_period = MagicMock()  # BillingPeriod enum
        subscription.tarif_plan = plan

        invoice_repo = MagicMock()
        invoice_repo.find_by_id.return_value = invoice

        sub_repo = MagicMock()
        sub_repo.find_by_id.return_value = subscription

        container = _make_container(
            invoice_repository=invoice_repo,
            subscription_repository=sub_repo,
        )
        service = RestoreService(container)

        result = service.process_restore(
            invoice_id=invoice.id, reason="refund_canceled"
        )

        assert result.success is True
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert subscription.cancelled_at is None
        assert subscription.starts_at is not None
        assert subscription.expires_at is not None
        sub_repo.save.assert_called_with(subscription)
        assert result.items_restored["subscription"] == str(sub_id)

    def test_restore_recredits_tokens(self):
        """Restore re-credits tokens for a refunded purchase."""
        from src.services.restore_service import RestoreService

        purchase_id = uuid4()
        user_id = uuid4()
        line_item = _make_line_item(LineItemType.TOKEN_BUNDLE, purchase_id)
        invoice = _make_invoice(InvoiceStatus.REFUNDED, [line_item], user_id=user_id)

        purchase = MagicMock()
        purchase.id = purchase_id
        purchase.status = PurchaseStatus.REFUNDED
        purchase.token_amount = 500

        balance = MagicMock()
        balance.balance = 100

        invoice_repo = MagicMock()
        invoice_repo.find_by_id.return_value = invoice

        purchase_repo = MagicMock()
        purchase_repo.find_by_id.return_value = purchase

        token_balance_repo = MagicMock()
        token_balance_repo.find_by_user_id.return_value = balance

        token_tx_repo = MagicMock()

        container = _make_container(
            invoice_repository=invoice_repo,
            token_bundle_purchase_repository=purchase_repo,
            token_balance_repository=token_balance_repo,
            token_transaction_repository=token_tx_repo,
        )
        service = RestoreService(container)

        result = service.process_restore(
            invoice_id=invoice.id, reason="refund_canceled"
        )

        assert result.success is True
        assert purchase.status == PurchaseStatus.COMPLETED
        assert purchase.tokens_credited is True
        purchase_repo.save.assert_called_with(purchase)
        assert balance.balance == 600  # 100 + 500
        token_balance_repo.save.assert_called()
        token_tx_repo.save.assert_called_once()
        assert str(purchase_id) in result.items_restored["token_bundles"]
        assert result.items_restored["tokens_credited"] == 500

    def test_restore_creates_balance_if_none(self):
        """If user has no token balance, one should be created on restore."""
        from src.services.restore_service import RestoreService

        purchase_id = uuid4()
        user_id = uuid4()
        line_item = _make_line_item(LineItemType.TOKEN_BUNDLE, purchase_id)
        invoice = _make_invoice(InvoiceStatus.REFUNDED, [line_item], user_id=user_id)

        purchase = MagicMock()
        purchase.id = purchase_id
        purchase.status = PurchaseStatus.REFUNDED
        purchase.token_amount = 300

        invoice_repo = MagicMock()
        invoice_repo.find_by_id.return_value = invoice

        purchase_repo = MagicMock()
        purchase_repo.find_by_id.return_value = purchase

        token_balance_repo = MagicMock()
        token_balance_repo.find_by_user_id.return_value = None

        container = _make_container(
            invoice_repository=invoice_repo,
            token_bundle_purchase_repository=purchase_repo,
            token_balance_repository=token_balance_repo,
            token_transaction_repository=MagicMock(),
        )
        service = RestoreService(container)

        result = service.process_restore(
            invoice_id=invoice.id, reason="refund_canceled"
        )

        assert result.success is True
        saved_balance = token_balance_repo.save.call_args[0][0]
        assert saved_balance.balance == 300

    def test_restore_reactivates_addon(self):
        """Restore re-activates a cancelled add-on subscription."""
        from src.services.restore_service import RestoreService

        addon_id = uuid4()
        line_item = _make_line_item(LineItemType.ADD_ON, addon_id)
        invoice = _make_invoice(InvoiceStatus.REFUNDED, [line_item])

        addon_sub = MagicMock()
        addon_sub.id = addon_id
        addon_sub.status = SubscriptionStatus.CANCELLED
        addon_sub.cancelled_at = datetime(2026, 2, 10)

        invoice_repo = MagicMock()
        invoice_repo.find_by_id.return_value = invoice

        addon_repo = MagicMock()
        addon_repo.find_by_id.return_value = addon_sub

        container = _make_container(
            invoice_repository=invoice_repo,
            addon_subscription_repository=addon_repo,
        )
        service = RestoreService(container)

        result = service.process_restore(
            invoice_id=invoice.id, reason="refund_canceled"
        )

        assert result.success is True
        assert addon_sub.status == SubscriptionStatus.ACTIVE
        assert addon_sub.cancelled_at is None
        assert addon_sub.activated_at is not None
        addon_repo.save.assert_called_with(addon_sub)
        assert str(addon_id) in result.items_restored["add_ons"]

    def test_restore_rejects_non_refunded_invoice(self):
        """Restore rejects invoice that is not REFUNDED."""
        from src.services.restore_service import RestoreService

        invoice = _make_invoice(InvoiceStatus.PAID)
        invoice_repo = MagicMock()
        invoice_repo.find_by_id.return_value = invoice

        container = _make_container(invoice_repository=invoice_repo)
        service = RestoreService(container)

        result = service.process_restore(invoice_id=invoice.id, reason="test")

        assert result.success is False
        assert "cannot restore" in result.error.lower()

    def test_restore_rejects_missing_invoice(self):
        """Restore rejects when invoice not found."""
        from src.services.restore_service import RestoreService

        invoice_repo = MagicMock()
        invoice_repo.find_by_id.return_value = None

        container = _make_container(invoice_repository=invoice_repo)
        service = RestoreService(container)

        result = service.process_restore(invoice_id=uuid4(), reason="test")

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_restore_handles_mixed_items(self):
        """Restore handles invoice with subscription + tokens + add-on."""
        from src.services.restore_service import RestoreService

        sub_id = uuid4()
        purchase_id = uuid4()
        addon_id = uuid4()
        user_id = uuid4()

        li_sub = _make_line_item(LineItemType.SUBSCRIPTION, sub_id)
        li_token = _make_line_item(LineItemType.TOKEN_BUNDLE, purchase_id)
        li_addon = _make_line_item(LineItemType.ADD_ON, addon_id)
        invoice = _make_invoice(
            InvoiceStatus.REFUNDED, [li_sub, li_token, li_addon], user_id=user_id
        )

        subscription = MagicMock(id=sub_id, status=SubscriptionStatus.CANCELLED)
        subscription.cancelled_at = datetime(2026, 2, 10)
        plan = MagicMock()
        plan.billing_period = MagicMock()
        subscription.tarif_plan = plan

        purchase = MagicMock(
            id=purchase_id, status=PurchaseStatus.REFUNDED, token_amount=200
        )

        addon_sub = MagicMock(id=addon_id, status=SubscriptionStatus.CANCELLED)
        addon_sub.cancelled_at = datetime(2026, 2, 10)

        balance = MagicMock()
        balance.balance = 50

        sub_repo = MagicMock(find_by_id=MagicMock(return_value=subscription))
        purchase_repo = MagicMock(find_by_id=MagicMock(return_value=purchase))
        addon_repo = MagicMock(find_by_id=MagicMock(return_value=addon_sub))
        token_balance_repo = MagicMock(find_by_user_id=MagicMock(return_value=balance))

        invoice_repo = MagicMock(find_by_id=MagicMock(return_value=invoice))

        container = _make_container(
            invoice_repository=invoice_repo,
            subscription_repository=sub_repo,
            token_bundle_purchase_repository=purchase_repo,
            addon_subscription_repository=addon_repo,
            token_balance_repository=token_balance_repo,
            token_transaction_repository=MagicMock(),
        )
        service = RestoreService(container)

        result = service.process_restore(
            invoice_id=invoice.id, reason="refund_canceled"
        )

        assert result.success is True
        assert result.items_restored["subscription"] == str(sub_id)
        assert str(purchase_id) in result.items_restored["token_bundles"]
        assert str(addon_id) in result.items_restored["add_ons"]
        assert result.items_restored["tokens_credited"] == 200
        assert invoice.status == InvoiceStatus.PAID
        assert subscription.status == SubscriptionStatus.ACTIVE
        assert purchase.status == PurchaseStatus.COMPLETED
        assert addon_sub.status == SubscriptionStatus.ACTIVE
        assert balance.balance == 250  # 50 + 200
