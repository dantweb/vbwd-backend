"""RBAC service for role-based access control."""
from typing import List, Set, Optional
from uuid import UUID
from src.repositories.role_repository import RoleRepository


class RBACService:
    """
    Service for role-based access control operations.

    Handles permission checking, role assignment, and revocation.
    """

    # Admin role has all permissions
    ADMIN_ROLE = "admin"

    def __init__(self, role_repository: RoleRepository):
        """
        Initialize RBAC service.

        Args:
            role_repository: Repository for role operations
        """
        self.role_repo = role_repository

    def has_permission(self, user_id: UUID, permission_name: str) -> bool:
        """
        Check if user has a specific permission.

        Admin users have all permissions.

        Args:
            user_id: User UUID
            permission_name: Name of permission to check

        Returns:
            True if user has the permission
        """
        # Admin has all permissions
        if self.role_repo.user_has_role(user_id, self.ADMIN_ROLE):
            return True

        permissions = self.get_user_permissions(user_id)
        return permission_name in permissions

    def has_any_permission(self, user_id: UUID, permission_names: List[str]) -> bool:
        """
        Check if user has any of the specified permissions.

        Args:
            user_id: User UUID
            permission_names: List of permission names to check

        Returns:
            True if user has at least one permission
        """
        if self.role_repo.user_has_role(user_id, self.ADMIN_ROLE):
            return True

        permissions = self.get_user_permissions(user_id)
        return bool(permissions & set(permission_names))

    def has_all_permissions(self, user_id: UUID, permission_names: List[str]) -> bool:
        """
        Check if user has all specified permissions.

        Args:
            user_id: User UUID
            permission_names: List of permission names to check

        Returns:
            True if user has all permissions
        """
        if self.role_repo.user_has_role(user_id, self.ADMIN_ROLE):
            return True

        permissions = self.get_user_permissions(user_id)
        return set(permission_names).issubset(permissions)

    def get_user_permissions(self, user_id: UUID) -> Set[str]:
        """
        Get all permissions for a user.

        Args:
            user_id: User UUID

        Returns:
            Set of permission names
        """
        return self.role_repo.get_user_permissions(user_id)

    def get_user_roles(self, user_id: UUID) -> List[str]:
        """
        Get all role names for a user.

        Args:
            user_id: User UUID

        Returns:
            List of role names
        """
        roles = self.role_repo.get_user_roles(user_id)
        return [role.name for role in roles]

    def assign_role(self, user_id: UUID, role_name: str) -> bool:
        """
        Assign a role to a user.

        Args:
            user_id: User UUID
            role_name: Name of role to assign

        Returns:
            True if successful, False if role not found
        """
        return self.role_repo.assign_role(user_id, role_name)

    def revoke_role(self, user_id: UUID, role_name: str) -> bool:
        """
        Revoke a role from a user.

        Args:
            user_id: User UUID
            role_name: Name of role to revoke

        Returns:
            True if successful
        """
        return self.role_repo.revoke_role(user_id, role_name)

    def has_role(self, user_id: UUID, role_name: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            user_id: User UUID
            role_name: Name of role to check

        Returns:
            True if user has the role
        """
        return self.role_repo.user_has_role(user_id, role_name)

    def is_admin(self, user_id: UUID) -> bool:
        """
        Check if user has admin role.

        Args:
            user_id: User UUID

        Returns:
            True if user is admin
        """
        return self.role_repo.user_has_role(user_id, self.ADMIN_ROLE)
