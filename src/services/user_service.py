"""User management service implementation."""
from typing import Optional
from uuid import UUID
from src.interfaces.auth import IUserService
from src.repositories.user_repository import UserRepository
from src.repositories.user_details_repository import UserDetailsRepository
from src.models.user import User
from src.models.user_details import UserDetails
from src.models.enums import UserStatus


class UserService(IUserService):
    """Service for user management operations."""

    def __init__(
        self,
        user_repository: UserRepository,
        user_details_repository: UserDetailsRepository
    ):
        """Initialize UserService.

        Args:
            user_repository: Repository for user data access
            user_details_repository: Repository for user details data access
        """
        self._user_repo = user_repository
        self._user_details_repo = user_details_repository

    def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User if found, None otherwise
        """
        return self._user_repo.find_by_id(user_id)

    def get_user_details(self, user_id: UUID) -> Optional[UserDetails]:
        """Get user details.

        Args:
            user_id: User UUID

        Returns:
            UserDetails if found, None otherwise
        """
        return self._user_details_repo.find_by_user_id(user_id)

    def update_user_details(self, user_id: UUID, details: dict) -> Optional[UserDetails]:
        """Update user details.

        Creates new user details record if none exists.

        Args:
            user_id: User UUID
            details: Dictionary of details to update

        Returns:
            Updated UserDetails
        """
        # Try to find existing details
        user_details = self._user_details_repo.find_by_user_id(user_id)

        if user_details:
            # Update existing details
            for key, value in details.items():
                if hasattr(user_details, key):
                    setattr(user_details, key, value)
            return self._user_details_repo.update(user_details)
        else:
            # Create new details
            user_details = UserDetails()
            user_details.user_id = user_id

            # Set provided details
            for key, value in details.items():
                if hasattr(user_details, key):
                    setattr(user_details, key, value)

            return self._user_details_repo.save(user_details)

    def update_user_status(self, user_id: UUID, status: UserStatus) -> Optional[User]:
        """Update user status.

        Args:
            user_id: User UUID
            status: New user status

        Returns:
            Updated User if found, None otherwise
        """
        user = self._user_repo.find_by_id(user_id)

        if user:
            user.status = status
            return self._user_repo.update(user)

        return None
