"""InvoiceLineItem domain model."""
from sqlalchemy.dialects.postgresql import UUID
from src.extensions import db
from src.models.base import BaseModel
from src.models.enums import LineItemType


class InvoiceLineItem(BaseModel):
    """
    Invoice line item model.

    Tracks individual items on an invoice (subscription, token bundle, add-on).
    """

    __tablename__ = "invoice_line_item"

    invoice_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("user_invoice.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_type = db.Column(
        db.Enum(LineItemType),
        nullable=False,
    )
    item_id = db.Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "invoice_id": str(self.invoice_id),
            "type": self.item_type.value,
            "item_id": str(self.item_id),
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": str(self.unit_price),
            "amount": str(self.total_price),
        }

    def __repr__(self) -> str:
        return f"<InvoiceLineItem(type={self.item_type.value}, amount={self.total_price})>"
