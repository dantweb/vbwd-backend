"""Enumeration types for models."""
import enum


class UserStatus(enum.Enum):
    """User account status."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class UserRole(enum.Enum):
    """User role."""

    USER = "USER"
    ADMIN = "ADMIN"
    VENDOR = "VENDOR"


class SubscriptionStatus(enum.Enum):
    """Subscription status."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class InvoiceStatus(enum.Enum):
    """Invoice status."""

    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class BillingPeriod(enum.Enum):
    """Billing period for tariff plans."""

    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    QUARTERLY = "QUARTERLY"
    WEEKLY = "WEEKLY"
    ONE_TIME = "ONE_TIME"


class UserCaseStatus(enum.Enum):
    """User case status."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class PurchaseStatus(enum.Enum):
    """Token bundle purchase status."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class LineItemType(enum.Enum):
    """Invoice line item type."""

    SUBSCRIPTION = "SUBSCRIPTION"
    TOKEN_BUNDLE = "TOKEN_BUNDLE"
    ADD_ON = "ADD_ON"


class TokenTransactionType(enum.Enum):
    """Token transaction type."""

    PURCHASE = "PURCHASE"
    USAGE = "USAGE"
    REFUND = "REFUND"
    BONUS = "BONUS"
    ADJUSTMENT = "ADJUSTMENT"


class ArcanaType(enum.Enum):
    """Tarot card arcana type."""

    MAJOR_ARCANA = "MAJOR_ARCANA"
    CUPS = "CUPS"
    WANDS = "WANDS"
    SWORDS = "SWORDS"
    PENTACLES = "PENTACLES"


class CardOrientation(enum.Enum):
    """Card orientation in spread."""

    UPRIGHT = "UPRIGHT"
    REVERSED = "REVERSED"


class CardPosition(enum.Enum):
    """Card position in 3-card spread."""

    PAST = "PAST"
    PRESENT = "PRESENT"
    FUTURE = "FUTURE"


class TaroSessionStatus(enum.Enum):
    """Taro session status."""

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CLOSED = "CLOSED"


class AddonSubscriptionStatus(enum.Enum):
    """Addon subscription status."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
