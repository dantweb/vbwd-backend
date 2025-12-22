"""Subscription domain events."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
from src.events.domain import DomainEvent


@dataclass
class SubscriptionCreatedEvent(DomainEvent):
    """Event: New subscription was created."""

    subscription_id: UUID = None
    user_id: UUID = None
    tarif_plan_id: UUID = None
    status: str = None

    def __post_init__(self):
        """Set event name and timestamp."""
        super().__post_init__()
        self.name = 'subscription.created'
        if not hasattr(self, 'data'):
            self.data = {}
        if not hasattr(self, 'propagation_stopped'):
            self.propagation_stopped = False


@dataclass
class SubscriptionActivatedEvent(DomainEvent):
    """Event: Subscription was activated."""

    subscription_id: UUID = None
    user_id: UUID = None
    tarif_plan_id: UUID = None
    started_at: datetime = None
    expires_at: datetime = None

    def __post_init__(self):
        """Set event name and timestamp."""
        super().__post_init__()
        self.name = 'subscription.activated'
        if not hasattr(self, 'data'):
            self.data = {}
        if not hasattr(self, 'propagation_stopped'):
            self.propagation_stopped = False


@dataclass
class SubscriptionCancelledEvent(DomainEvent):
    """Event: Subscription was cancelled."""

    subscription_id: UUID = None
    user_id: UUID = None
    cancelled_by: UUID = None
    reason: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        super().__post_init__()
        self.name = 'subscription.cancelled'
        if not hasattr(self, 'data'):
            self.data = {}
        if not hasattr(self, 'propagation_stopped'):
            self.propagation_stopped = False


@dataclass
class SubscriptionExpiredEvent(DomainEvent):
    """Event: Subscription expired."""

    subscription_id: UUID = None
    user_id: UUID = None
    expired_at: datetime = None

    def __post_init__(self):
        """Set event name and timestamp."""
        super().__post_init__()
        self.name = 'subscription.expired'
        if not hasattr(self, 'data'):
            self.data = {}
        if not hasattr(self, 'propagation_stopped'):
            self.propagation_stopped = False


@dataclass
class PaymentCompletedEvent(DomainEvent):
    """Event: Payment was completed successfully."""

    subscription_id: UUID = None
    user_id: UUID = None
    transaction_id: str = None
    amount: Decimal = None
    currency: str = None

    def __post_init__(self):
        """Set event name and timestamp."""
        super().__post_init__()
        self.name = 'payment.completed'
        if not hasattr(self, 'data'):
            self.data = {}
        if not hasattr(self, 'propagation_stopped'):
            self.propagation_stopped = False


@dataclass
class PaymentFailedEvent(DomainEvent):
    """Event: Payment failed."""

    subscription_id: UUID = None
    user_id: UUID = None
    error_message: str = None

    def __post_init__(self):
        """Set event name and timestamp."""
        super().__post_init__()
        self.name = 'payment.failed'
        if not hasattr(self, 'data'):
            self.data = {}
        if not hasattr(self, 'propagation_stopped'):
            self.propagation_stopped = False
