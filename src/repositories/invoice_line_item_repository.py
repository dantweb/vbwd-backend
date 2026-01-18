"""InvoiceLineItem repository implementation."""
from typing import List
from uuid import UUID
from src.repositories.base import BaseRepository
from src.models.invoice_line_item import InvoiceLineItem
from src.models.enums import LineItemType


class InvoiceLineItemRepository(BaseRepository[InvoiceLineItem]):
    """Repository for InvoiceLineItem entity operations."""

    def __init__(self, session):
        super().__init__(session=session, model=InvoiceLineItem)

    def find_by_invoice(self, invoice_id: UUID) -> List[InvoiceLineItem]:
        """Find all line items for an invoice."""
        return (
            self._session.query(InvoiceLineItem)
            .filter(InvoiceLineItem.invoice_id == invoice_id)
            .all()
        )

    def find_by_item(self, item_id: UUID) -> List[InvoiceLineItem]:
        """Find all line items referencing a specific item."""
        return (
            self._session.query(InvoiceLineItem)
            .filter(InvoiceLineItem.item_id == item_id)
            .all()
        )

    def find_by_type(
        self, invoice_id: UUID, item_type: LineItemType
    ) -> List[InvoiceLineItem]:
        """Find line items of a specific type for an invoice."""
        return (
            self._session.query(InvoiceLineItem)
            .filter(
                InvoiceLineItem.invoice_id == invoice_id,
                InvoiceLineItem.item_type == item_type,
            )
            .all()
        )

    def create(self, line_item: InvoiceLineItem) -> InvoiceLineItem:
        """Create a new line item."""
        self._session.add(line_item)
        self._session.commit()
        self._session.refresh(line_item)
        return line_item

    def create_many(self, line_items: List[InvoiceLineItem]) -> List[InvoiceLineItem]:
        """Create multiple line items."""
        for item in line_items:
            self._session.add(item)
        self._session.commit()
        for item in line_items:
            self._session.refresh(item)
        return line_items
