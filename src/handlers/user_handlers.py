"""User event handlers."""
from src.events.domain import IEventHandler, DomainEvent, EventResult
from src.events.user_events import UserCreatedEvent, UserStatusUpdatedEvent, UserDeletedEvent


class UserCreatedHandler(IEventHandler):
    """
    Handler for user creation events.

    This handler can perform actions when a new user is created,
    such as sending welcome emails, creating default settings, etc.
    """

    def __init__(self):
        """Initialize handler."""
        self.handled_events = []

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler handles user.created events."""
        return isinstance(event, UserCreatedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle user creation event.

        Args:
            event: UserCreatedEvent

        Returns:
            EventResult indicating success or failure
        """
        if not isinstance(event, UserCreatedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            # Track handled events (for testing/auditing)
            self.handled_events.append(event)

            # Here you would:
            # - Send welcome email
            # - Create default user settings
            # - Log audit trail
            # - Trigger onboarding workflow

            return EventResult.success_result({
                "user_id": str(event.user_id),
                "email": event.email,
                "handled": True
            })

        except Exception as e:
            return EventResult.error_result(str(e))


class UserStatusUpdatedHandler(IEventHandler):
    """
    Handler for user status update events.

    This handler performs actions when user status changes,
    such as logging, notifications, access control updates.
    """

    def __init__(self):
        """Initialize handler."""
        self.handled_events = []

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler handles user.status.updated events."""
        return isinstance(event, UserStatusUpdatedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle user status update event.

        Args:
            event: UserStatusUpdatedEvent

        Returns:
            EventResult indicating success or failure
        """
        if not isinstance(event, UserStatusUpdatedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            # Track handled events
            self.handled_events.append(event)

            # Here you would:
            # - Log status change
            # - Send notification to user
            # - Update access control
            # - Trigger workflows based on status

            return EventResult.success_result({
                "user_id": str(event.user_id),
                "old_status": event.old_status,
                "new_status": event.new_status,
                "handled": True
            })

        except Exception as e:
            return EventResult.error_result(str(e))


class UserDeletedHandler(IEventHandler):
    """
    Handler for user deletion events.

    This handler performs cleanup when a user is deleted.
    """

    def __init__(self):
        """Initialize handler."""
        self.handled_events = []

    def can_handle(self, event: DomainEvent) -> bool:
        """Check if this handler handles user.deleted events."""
        return isinstance(event, UserDeletedEvent)

    def handle(self, event: DomainEvent) -> EventResult:
        """
        Handle user deletion event.

        Args:
            event: UserDeletedEvent

        Returns:
            EventResult indicating success or failure
        """
        if not isinstance(event, UserDeletedEvent):
            return EventResult.error_result("Invalid event type")

        try:
            # Track handled events
            self.handled_events.append(event)

            # Here you would:
            # - Clean up user data
            # - Cancel subscriptions
            # - Log audit trail
            # - Send confirmation

            return EventResult.success_result({
                "user_id": str(event.user_id),
                "handled": True
            })

        except Exception as e:
            return EventResult.error_result(str(e))
