"""Tests for SubscriptionService."""
import pytest
from unittest.mock import Mock
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4


class TestSubscriptionServiceCreate:
    """Test cases for creating subscriptions."""

    @pytest.fixture
    def mock_sub_repo(self):
        """Mock SubscriptionRepository."""
        return Mock()

    @pytest.fixture
    def mock_plan_repo(self):
        """Mock TarifPlanRepository."""
        return Mock()

    @pytest.fixture
    def subscription_service(self, mock_sub_repo, mock_plan_repo):
        """Create SubscriptionService with mocked dependencies."""
        from src.services.subscription_service import SubscriptionService
        return SubscriptionService(
            subscription_repo=mock_sub_repo,
            tarif_plan_repo=mock_plan_repo,
        )

    def test_create_subscription_creates_pending(self, subscription_service, mock_sub_repo, mock_plan_repo):
        """create_subscription should create pending subscription."""
        from src.models.subscription import Subscription
        from src.models.tarif_plan import TarifPlan
        from src.models.enums import SubscriptionStatus, BillingPeriod

        plan_id = uuid4()
        user_id = uuid4()

        plan = TarifPlan()
        plan.id = plan_id
        plan.name = "Pro"
        plan.billing_period = BillingPeriod.MONTHLY
        plan.price_float = 29.99
        plan.is_active = True

        mock_plan_repo.find_by_id.return_value = plan

        subscription = Subscription()
        subscription.id = uuid4()
        subscription.user_id = user_id
        subscription.tarif_plan_id = plan_id
        subscription.status = SubscriptionStatus.PENDING

        mock_sub_repo.save.return_value = subscription

        result = subscription_service.create_subscription(user_id=user_id, tarif_plan_id=plan_id)

        assert result.status == SubscriptionStatus.PENDING
        mock_sub_repo.save.assert_called_once()
        mock_plan_repo.find_by_id.assert_called_once_with(plan_id)

    def test_create_subscription_raises_if_plan_not_found(self, subscription_service, mock_plan_repo):
        """create_subscription should raise error if plan not found."""
        plan_id = uuid4()
        user_id = uuid4()

        mock_plan_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            subscription_service.create_subscription(user_id=user_id, tarif_plan_id=plan_id)

    def test_create_subscription_raises_if_plan_inactive(self, subscription_service, mock_plan_repo):
        """create_subscription should raise error if plan is inactive."""
        from src.models.tarif_plan import TarifPlan

        plan_id = uuid4()
        user_id = uuid4()

        plan = TarifPlan()
        plan.id = plan_id
        plan.is_active = False

        mock_plan_repo.find_by_id.return_value = plan

        with pytest.raises(ValueError, match="not active"):
            subscription_service.create_subscription(user_id=user_id, tarif_plan_id=plan_id)


class TestSubscriptionServiceActivate:
    """Test cases for activating subscriptions."""

    @pytest.fixture
    def mock_sub_repo(self):
        """Mock SubscriptionRepository."""
        return Mock()

    @pytest.fixture
    def subscription_service(self, mock_sub_repo):
        """Create SubscriptionService with mocked dependencies."""
        from src.services.subscription_service import SubscriptionService
        return SubscriptionService(subscription_repo=mock_sub_repo)

    def test_activate_subscription_sets_dates(self, subscription_service, mock_sub_repo):
        """activate_subscription should set status and dates."""
        from src.models.subscription import Subscription
        from src.models.tarif_plan import TarifPlan
        from src.models.enums import SubscriptionStatus, BillingPeriod

        sub_id = uuid4()
        plan_id = uuid4()
        user_id = uuid4()

        plan = TarifPlan()
        plan.id = plan_id
        plan.billing_period = BillingPeriod.MONTHLY

        subscription = Subscription()
        subscription.id = sub_id
        subscription.user_id = user_id
        subscription.tarif_plan_id = plan_id
        subscription.status = SubscriptionStatus.PENDING
        subscription.tarif_plan = plan

        mock_sub_repo.find_by_id.return_value = subscription
        mock_sub_repo.save.return_value = subscription

        result = subscription_service.activate_subscription(sub_id)

        assert result.status == SubscriptionStatus.ACTIVE
        assert result.started_at is not None
        assert result.expires_at is not None
        mock_sub_repo.save.assert_called_once()

    def test_activate_subscription_raises_if_not_found(self, subscription_service, mock_sub_repo):
        """activate_subscription should raise error if not found."""
        sub_id = uuid4()
        mock_sub_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            subscription_service.activate_subscription(sub_id)


class TestSubscriptionServiceGetActive:
    """Test cases for getting active subscriptions."""

    @pytest.fixture
    def mock_sub_repo(self):
        """Mock SubscriptionRepository."""
        return Mock()

    @pytest.fixture
    def subscription_service(self, mock_sub_repo):
        """Create SubscriptionService with mocked dependencies."""
        from src.services.subscription_service import SubscriptionService
        return SubscriptionService(subscription_repo=mock_sub_repo)

    def test_get_active_subscription_returns_valid(self, subscription_service, mock_sub_repo):
        """get_active_subscription should return valid subscription."""
        from src.models.subscription import Subscription
        from src.models.enums import SubscriptionStatus

        user_id = uuid4()

        subscription = Subscription()
        subscription.id = uuid4()
        subscription.user_id = user_id
        subscription.tarif_plan_id = uuid4()
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.expires_at = datetime.utcnow() + timedelta(days=30)

        mock_sub_repo.find_active_by_user.return_value = subscription

        result = subscription_service.get_active_subscription(user_id=user_id)

        assert result is not None
        assert result.is_valid is True
        mock_sub_repo.find_active_by_user.assert_called_once_with(user_id)

    def test_get_active_subscription_returns_none_if_not_found(self, subscription_service, mock_sub_repo):
        """get_active_subscription should return None if no active subscription."""
        user_id = uuid4()
        mock_sub_repo.find_active_by_user.return_value = None

        result = subscription_service.get_active_subscription(user_id=user_id)

        assert result is None


class TestSubscriptionServiceCancel:
    """Test cases for canceling subscriptions."""

    @pytest.fixture
    def mock_sub_repo(self):
        """Mock SubscriptionRepository."""
        return Mock()

    @pytest.fixture
    def subscription_service(self, mock_sub_repo):
        """Create SubscriptionService with mocked dependencies."""
        from src.services.subscription_service import SubscriptionService
        return SubscriptionService(subscription_repo=mock_sub_repo)

    def test_cancel_subscription_sets_status(self, subscription_service, mock_sub_repo):
        """cancel_subscription should set cancelled status."""
        from src.models.subscription import Subscription
        from src.models.enums import SubscriptionStatus

        sub_id = uuid4()

        subscription = Subscription()
        subscription.id = sub_id
        subscription.user_id = uuid4()
        subscription.tarif_plan_id = uuid4()
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.started_at = datetime.utcnow()
        subscription.expires_at = datetime.utcnow() + timedelta(days=30)

        mock_sub_repo.find_by_id.return_value = subscription
        mock_sub_repo.save.return_value = subscription

        result = subscription_service.cancel_subscription(sub_id)

        assert result.status == SubscriptionStatus.CANCELLED
        assert result.cancelled_at is not None
        mock_sub_repo.save.assert_called_once()

    def test_cancel_subscription_raises_if_not_found(self, subscription_service, mock_sub_repo):
        """cancel_subscription should raise error if not found."""
        sub_id = uuid4()
        mock_sub_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            subscription_service.cancel_subscription(sub_id)


class TestSubscriptionServiceGetUserSubscriptions:
    """Test cases for getting user subscriptions."""

    @pytest.fixture
    def mock_sub_repo(self):
        """Mock SubscriptionRepository."""
        return Mock()

    @pytest.fixture
    def subscription_service(self, mock_sub_repo):
        """Create SubscriptionService with mocked dependencies."""
        from src.services.subscription_service import SubscriptionService
        return SubscriptionService(subscription_repo=mock_sub_repo)

    def test_get_user_subscriptions_returns_list(self, subscription_service, mock_sub_repo):
        """get_user_subscriptions should return all user subscriptions."""
        from src.models.subscription import Subscription
        from src.models.enums import SubscriptionStatus

        user_id = uuid4()

        sub1 = Subscription()
        sub1.id = uuid4()
        sub1.user_id = user_id
        sub1.status = SubscriptionStatus.ACTIVE

        sub2 = Subscription()
        sub2.id = uuid4()
        sub2.user_id = user_id
        sub2.status = SubscriptionStatus.EXPIRED

        subscriptions = [sub1, sub2]
        mock_sub_repo.find_by_user.return_value = subscriptions

        result = subscription_service.get_user_subscriptions(user_id=user_id)

        assert len(result) == 2
        mock_sub_repo.find_by_user.assert_called_once_with(user_id)
