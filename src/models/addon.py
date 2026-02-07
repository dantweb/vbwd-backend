"""AddOn domain model - optional extras for subscriptions."""
from src.extensions import db
from src.models.base import BaseModel
from src.models.enums import BillingPeriod
from sqlalchemy.dialects.postgresql import JSONB


class AddOn(BaseModel):
    """
    Add-on model.

    Represents optional extras that can be added to subscriptions.
    Uses a JSON `config` field for flexible parameters (like tarif_plan.features).
    """

    __tablename__ = "addon"

    # Basic info
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    # Pricing
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    currency = db.Column(db.String(3), nullable=False, default="EUR")
    billing_period = db.Column(
        db.String(50), nullable=False, default=BillingPeriod.MONTHLY.value
    )

    # Flexible configuration (like tarif_plan.features)
    config = db.Column(JSONB, nullable=False, default=dict)

    # Status
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)

    @property
    def is_recurring(self) -> bool:
        """Check if this is a recurring add-on."""
        return self.billing_period != BillingPeriod.ONE_TIME.value

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "price": str(self.price),
            "currency": self.currency,
            "billing_period": self.billing_period,
            "config": self.config or {},
            "is_active": self.is_active,
            "is_recurring": self.is_recurring,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<AddOn(name='{self.name}', slug='{self.slug}', price={self.price})>"
