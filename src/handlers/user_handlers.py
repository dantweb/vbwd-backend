"""User event handlers."""
from typing import Optional
from src.events.domain import IEventHandler, DomainEvent, EventResult
from src.events.user_events import UserCreatedEvent, UserStatusUpdatedEvent, UserDeletedEvent


class UserCreatedHandler(IEventHandler):
    """
    Handler for user creation events.

    This handler can perform actions when a new user is created,
    such as sending welcome emails, creating default settings, etc.
    """

    def __init__(self, email_service=None):
        """
        Initialize handler.

        Args:
            email_service: Optional EmailService for sending welcome emails.
        """
        self.handled_events = []
        self._email_service = email_service

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

            email_sent = False

            # Send welcome email if email service available
            if self._email_service and event.email:
                first_name = getattr(event, 'first_name', None) or 'User'
                result = self._email_service.send_welcome_email(
                    to_email=event.email,
                    first_name=first_name
                )
                email_sent = result.success

            return EventResult.success_result({
                "user_id": str(event.user_id),
                "email": event.email,
                "email_sent": email_sent,
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
