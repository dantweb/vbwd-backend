"""Subscription service implementation."""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from src.repositories.subscription_repository import SubscriptionRepository
from src.repositories.tarif_plan_repository import TarifPlanRepository
from src.models.subscription import Subscription
from src.models.enums import SubscriptionStatus, BillingPeriod


class SubscriptionService:
    """
    Subscription lifecycle management service.

    Handles subscription creation, activation, cancellation, and retrieval.
    """

    # Duration in days for each billing period
    PERIOD_DAYS = {
        BillingPeriod.MONTHLY: 30,
        BillingPeriod.QUARTERLY: 90,
        BillingPeriod.YEARLY: 365,
        BillingPeriod.ONE_TIME: 36500,  # ~100 years for lifetime
    }

    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        tarif_plan_repo: Optional[TarifPlanRepository] = None,
    ):
        """Initialize SubscriptionService.

        Args:
            subscription_repo: Repository for subscription data access
            tarif_plan_repo: Optional repository for tariff plan validation
        """
        self._subscription_repo = subscription_repo
        self._tarif_plan_repo = tarif_plan_repo

    def get_active_subscription(self, user_id: UUID) -> Optional[Subscription]:
        """Get user's active subscription.

        Args:
            user_id: User UUID

        Returns:
            Active subscription if found, None otherwise
        """
        return self._subscription_repo.find_active_by_user(user_id)

    def get_user_subscriptions(self, user_id: UUID) -> List[Subscription]:
        """Get all user subscriptions.

        Args:
            user_id: User UUID

        Returns:
            List of all user subscriptions
        """
        return self._subscription_repo.find_by_user(user_id)

    def create_subscription(
        self,
        user_id: UUID,
        tarif_plan_id: UUID,
    ) -> Subscription:
        """
        Create new subscription (pending until payment).

        Args:
            user_id: User UUID
            tarif_plan_id: Tariff plan UUID

        Returns:
            Created subscription with pending status

        Raises:
            ValueError: If plan not found or not active
        """
        # Verify plan exists and is active
        if self._tarif_plan_repo:
            plan = self._tarif_plan_repo.find_by_id(tarif_plan_id)
            if not plan:
                raise ValueError(f"Tariff plan {tarif_plan_id} not found")
            if not plan.is_active:
                raise ValueError(f"Tariff plan {tarif_plan_id} is not active")

        subscription = Subscription()
        subscription.user_id = user_id
        subscription.tarif_plan_id = tarif_plan_id
        subscription.status = SubscriptionStatus.PENDING

        return self._subscription_repo.save(subscription)

    def activate_subscription(self, subscription_id: UUID) -> Subscription:
        """
        Activate subscription after payment.

        Sets status to active and calculates expiration date
        based on tariff plan billing period.

        Args:
            subscription_id: Subscription UUID

        Returns:
            Activated subscription

        Raises:
            ValueError: If subscription not found
        """
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        # Get plan for duration
        plan = subscription.tarif_plan
        duration_days = self.PERIOD_DAYS.get(plan.billing_period, 30)

        # Activate using model method
        subscription.activate(duration_days)

        return self._subscription_repo.save(subscription)

    def cancel_subscription(self, subscription_id: UUID) -> Subscription:
        """
        Cancel subscription.

        Args:
            subscription_id: Subscription UUID

        Returns:
            Cancelled subscription

        Raises:
            ValueError: If subscription not found
        """
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        # Cancel using model method
        subscription.cancel()

        return self._subscription_repo.save(subscription)

    def renew_subscription(self, subscription_id: UUID) -> Subscription:
        """
        Renew an expired subscription.

        Args:
            subscription_id: Subscription UUID

        Returns:
            Renewed subscription

        Raises:
            ValueError: If subscription not found
        """
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        # Get plan for duration
        plan = subscription.tarif_plan
        duration_days = self.PERIOD_DAYS.get(plan.billing_period, 30)

        # Reactivate
        subscription.activate(duration_days)

        return self._subscription_repo.save(subscription)

    def get_expiring_subscriptions(self, days: int = 7) -> List[Subscription]:
        """
        Get subscriptions expiring within specified days.

        Useful for sending renewal reminders.

        Args:
            days: Number of days threshold

        Returns:
            List of expiring subscriptions
        """
        return self._subscription_repo.find_expiring_soon(days)

    def expire_subscriptions(self) -> List[Subscription]:
        """
        Find and mark expired subscriptions.

        Returns:
            List of expired subscriptions
        """
        expired = self._subscription_repo.find_expired()

        for subscription in expired:
            subscription.expire()
            self._subscription_repo.save(subscription)

        return expired
