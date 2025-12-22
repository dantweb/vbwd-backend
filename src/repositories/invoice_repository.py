"""Invoice repository implementation."""
from typing import Optional, List, Union
from uuid import UUID
from datetime import datetime
from src.repositories.base import BaseRepository
from src.models import UserInvoice, InvoiceStatus


class InvoiceRepository(BaseRepository[UserInvoice]):
    """Repository for UserInvoice entity operations."""

    def __init__(self, session):
        super().__init__(session=session, model=UserInvoice)

    def find_by_user(self, user_id: Union[UUID, str]) -> List[UserInvoice]:
        """Find all invoices for a user."""
        return (
            self._session.query(UserInvoice)
            .filter(UserInvoice.user_id == user_id)
            .order_by(UserInvoice.created_at.desc())
            .all()
        )

    def find_by_invoice_number(self, invoice_number: str) -> Optional[UserInvoice]:
        """Find invoice by invoice number."""
        return (
            self._session.query(UserInvoice)
            .filter(UserInvoice.invoice_number == invoice_number)
            .first()
        )

    def find_by_subscription(self, subscription_id: Union[UUID, str]) -> List[UserInvoice]:
        """Find all invoices for a subscription."""
        return (
            self._session.query(UserInvoice)
            .filter(UserInvoice.subscription_id == subscription_id)
            .order_by(UserInvoice.created_at.desc())
            .all()
        )

    def find_pending(self) -> List[UserInvoice]:
        """Find all pending invoices."""
        return (
            self._session.query(UserInvoice)
            .filter(UserInvoice.status == InvoiceStatus.PENDING)
            .all()
        )

    def find_unpaid_by_user(self, user_id: Union[UUID, str]) -> List[UserInvoice]:
        """Find unpaid invoices for a user."""
        return (
            self._session.query(UserInvoice)
            .filter(
                UserInvoice.user_id == user_id,
                UserInvoice.status == InvoiceStatus.PENDING,
            )
            .order_by(UserInvoice.created_at.desc())
            .all()
        )
