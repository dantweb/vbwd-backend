"""Subscription service implementation."""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from src.repositories.subscription_repository import SubscriptionRepository
from src.repositories.tarif_plan_repository import TarifPlanRepository
from src.models.subscription import Subscription
from src.models.enums import SubscriptionStatus, BillingPeriod


class SubscriptionResult:
    """Result of a subscription operation."""

    def __init__(
        self,
        success: bool,
        subscription: Optional[Subscription] = None,
        error: Optional[str] = None,
    ):
        """
        Initialize subscription result.

        Args:
            success: Whether the operation succeeded.
            subscription: The subscription if successful.
            error: Error message if failed.
        """
        self.success = success
        self.subscription = subscription
        self.error = error


class ProrationResult:
    """Result of a proration calculation."""

    def __init__(self, credit: Decimal, amount_due: Decimal, days_remaining: int):
        """
        Initialize proration result.

        Args:
            credit: Credit for unused time.
            amount_due: Amount due for new plan.
            days_remaining: Days remaining on current plan.
        """
        self.credit = credit
        self.amount_due = amount_due
        self.days_remaining = days_remaining


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

    def activate_subscription(self, subscription_id: UUID) -> SubscriptionResult:
        """
        Activate subscription after payment.

        Sets status to active and calculates expiration date
        based on tariff plan billing period.

        Args:
            subscription_id: Subscription UUID

        Returns:
            SubscriptionResult with activated subscription
        """
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            return SubscriptionResult(success=False, error="Subscription not found")

        # Get plan for duration
        plan = subscription.tarif_plan
        duration_days = self.PERIOD_DAYS.get(plan.billing_period, 30)

        # Activate using model method
        subscription.activate(duration_days)
        saved = self._subscription_repo.save(subscription)

        return SubscriptionResult(success=True, subscription=saved)

    def cancel_subscription(self, subscription_id: UUID) -> SubscriptionResult:
        """
        Cancel subscription.

        Args:
            subscription_id: Subscription UUID

        Returns:
            SubscriptionResult with cancelled subscription
        """
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            return SubscriptionResult(success=False, error="Subscription not found")

        # Cancel using model method
        subscription.cancel()
        saved = self._subscription_repo.save(subscription)

        return SubscriptionResult(success=True, subscription=saved)

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

    def pause_subscription(self, subscription_id: UUID) -> SubscriptionResult:
        """
        Pause an active subscription.

        The subscription will stop being billed and the expiration
        will be extended when resumed.

        Args:
            subscription_id: Subscription UUID

        Returns:
            SubscriptionResult with paused subscription
        """
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            return SubscriptionResult(success=False, error="Subscription not found")

        if subscription.status == SubscriptionStatus.PAUSED:
            return SubscriptionResult(
                success=False, error="Subscription is already paused"
            )

        if subscription.status != SubscriptionStatus.ACTIVE:
            return SubscriptionResult(
                success=False, error="Only active subscriptions can be paused"
            )

        subscription.pause()
        saved = self._subscription_repo.save(subscription)

        return SubscriptionResult(success=True, subscription=saved)

    def resume_subscription(self, subscription_id: UUID) -> SubscriptionResult:
        """
        Resume a paused subscription.

        The expiration date is extended by the duration of the pause.

        Args:
            subscription_id: Subscription UUID

        Returns:
            SubscriptionResult with resumed subscription
        """
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            return SubscriptionResult(success=False, error="Subscription not found")

        if subscription.status != SubscriptionStatus.PAUSED:
            return SubscriptionResult(success=False, error="Subscription is not paused")

        # Calculate pause duration and extend expiration
        if subscription.paused_at and subscription.expires_at:
            paused_duration = datetime.utcnow() - subscription.paused_at
            subscription.expires_at = subscription.expires_at + paused_duration

        subscription.resume()
        saved = self._subscription_repo.save(subscription)

        return SubscriptionResult(success=True, subscription=saved)

    def calculate_proration(
        self, subscription_id: UUID, new_plan_id: UUID
    ) -> Optional[ProrationResult]:
        """
        Calculate proration for plan change.

        Returns credit for unused time and amount due for new plan.

        Args:
            subscription_id: Subscription UUID
            new_plan_id: New plan UUID

        Returns:
            ProrationResult with credit and amount due, or None if calculation fails
        """
        if not self._tarif_plan_repo:
            return None

        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            return None

        current_plan = self._tarif_plan_repo.find_by_id(subscription.tarif_plan_id)
        new_plan = self._tarif_plan_repo.find_by_id(new_plan_id)

        if not current_plan or not new_plan:
            return None

        # Calculate days remaining
        if not subscription.expires_at:
            return None

        days_remaining = max(0, (subscription.expires_at - datetime.utcnow()).days)
        total_days = self.PERIOD_DAYS.get(current_plan.billing_period, 30)

        # Credit for unused time
        daily_rate = current_plan.price / Decimal(total_days)
        credit = daily_rate * Decimal(days_remaining)

        # Amount due for new plan
        amount_due = new_plan.price - credit

        return ProrationResult(
            credit=credit.quantize(Decimal("0.01")),
            amount_due=max(amount_due, Decimal("0")).quantize(Decimal("0.01")),
            days_remaining=days_remaining,
        )

    def upgrade_subscription(
        self, subscription_id: UUID, new_plan_id: UUID
    ) -> SubscriptionResult:
        """
        Upgrade subscription to higher tier plan immediately.

        Args:
            subscription_id: Subscription UUID
            new_plan_id: New plan UUID

        Returns:
            SubscriptionResult with upgraded subscription
        """
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            return SubscriptionResult(success=False, error="Subscription not found")

        if str(subscription.tarif_plan_id) == str(new_plan_id):
            return SubscriptionResult(
                success=False, error="Already subscribed to this plan"
            )

        if subscription.status != SubscriptionStatus.ACTIVE:
            return SubscriptionResult(
                success=False, error="Only active subscriptions can be upgraded"
            )

        # Change plan immediately
        subscription.tarif_plan_id = new_plan_id
        subscription.pending_plan_id = None
        saved = self._subscription_repo.save(subscription)

        return SubscriptionResult(success=True, subscription=saved)

    def downgrade_subscription(
        self, subscription_id: UUID, new_plan_id: UUID
    ) -> SubscriptionResult:
        """
        Downgrade subscription at next renewal.

        Args:
            subscription_id: Subscription UUID
            new_plan_id: New plan UUID

        Returns:
            SubscriptionResult with subscription having pending_plan_id set
        """
        subscription = self._subscription_repo.find_by_id(subscription_id)
        if not subscription:
            return SubscriptionResult(success=False, error="Subscription not found")

        if str(subscription.tarif_plan_id) == str(new_plan_id):
            return SubscriptionResult(
                success=False, error="Already subscribed to this plan"
            )

        if subscription.status != SubscriptionStatus.ACTIVE:
            return SubscriptionResult(
                success=False, error="Only active subscriptions can be downgraded"
            )

        # Set pending plan change (takes effect at renewal)
        subscription.pending_plan_id = new_plan_id
        saved = self._subscription_repo.save(subscription)

        return SubscriptionResult(success=True, subscription=saved)
