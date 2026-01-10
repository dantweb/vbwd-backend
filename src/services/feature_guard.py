"""Feature guard service for tariff-based access control."""
from typing import Optional, Dict, Tuple, Set
from uuid import UUID
from src.repositories.subscription_repository import SubscriptionRepository
from src.repositories.feature_usage_repository import FeatureUsageRepository


class FeatureGuard:
    """
    Service for tariff-based feature access control.

    Handles feature gating based on subscription plans
    and usage limits.
    """

    # Free tier features available to all users
    FREE_TIER_FEATURES: Set[str] = {
        "basic_access",
        "limited_uploads",
        "standard_support",
    }

    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        usage_repo: FeatureUsageRepository,
    ):
        """
        Initialize feature guard.

        Args:
            subscription_repo: Repository for subscription operations
            usage_repo: Repository for feature usage tracking
        """
        self.subscription_repo = subscription_repo
        self.usage_repo = usage_repo

    def can_access_feature(self, user_id: UUID, feature_name: str) -> bool:
        """
        Check if user can access a feature.

        Falls back to free tier if no active subscription.

        Args:
            user_id: User UUID
            feature_name: Name of feature to check

        Returns:
            True if user can access the feature
        """
        subscription = self.subscription_repo.get_active_subscription(user_id)

        if not subscription:
            # No subscription - check free tier
            return feature_name in self.FREE_TIER_FEATURES

        if subscription.is_expired:
            # Expired subscription - fall back to free tier
            return feature_name in self.FREE_TIER_FEATURES

        # Check plan features
        plan_features = subscription.tarif_plan.features or []
        return feature_name in plan_features

    def check_usage_limit(
        self, user_id: UUID, feature_name: str, increment: int = 1
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if user is within usage limit for a feature.

        Also increments usage if within limit.

        Args:
            user_id: User UUID
            feature_name: Name of feature to check
            increment: Amount to increment usage by

        Returns:
            Tuple of (is_within_limit, remaining_usage)
            remaining_usage is None for unlimited features
        """
        subscription = self.subscription_repo.get_active_subscription(user_id)
        if not subscription:
            return False, None

        # Get limit from plan
        limit = self._get_feature_limit(subscription.tarif_plan, feature_name)
        if limit is None:
            # Unlimited
            return True, None

        # Get current usage
        period_start = subscription.current_period_start or subscription.start_date
        current_usage = self.usage_repo.get_monthly_usage(
            user_id, feature_name, period_start
        )

        remaining = limit - current_usage
        if remaining >= increment:
            # Within limit - increment usage
            self.usage_repo.increment_usage(
                user_id, feature_name, period_start, increment
            )
            return True, remaining - increment

        return False, remaining

    def get_feature_limits(self, user_id: UUID) -> Dict[str, dict]:
        """
        Get all feature limits and current usage for a user.

        Args:
            user_id: User UUID

        Returns:
            Dictionary of feature_name -> {limit, used, remaining}
        """
        subscription = self.subscription_repo.get_active_subscription(user_id)
        if not subscription:
            return {}

        limits = self._get_plan_limits(subscription.tarif_plan)
        if not limits:
            return {}

        period_start = subscription.current_period_start or subscription.start_date
        result = {}

        for feature_name, limit in limits.items():
            usage = self.usage_repo.get_monthly_usage(
                user_id, feature_name, period_start
            )
            result[feature_name] = {
                "limit": limit,
                "used": usage,
                "remaining": max(0, limit - usage),
            }

        return result

    def get_user_features(self, user_id: UUID) -> Set[str]:
        """
        Get all features available to a user.

        Args:
            user_id: User UUID

        Returns:
            Set of available feature names
        """
        subscription = self.subscription_repo.get_active_subscription(user_id)

        if not subscription or subscription.is_expired:
            return self.FREE_TIER_FEATURES.copy()

        plan_features = set(subscription.tarif_plan.features or [])
        return plan_features | self.FREE_TIER_FEATURES

    def _get_feature_limit(self, tarif_plan, feature_name: str) -> Optional[int]:
        """
        Get limit for a specific feature from plan.

        Args:
            tarif_plan: TarifPlan model
            feature_name: Name of feature

        Returns:
            Limit value or None for unlimited
        """
        limits = self._get_plan_limits(tarif_plan)
        return limits.get(feature_name)

    def _get_plan_limits(self, tarif_plan) -> Dict[str, int]:
        """
        Get all limits from a tarif plan.

        Limits are stored in the plan's features JSON
        under a 'limits' key.

        Args:
            tarif_plan: TarifPlan model

        Returns:
            Dictionary of feature_name -> limit
        """
        features = tarif_plan.features or []

        # Check if features contains a limits dict
        # Could be structured as {"limits": {...}} or just a list
        if isinstance(features, dict):
            return features.get("limits", {})

        # If it's a list, there are no limits defined
        return {}
