"""Subscription domain model."""
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
from src.extensions import db
from src.models.base import BaseModel
from src.models.enums import SubscriptionStatus


class Subscription(BaseModel):
    """
    User subscription model.

    Tracks subscription lifecycle from creation through expiration.
    """

    __tablename__ = "subscription"

    user_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tarif_plan_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("tarif_plan.id"),
        nullable=False,
    )
    status = db.Column(
        db.Enum(SubscriptionStatus),
        nullable=False,
        default=SubscriptionStatus.PENDING,
        index=True,
    )
    started_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, index=True)
    cancelled_at = db.Column(db.DateTime)

    # Relationships
    invoices = db.relationship(
        "UserInvoice",
        backref="subscription",
        lazy="dynamic",
    )

    @property
    def is_valid(self) -> bool:
        """Check if subscription is currently valid."""
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    @property
    def days_remaining(self) -> int:
        """Calculate days remaining until expiration."""
        if not self.expires_at:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)

    def activate(self, duration_days: int) -> None:
        """
        Activate subscription.

        Args:
            duration_days: Number of days the subscription is valid.
        """
        now = datetime.utcnow()
        self.status = SubscriptionStatus.ACTIVE
        self.started_at = now
        self.expires_at = now + timedelta(days=duration_days)

    def cancel(self) -> None:
        """Cancel subscription."""
        self.status = SubscriptionStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()

    def expire(self) -> None:
        """Mark subscription as expired."""
        self.status = SubscriptionStatus.EXPIRED

    def pause(self) -> None:
        """Pause subscription."""
        self.status = SubscriptionStatus.PAUSED

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tarif_plan_id": self.tarif_plan_id,
            "status": self.status.value,
            "is_valid": self.is_valid,
            "days_remaining": self.days_remaining,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, status={self.status.value})>"
