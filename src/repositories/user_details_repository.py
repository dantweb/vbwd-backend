"""Repository for UserDetails model."""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from src.repositories.base import BaseRepository
from src.models.user_details import UserDetails


class UserDetailsRepository(BaseRepository[UserDetails]):
    """Repository for managing user details."""

    def __init__(self, session: Session):
        """Initialize repository.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session=session, model=UserDetails)

    def find_by_user_id(self, user_id: UUID) -> Optional[UserDetails]:
        """Find user details by user ID.

        Args:
            user_id: User UUID

        Returns:
            UserDetails if found, None otherwise
        """
        return self._session.query(UserDetails).filter_by(user_id=user_id).first()
