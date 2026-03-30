"""Restore service — reverses a refund, restoring invoice and all items."""
from typing import Optional, Dict, Any
from uuid import UUID

from vbwd.events.line_item_registry import (
    LineItemContext,
    LineItemHandlerRegistry,
    line_item_registry,
)
from vbwd.models.enums import InvoiceStatus


class RestoreResult:
    """Result of a restore operation."""

    def __init__(
        self,
        success: bool,
        invoice=None,
        items_restored: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ):
        self.success = success
        self.invoice = invoice
        self.items_restored = items_restored
        self.error = error


class RestoreService:
    """Service for restoring a refunded invoice.

    Reverses a refund — restores the invoice to PAID and delegates
    line item restoration to the LineItemHandlerRegistry.
    """

    def __init__(self, container, registry: LineItemHandlerRegistry | None = None):
        self._container = container
        self._registry = registry or line_item_registry

    def process_restore(self, invoice_id: UUID, reason: str = "") -> RestoreResult:
        """Restore a refunded invoice back to PAID state."""
        invoice_repo = self._container.invoice_repository()

        # 1. Fetch and validate invoice
        invoice = invoice_repo.find_by_id(str(invoice_id))
        if not invoice:
            return RestoreResult(success=False, error=f"Invoice {invoice_id} not found")

        if invoice.status != InvoiceStatus.REFUNDED:
            return RestoreResult(
                success=False,
                error=f"Cannot restore: invoice status is {invoice.status.value}, expected refunded",
            )

        # 2. Mark invoice as paid again
        invoice.status = InvoiceStatus.PAID
        invoice_repo.save(invoice)

        # 3. Delegate line item restoration to registry
        context = LineItemContext(
            invoice=invoice,
            user_id=invoice.user_id,
            container=self._container,
        )
        items_restored: Dict[str, Any] = {
            "subscription": None,
            "token_bundles": [],
            "add_ons": [],
            "tokens_credited": 0,
        }

        for line_item in invoice.line_items:
            result = self._registry.process_restoration(line_item, context)
            if result.success and not result.skipped:
                data = result.data
                if "subscription_id" in data:
                    items_restored["subscription"] = data["subscription_id"]
                if "purchase_id" in data:
                    items_restored["token_bundles"].append(data["purchase_id"])
                if "addon_subscription_id" in data:
                    items_restored["add_ons"].append(data["addon_subscription_id"])
                items_restored["tokens_credited"] += data.get("tokens_credited", 0)

        return RestoreResult(
            success=True, invoice=invoice, items_restored=items_restored
        )
