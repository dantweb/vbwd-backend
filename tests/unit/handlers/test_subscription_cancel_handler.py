"""Tests for SubscriptionCancelledHandler (event-driven cancellation).

The handler receives SubscriptionCancelledEvent (from Stripe webhook or admin),
marks the subscription CANCELLED, sets cancelled_at, and also cancels linked
active add-on subscriptions. It never calls any external APIs directly.
"""
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import MagicMock

from src.handlers.subscription_cancel_handler import SubscriptionCancelledHandler
from src.events.payment_events import SubscriptionCancelledEvent
from src.events.domain import EventResult
from src.models.enums import SubscriptionStatus


@pytest.fixture
def mock_container(mocker):
    """Mock DI container with subscription and addon_subscription repos."""
    container = mocker.MagicMock()
    container.subscription_repository.return_value = mocker.MagicMock()
    container.addon_subscription_repository.return_value = mocker.MagicMock()
    return container


@pytest.fixture
def handler(mock_container):
    """Create SubscriptionCancelledHandler with mocked container."""
    return SubscriptionCancelledHandler(container=mock_container)


@pytest.fixture
def subscription():
    """Active subscription mock."""
    sub = MagicMock()
    sub.id = uuid4()
    sub.user_id = uuid4()
    sub.status = SubscriptionStatus.ACTIVE
    sub.cancelled_at = None
    return sub


@pytest.fixture
def event(subscription):
    """SubscriptionCancelledEvent for the fixture subscription."""
    return SubscriptionCancelledEvent(
        subscription_id=subscription.id,
        user_id=subscription.user_id,
        reason="stripe_subscription_deleted",
        provider="stripe",
    )


class TestSubscriptionCancelledHandler:
    """Tests for SubscriptionCancelledHandler."""

    def test_cancels_active_subscription(
        self, handler, mock_container, subscription, event
    ):
        """Handler should set status=CANCELLED and cancelled_at on active subscription."""
        sub_repo = mock_container.subscription_repository.return_value
        sub_repo.find_by_id.return_value = subscription
        mock_container.addon_subscription_repository.return_value.find_by_subscription.return_value = (
            []
        )

        result = handler.handle(event)

        assert result.success is True
        assert subscription.status == SubscriptionStatus.CANCELLED
        assert subscription.cancelled_at is not None
        assert isinstance(subscription.cancelled_at, datetime)
        sub_repo.save.assert_called_with(subscription)

    def test_cancels_linked_addon_subscriptions(
        self, handler, mock_container, subscription, event
    ):
        """Handler should also cancel active add-on subscriptions linked to the subscription."""
        sub_repo = mock_container.subscription_repository.return_value
        sub_repo.find_by_id.return_value = subscription

        addon_sub_1 = MagicMock()
        addon_sub_1.status = SubscriptionStatus.ACTIVE
        addon_sub_1.cancelled_at = None

        addon_sub_2 = MagicMock()
        addon_sub_2.status = SubscriptionStatus.ACTIVE
        addon_sub_2.cancelled_at = None

        addon_repo = mock_container.addon_subscription_repository.return_value
        addon_repo.find_by_subscription.return_value = [addon_sub_1, addon_sub_2]

        result = handler.handle(event)

        assert result.success is True
        assert addon_sub_1.status == SubscriptionStatus.CANCELLED
        assert addon_sub_1.cancelled_at is not None
        assert addon_sub_2.status == SubscriptionStatus.CANCELLED
        assert addon_sub_2.cancelled_at is not None
        assert addon_repo.save.call_count == 2

    def test_skips_already_cancelled(self, handler, mock_container, event):
        """Handler should succeed without error if subscription is already cancelled."""
        sub = MagicMock()
        sub.id = event.subscription_id
        sub.status = SubscriptionStatus.CANCELLED
        sub_repo = mock_container.subscription_repository.return_value
        sub_repo.find_by_id.return_value = sub

        result = handler.handle(event)

        assert result.success is True
        sub_repo.save.assert_not_called()

    def test_skips_missing_subscription(self, handler, mock_container, event):
        """Handler should succeed without error if subscription is not found."""
        sub_repo = mock_container.subscription_repository.return_value
        sub_repo.find_by_id.return_value = None

        result = handler.handle(event)

        assert result.success is True

    def test_event_driven_no_direct_stripe_calls(
        self, handler, mock_container, subscription, event
    ):
        """Handler should ONLY use repositories -- no Stripe API calls."""
        sub_repo = mock_container.subscription_repository.return_value
        sub_repo.find_by_id.return_value = subscription
        mock_container.addon_subscription_repository.return_value.find_by_subscription.return_value = (
            []
        )

        handler.handle(event)

        # The handler should only interact with repos, never with external APIs.
        # Verify it accessed repos through the container.
        mock_container.subscription_repository.assert_called()
        mock_container.addon_subscription_repository.assert_called()
        # No other container methods (like event_dispatcher or sdk_registry) should be called.
        mock_container.event_dispatcher.assert_not_called()

    def test_returns_success_result(self, handler, mock_container, subscription, event):
        """Handler should return EventResult with success=True."""
        sub_repo = mock_container.subscription_repository.return_value
        sub_repo.find_by_id.return_value = subscription
        mock_container.addon_subscription_repository.return_value.find_by_subscription.return_value = (
            []
        )

        result = handler.handle(event)

        assert isinstance(result, EventResult)
        assert result.success is True
