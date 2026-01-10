"""User domain events."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from src.events.domain import DomainEvent


@dataclass
class UserCreatedEvent(DomainEvent):
    """Event: New user was created."""

    user_id: Optional[UUID] = None
    email: Optional[str] = None
    role: Optional[str] = None
    first_name: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        super().__post_init__()
        self.name = "user.created"
        if not hasattr(self, "data"):
            self.data = {}
        if not hasattr(self, "propagation_stopped"):
            self.propagation_stopped = False


@dataclass
class UserStatusUpdatedEvent(DomainEvent):
    """Event: User status was updated."""

    user_id: Optional[UUID] = None
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    updated_by: Optional[UUID] = None
    reason: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        super().__post_init__()
        self.name = "user.status.updated"
        if not hasattr(self, "data"):
            self.data = {}
        if not hasattr(self, "propagation_stopped"):
            self.propagation_stopped = False


@dataclass
class UserDeletedEvent(DomainEvent):
    """Event: User was deleted."""

    user_id: Optional[UUID] = None
    deleted_by: Optional[UUID] = None
    reason: Optional[str] = None

    def __post_init__(self):
        """Set event name and timestamp."""
        super().__post_init__()
        self.name = "user.deleted"
        if not hasattr(self, "data"):
            self.data = {}
        if not hasattr(self, "propagation_stopped"):
            self.propagation_stopped = False
