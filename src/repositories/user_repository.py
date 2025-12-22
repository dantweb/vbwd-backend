"""User repository implementation."""
from typing import Optional, List
from src.repositories.base import BaseRepository
from src.models import User


class UserRepository(BaseRepository[User]):
    """Repository for User entity operations."""

    def __init__(self, session):
        super().__init__(session=session, model=User)

    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        return (
            self._session.query(User)
            .filter(User.email == email)
            .first()
        )

    def find_by_status(self, status: str) -> List[User]:
        """Find users by status."""
        return (
            self._session.query(User)
            .filter(User.status == status)
            .all()
        )

    def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        return (
            self._session.query(User)
            .filter(User.email == email)
            .count() > 0
        )
