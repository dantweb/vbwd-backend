"""Tests for Feature Guard service."""
import pytest
from unittest.mock import Mock
from uuid import uuid4
from datetime import datetime
from src.services.feature_guard import FeatureGuard


class TestFeatureGuard:
    """Test cases for FeatureGuard."""

    @pytest.fixture
    def mock_subscription_repo(self):
        """Create mock subscription repository."""
        return Mock()

    @pytest.fixture
    def mock_usage_repo(self):
        """Create mock feature usage repository."""
        return Mock()

    @pytest.fixture
    def feature_guard(self, mock_subscription_repo, mock_usage_repo):
        """Create feature guard with mock repositories."""
        return FeatureGuard(mock_subscription_repo, mock_usage_repo)

    @pytest.fixture
    def mock_subscription(self):
        """Create mock subscription with plan."""
        sub = Mock()
        sub.is_expired = False
        sub.tarif_plan = Mock()
        sub.tarif_plan.features = ["premium_feature", "api_access"]
        sub.current_period_start = datetime(2024, 1, 1)
        sub.start_date = datetime(2024, 1, 1)
        return sub

    def test_can_access_feature_with_active_subscription(
        self, feature_guard, mock_subscription_repo, mock_subscription
    ):
        """User with plan containing feature can access."""
        user_id = uuid4()
        mock_subscription_repo.find_active_by_user.return_value = mock_subscription

        result = feature_guard.can_access_feature(user_id, "premium_feature")

        assert result is True

    def test_cannot_access_feature_not_in_plan(
        self, feature_guard, mock_subscription_repo, mock_subscription
    ):
        """User without feature in plan is denied."""
        user_id = uuid4()
        mock_subscription_repo.find_active_by_user.return_value = mock_subscription

        result = feature_guard.can_access_feature(user_id, "enterprise_only")

        assert result is False

    def test_expired_subscription_uses_free_tier(
        self, feature_guard, mock_subscription_repo, mock_subscription
    ):
        """Expired subscription falls back to free tier."""
        user_id = uuid4()
        mock_subscription.is_expired = True
        mock_subscription_repo.find_active_by_user.return_value = mock_subscription

        # Free tier feature should be accessible
        result = feature_guard.can_access_feature(user_id, "basic_access")
        assert result is True

        # Premium feature should not be accessible
        result = feature_guard.can_access_feature(user_id, "premium_feature")
        assert result is False

    def test_no_subscription_uses_free_tier(
        self, feature_guard, mock_subscription_repo
    ):
        """No subscription falls back to free tier."""
        user_id = uuid4()
        mock_subscription_repo.find_active_by_user.return_value = None

        result = feature_guard.can_access_feature(user_id, "basic_access")
        assert result is True

        result = feature_guard.can_access_feature(user_id, "premium_feature")
        assert result is False

    def test_usage_limit_enforced(
        self, feature_guard, mock_subscription_repo, mock_usage_repo, mock_subscription
    ):
        """Feature usage limits enforced."""
        user_id = uuid4()
        mock_subscription.tarif_plan.features = {"limits": {"api_calls": 100}}
        mock_subscription_repo.find_active_by_user.return_value = mock_subscription
        mock_usage_repo.get_monthly_usage.return_value = 99  # 1 remaining

        allowed, remaining = feature_guard.check_usage_limit(user_id, "api_calls", 1)

        assert allowed is True
        assert remaining == 0

    def test_usage_limit_exceeded(
        self, feature_guard, mock_subscription_repo, mock_usage_repo, mock_subscription
    ):
        """Denies when usage limit exceeded."""
        user_id = uuid4()
        mock_subscription.tarif_plan.features = {"limits": {"api_calls": 100}}
        mock_subscription_repo.find_active_by_user.return_value = mock_subscription
        mock_usage_repo.get_monthly_usage.return_value = 100  # At limit

        allowed, remaining = feature_guard.check_usage_limit(user_id, "api_calls", 1)

        assert allowed is False
        assert remaining == 0

    def test_unlimited_feature_returns_none_remaining(
        self, feature_guard, mock_subscription_repo, mock_usage_repo, mock_subscription
    ):
        """Unlimited features return None for remaining."""
        user_id = uuid4()
        mock_subscription.tarif_plan.features = []  # No limits defined
        mock_subscription_repo.find_active_by_user.return_value = mock_subscription

        allowed, remaining = feature_guard.check_usage_limit(
            user_id, "unlimited_feature"
        )

        assert allowed is True
        assert remaining is None

    def test_get_feature_limits_returns_usage_stats(
        self, feature_guard, mock_subscription_repo, mock_usage_repo, mock_subscription
    ):
        """Returns all feature limits and usage stats."""
        user_id = uuid4()
        mock_subscription.tarif_plan.features = {
            "limits": {"api_calls": 100, "exports": 10}
        }
        mock_subscription_repo.find_active_by_user.return_value = mock_subscription
        mock_usage_repo.get_monthly_usage.side_effect = [50, 3]  # api_calls, exports

        result = feature_guard.get_feature_limits(user_id)

        assert "api_calls" in result
        assert result["api_calls"]["limit"] == 100
        assert result["api_calls"]["used"] == 50
        assert result["api_calls"]["remaining"] == 50

        assert "exports" in result
        assert result["exports"]["limit"] == 10
        assert result["exports"]["used"] == 3
        assert result["exports"]["remaining"] == 7

    def test_get_feature_limits_empty_without_subscription(
        self, feature_guard, mock_subscription_repo
    ):
        """Returns empty dict without subscription."""
        user_id = uuid4()
        mock_subscription_repo.find_active_by_user.return_value = None

        result = feature_guard.get_feature_limits(user_id)

        assert result == {}

    def test_get_user_features_combines_plan_and_free_tier(
        self, feature_guard, mock_subscription_repo, mock_subscription
    ):
        """Returns union of plan features and free tier."""
        user_id = uuid4()
        mock_subscription_repo.find_active_by_user.return_value = mock_subscription

        result = feature_guard.get_user_features(user_id)

        # Should include plan features
        assert "premium_feature" in result
        assert "api_access" in result
        # Should include free tier
        assert "basic_access" in result

    def test_check_usage_limit_no_subscription(
        self, feature_guard, mock_subscription_repo
    ):
        """Returns False when no subscription."""
        user_id = uuid4()
        mock_subscription_repo.find_active_by_user.return_value = None

        allowed, remaining = feature_guard.check_usage_limit(user_id, "api_calls")

        assert allowed is False
        assert remaining is None

    def test_check_usage_limit_increments_on_success(
        self, feature_guard, mock_subscription_repo, mock_usage_repo, mock_subscription
    ):
        """Increments usage when within limit."""
        user_id = uuid4()
        mock_subscription.tarif_plan.features = {"limits": {"api_calls": 100}}
        mock_subscription_repo.find_active_by_user.return_value = mock_subscription
        mock_usage_repo.get_monthly_usage.return_value = 50

        feature_guard.check_usage_limit(user_id, "api_calls", 5)

        mock_usage_repo.increment_usage.assert_called_once()
