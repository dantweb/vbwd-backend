"""Subscription repository implementation."""
from typing import Optional, List, Union
from uuid import UUID
from datetime import datetime
from src.repositories.base import BaseRepository
from src.models import Subscription, SubscriptionStatus


class SubscriptionRepository(BaseRepository[Subscription]):
    """Repository for Subscription entity operations."""

    def __init__(self, session):
        super().__init__(session=session, model=Subscription)

    def find_by_user(self, user_id: Union[UUID, str]) -> List[Subscription]:
        """Find all subscriptions for a user."""
        return (
            self._session.query(Subscription)
            .filter(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
            .all()
        )

    def find_active_by_user(self, user_id: Union[UUID, str]) -> Optional[Subscription]:
        """Find active subscription for a user."""
        return (
            self._session.query(Subscription)
            .filter(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
            .first()
        )

    def find_expiring_soon(self, days: int = 7) -> List[Subscription]:
        """Find subscriptions expiring within specified days."""
        from datetime import timedelta
        threshold = datetime.utcnow() + timedelta(days=days)
        return (
            self._session.query(Subscription)
            .filter(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.expires_at <= threshold,
            )
            .all()
        )

    def find_expired(self) -> List[Subscription]:
        """Find subscriptions that have expired."""
        return (
            self._session.query(Subscription)
            .filter(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.expires_at < datetime.utcnow(),
            )
            .all()
        )
