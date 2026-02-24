"""TarifPlan domain model."""
from sqlalchemy.dialects.postgresql import UUID
from src.extensions import db
from src.models.base import BaseModel
from src.models.enums import BillingPeriod


class TarifPlan(BaseModel):
    """
    Tariff plan model.

    Defines subscription plans with pricing and features.
    """

    __tablename__ = "tarif_plan"

    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    description = db.Column(db.Text)

    # Quick access float price (for fast sorting/filtering)
    price_float = db.Column(db.Float, nullable=False)

    # Reference to Price object (detailed pricing with taxes)
    price_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("price.id"),
        nullable=True,  # Optional for backward compatibility
        index=True,
    )

    # Legacy fields (kept for backward compatibility)
    price = db.Column(db.Numeric(10, 2), nullable=True)  # Made nullable
    currency = db.Column(db.String(3), nullable=True, default="EUR")  # Made nullable

    billing_period = db.Column(
        db.Enum(
            BillingPeriod,
            name="billingperiod",
            native_enum=True,
            create_constraint=False,
        ),
        nullable=False,
    )
    features = db.Column(db.JSON, default=list)
    trial_days = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    sort_order = db.Column(db.Integer, default=0)

    # Relationships
    price_obj = db.relationship(
        "Price",
        backref="tarif_plans",
        lazy="joined",
        foreign_keys=[price_id],
    )
    subscriptions = db.relationship(
        "Subscription",
        backref="tarif_plan",
        lazy="dynamic",
        cascade="all, delete-orphan",
        foreign_keys="[Subscription.tarif_plan_id]",
    )
    pending_subscriptions = db.relationship(
        "Subscription",
        backref="pending_plan",
        lazy="dynamic",
        foreign_keys="[Subscription.pending_plan_id]",
    )
    invoices = db.relationship(
        "UserInvoice",
        backref="tarif_plan",
        lazy="dynamic",
    )

    @property
    def is_recurring(self) -> bool:
        """Check if this is a recurring subscription plan."""
        return self.billing_period != BillingPeriod.ONE_TIME

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "price_float": self.price_float,
            "billing_period": self.billing_period.value,
            "features": self.features,
            "trial_days": self.trial_days,
            "is_active": self.is_active,
            "is_recurring": self.is_recurring,
        }

        # Include Price object if available
        if self.price_obj:
            result["price"] = self.price_obj.to_dict()
        elif self.price:
            # Legacy fallback
            result["price"] = {
                "price_decimal": str(self.price),
                "currency_code": self.currency,
            }

        return result

    def __repr__(self) -> str:
        return f"<TarifPlan(slug='{self.slug}', price={self.price})>"
