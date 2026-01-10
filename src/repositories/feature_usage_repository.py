"""Feature usage repository."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from src.repositories.base import BaseRepository
from src.models.feature_usage import FeatureUsage


class FeatureUsageRepository(BaseRepository[FeatureUsage]):
    """Repository for feature usage tracking."""

    def __init__(self, session):
        """Initialize with FeatureUsage model."""
        super().__init__(session, FeatureUsage)

    def get_usage(
        self, user_id: UUID, feature_name: str, period_start: datetime
    ) -> Optional[FeatureUsage]:
        """
        Get usage record for user/feature/period.

        Args:
            user_id: User UUID
            feature_name: Name of the feature
            period_start: Start of billing period

        Returns:
            FeatureUsage record or None
        """
        return (
            self._session.query(FeatureUsage)
            .filter(
                FeatureUsage.user_id == user_id,
                FeatureUsage.feature_name == feature_name,
                FeatureUsage.period_start == period_start,
            )
            .first()
        )

    def get_monthly_usage(
        self, user_id: UUID, feature_name: str, period_start: datetime
    ) -> int:
        """
        Get usage count for a feature in the current period.

        Args:
            user_id: User UUID
            feature_name: Name of the feature
            period_start: Start of billing period

        Returns:
            Usage count (0 if no record exists)
        """
        record = self.get_usage(user_id, feature_name, period_start)
        return record.usage_count if record else 0

    def increment_usage(
        self, user_id: UUID, feature_name: str, period_start: datetime, amount: int = 1
    ) -> int:
        """
        Increment usage for a feature.

        Creates record if it doesn't exist.

        Args:
            user_id: User UUID
            feature_name: Name of the feature
            period_start: Start of billing period
            amount: Amount to increment (default 1)

        Returns:
            New usage count
        """
        record = self.get_usage(user_id, feature_name, period_start)

        if record:
            record.increment(amount)
        else:
            record = FeatureUsage(
                user_id=user_id,
                feature_name=feature_name,
                period_start=period_start,
                usage_count=amount,
            )
            self._session.add(record)

        self._session.commit()
        return record.usage_count

    def reset_usage(
        self, user_id: UUID, feature_name: str, period_start: datetime
    ) -> bool:
        """
        Reset usage count to zero.

        Args:
            user_id: User UUID
            feature_name: Name of the feature
            period_start: Start of billing period

        Returns:
            True if reset, False if no record found
        """
        record = self.get_usage(user_id, feature_name, period_start)
        if record:
            record.usage_count = 0
            self._session.commit()
            return True
        return False

    def get_all_usage_for_user(self, user_id: UUID, period_start: datetime) -> dict:
        """
        Get all feature usage for a user in a period.

        Args:
            user_id: User UUID
            period_start: Start of billing period

        Returns:
            Dictionary of feature_name -> usage_count
        """
        records = (
            self._session.query(FeatureUsage)
            .filter(
                FeatureUsage.user_id == user_id,
                FeatureUsage.period_start == period_start,
            )
            .all()
        )

        return {r.feature_name: r.usage_count for r in records}
