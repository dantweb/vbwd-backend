"""Tests for user event handlers."""
import pytest
from uuid import uuid4
from src.handlers.user_handlers import (
    UserCreatedHandler,
    UserStatusUpdatedHandler,
    UserDeletedHandler,
)
from src.events.user_events import (
    UserCreatedEvent,
    UserStatusUpdatedEvent,
    UserDeletedEvent,
)
from src.events.domain import DomainEvent


class TestUserCreatedHandler:
    """Test cases for UserCreatedHandler."""

    @pytest.fixture
    def handler(self):
        """Create UserCreatedHandler."""
        return UserCreatedHandler()

    def test_can_handle_returns_true_for_user_created_event(self, handler):
        """can_handle should return True for UserCreatedEvent."""
        event = UserCreatedEvent(user_id=uuid4(), email="test@example.com", role="user")

        assert handler.can_handle(event) is True

    def test_can_handle_returns_false_for_other_events(self, handler):
        """can_handle should return False for non-UserCreatedEvent."""
        event = DomainEvent(name="other.event")

        assert handler.can_handle(event) is False

    def test_handle_processes_user_created_event(self, handler):
        """handle should process UserCreatedEvent successfully."""
        user_id = uuid4()
        event = UserCreatedEvent(user_id=user_id, email="test@example.com", role="user")

        result = handler.handle(event)

        assert result.success is True
        assert result.data["user_id"] == str(user_id)
        assert result.data["email"] == "test@example.com"
        assert len(handler.handled_events) == 1

    def test_handle_returns_error_for_invalid_event(self, handler):
        """handle should return error for invalid event type."""
        event = DomainEvent(name="other.event")

        result = handler.handle(event)

        assert result.success is False
        assert "Invalid event type" in result.error


class TestUserStatusUpdatedHandler:
    """Test cases for UserStatusUpdatedHandler."""

    @pytest.fixture
    def handler(self):
        """Create UserStatusUpdatedHandler."""
        return UserStatusUpdatedHandler()

    def test_can_handle_returns_true_for_user_status_updated_event(self, handler):
        """can_handle should return True for UserStatusUpdatedEvent."""
        event = UserStatusUpdatedEvent(
            user_id=uuid4(), old_status="active", new_status="suspended"
        )

        assert handler.can_handle(event) is True

    def test_handle_processes_status_update_event(self, handler):
        """handle should process UserStatusUpdatedEvent successfully."""
        user_id = uuid4()
        event = UserStatusUpdatedEvent(
            user_id=user_id,
            old_status="active",
            new_status="suspended",
            reason="Policy violation",
        )

        result = handler.handle(event)

        assert result.success is True
        assert result.data["old_status"] == "active"
        assert result.data["new_status"] == "suspended"
        assert len(handler.handled_events) == 1


class TestUserDeletedHandler:
    """Test cases for UserDeletedHandler."""

    @pytest.fixture
    def handler(self):
        """Create UserDeletedHandler."""
        return UserDeletedHandler()

    def test_can_handle_returns_true_for_user_deleted_event(self, handler):
        """can_handle should return True for UserDeletedEvent."""
        event = UserDeletedEvent(user_id=uuid4(), deleted_by=uuid4())

        assert handler.can_handle(event) is True

    def test_handle_processes_user_deleted_event(self, handler):
        """handle should process UserDeletedEvent successfully."""
        user_id = uuid4()
        event = UserDeletedEvent(
            user_id=user_id, deleted_by=uuid4(), reason="User request"
        )

        result = handler.handle(event)

        assert result.success is True
        assert result.data["user_id"] == str(user_id)
        assert len(handler.handled_events) == 1
