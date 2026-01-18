"""TokenBundle repository implementation."""
from typing import Optional, List, Tuple
from src.repositories.base import BaseRepository
from src.models import TokenBundle


class TokenBundleRepository(BaseRepository[TokenBundle]):
    """Repository for TokenBundle entity operations."""

    def __init__(self, session):
        super().__init__(session=session, model=TokenBundle)

    def find_active(self) -> List[TokenBundle]:
        """Find all active token bundles ordered by sort_order."""
        return (
            self._session.query(TokenBundle)
            .filter(TokenBundle.is_active.is_(True))
            .order_by(TokenBundle.sort_order, TokenBundle.name)
            .all()
        )

    def find_all_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        include_inactive: bool = True,
    ) -> Tuple[List[TokenBundle], int]:
        """
        Find all token bundles with pagination.

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            include_inactive: Include inactive bundles

        Returns:
            Tuple of (bundles list, total count)
        """
        query = self._session.query(TokenBundle)

        if not include_inactive:
            query = query.filter(TokenBundle.is_active.is_(True))

        total = query.count()

        bundles = (
            query.order_by(TokenBundle.sort_order, TokenBundle.name)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return bundles, total

    def count_active(self) -> int:
        """Count active token bundles."""
        return (
            self._session.query(TokenBundle)
            .filter(TokenBundle.is_active.is_(True))
            .count()
        )
