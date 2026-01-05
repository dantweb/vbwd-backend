"""Repository for Currency model."""
from typing import Optional, List
from sqlalchemy.orm import Session
from src.repositories.base import BaseRepository
from src.models.currency import Currency


class CurrencyRepository(BaseRepository[Currency]):
    """Repository for managing currencies."""

    def __init__(self, session: Session):
        """Initialize repository.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session, Currency)

    def find_by_code(self, code: str) -> Optional[Currency]:
        """Find currency by ISO code.

        Args:
            code: ISO 4217 currency code (e.g., EUR, USD)

        Returns:
            Currency if found, None otherwise
        """
        return self._session.query(Currency).filter_by(code=code.upper()).first()

    def find_default(self) -> Optional[Currency]:
        """Find the default (base) currency.

        Returns:
            Default currency if found, None otherwise
        """
        return self._session.query(Currency).filter_by(is_default=True).first()

    def find_active(self) -> List[Currency]:
        """Find all active currencies.

        Returns:
            List of active currencies
        """
        return self._session.query(Currency).filter_by(is_active=True).all()
