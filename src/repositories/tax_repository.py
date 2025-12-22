"""Repository for Tax model."""
from typing import Optional, List
from sqlalchemy.orm import Session
from src.repositories.base import BaseRepository
from src.models.tax import Tax


class TaxRepository(BaseRepository[Tax]):
    """Repository for managing taxes."""

    def __init__(self, session: Session):
        """Initialize repository.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(Tax, session)

    def find_by_code(self, code: str) -> Optional[Tax]:
        """Find tax by code.

        Args:
            code: Tax code (e.g., VAT_DE, SALES_TAX_CA)

        Returns:
            Tax if found, None otherwise
        """
        return self._session.query(Tax).filter_by(code=code.upper()).first()

    def find_by_country(self, country_code: str) -> List[Tax]:
        """Find all taxes for a country.

        Args:
            country_code: ISO 3166-1 alpha-2 country code

        Returns:
            List of taxes for the country
        """
        return self._session.query(Tax).filter_by(
            country_code=country_code.upper(),
            is_active=True
        ).all()

    def find_active(self) -> List[Tax]:
        """Find all active taxes.

        Returns:
            List of active taxes
        """
        return self._session.query(Tax).filter_by(is_active=True).all()
