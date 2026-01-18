"""Enumeration types for models."""
import enum


class UserStatus(enum.Enum):
    """User account status."""

    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserRole(enum.Enum):
    """User role."""

    USER = "user"
    ADMIN = "admin"
    VENDOR = "vendor"


class SubscriptionStatus(enum.Enum):
    """Subscription status."""

    PENDING = "pending"
    ACTIVE = "active"
    TRIALING = "trialing"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class InvoiceStatus(enum.Enum):
    """Invoice status."""

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class BillingPeriod(enum.Enum):
    """Billing period for tariff plans."""

    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"
    WEEKLY = "weekly"
    ONE_TIME = "one_time"


class UserCaseStatus(enum.Enum):
    """User case status."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class PurchaseStatus(enum.Enum):
    """Token bundle purchase status."""

    PENDING = "pending"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class LineItemType(enum.Enum):
    """Invoice line item type."""

    SUBSCRIPTION = "subscription"
    TOKEN_BUNDLE = "token_bundle"
    ADD_ON = "add_on"


class TokenTransactionType(enum.Enum):
    """Token transaction type."""

    PURCHASE = "purchase"
    USAGE = "usage"
    REFUND = "refund"
    BONUS = "bonus"
    ADJUSTMENT = "adjustment"
