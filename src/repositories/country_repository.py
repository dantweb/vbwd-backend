"""Country repository for billing address configuration."""
from typing import List, Optional
from src.repositories.base import BaseRepository
from src.models.country import Country


class CountryRepository(BaseRepository[Country]):
    """Repository for Country entities."""

    def __init__(self, session):
        super().__init__(session=session, model=Country)

    def find_by_code(self, code: str) -> Optional[Country]:
        """Find country by ISO code."""
        return self._session.query(Country).filter(Country.code == code.upper()).first()

    def find_all_ordered(self) -> List[Country]:
        """Find all countries ordered by enabled status then position."""
        return (
            self._session.query(Country)
            .order_by(Country.is_enabled.desc(), Country.position, Country.name)
            .all()
        )

    def find_enabled(self) -> List[Country]:
        """Find all enabled countries ordered by position."""
        return (
            self._session.query(Country)
            .filter(Country.is_enabled.is_(True))
            .order_by(Country.position, Country.name)
            .all()
        )

    def find_disabled(self) -> List[Country]:
        """Find all disabled countries ordered by name."""
        return (
            self._session.query(Country)
            .filter(Country.is_enabled.is_(False))
            .order_by(Country.name)
            .all()
        )

    def get_max_enabled_position(self) -> int:
        """Get the maximum position among enabled countries."""
        result = self._session.query(
            self._session.query(Country.position)
            .filter(Country.is_enabled.is_(True))
            .subquery()
            .c.position
        ).scalar()
        if result is None:
            # Alternative query
            from sqlalchemy import func

            result = (
                self._session.query(func.max(Country.position))
                .filter(Country.is_enabled.is_(True))
                .scalar()
            )
        return result if result is not None else -1

    def update_positions(self, code_order: List[str]) -> List[Country]:
        """
        Update positions for enabled countries based on order.

        Args:
            code_order: List of country codes in desired order

        Returns:
            Updated countries
        """
        updated = []
        for position, code in enumerate(code_order):
            country = self.find_by_code(code)
            if country and country.is_enabled:
                country.position = position  # type: ignore[assignment]
                updated.append(country)

        self._session.commit()
        return updated

    def code_exists(self, code: str) -> bool:
        """Check if country code exists."""
        return (
            self._session.query(Country).filter(Country.code == code.upper()).first()
        ) is not None
