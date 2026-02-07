"""AddOn repository implementation."""
from typing import Optional, List, Tuple
from uuid import UUID
from src.repositories.base import BaseRepository
from src.models import AddOn


class AddOnRepository(BaseRepository[AddOn]):
    """Repository for AddOn entity operations."""

    def __init__(self, session):
        super().__init__(session=session, model=AddOn)

    def find_by_slug(self, slug: str) -> Optional[AddOn]:
        """Find add-on by slug."""
        return self._session.query(AddOn).filter(AddOn.slug == slug).first()

    def find_active(self) -> List[AddOn]:
        """Find all active add-ons ordered by sort_order."""
        return (
            self._session.query(AddOn)
            .filter(AddOn.is_active.is_(True))
            .order_by(AddOn.sort_order, AddOn.name)
            .all()
        )

    def find_all_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        include_inactive: bool = True,
    ) -> Tuple[List[AddOn], int]:
        """
        Find all add-ons with pagination.

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            include_inactive: Include inactive add-ons

        Returns:
            Tuple of (add-ons list, total count)
        """
        query = self._session.query(AddOn)

        if not include_inactive:
            query = query.filter(AddOn.is_active.is_(True))

        total = query.count()

        addons = (
            query.order_by(AddOn.sort_order, AddOn.name)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return addons, total

    def slug_exists(self, slug: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if slug exists (for validation).

        Args:
            slug: Slug to check
            exclude_id: ID to exclude from check (for updates)

        Returns:
            True if slug exists
        """
        query = self._session.query(AddOn).filter(AddOn.slug == slug)
        if exclude_id:
            query = query.filter(AddOn.id != exclude_id)
        return query.count() > 0

    def count_active(self) -> int:
        """Count active add-ons."""
        return self._session.query(AddOn).filter(AddOn.is_active.is_(True)).count()
