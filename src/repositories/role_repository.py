"""Role repository for RBAC operations."""
from typing import List, Optional, Set
from uuid import UUID
from src.repositories.base import BaseRepository
from src.models.role import Role, Permission, user_roles


class RoleRepository(BaseRepository[Role]):
    """Repository for Role and Permission operations."""

    def __init__(self, session):
        """Initialize with Role model."""
        super().__init__(session, Role)

    def find_by_name(self, name: str) -> Optional[Role]:
        """Find role by name."""
        return self._session.query(Role).filter(Role.name == name).first()

    def get_user_roles(self, user_id: UUID) -> List[Role]:
        """Get all roles for a user."""
        return (
            self._session.query(Role)
            .join(user_roles)
            .filter(user_roles.c.user_id == user_id)
            .all()
        )

    def get_user_permissions(self, user_id: UUID) -> Set[str]:
        """Get all permission names for a user."""
        roles = self.get_user_roles(user_id)
        permissions = set()
        for role in roles:
            for perm in role.permissions:
                permissions.add(perm.name)
        return permissions

    def assign_role(self, user_id: UUID, role_name: str) -> bool:
        """
        Assign a role to a user.

        Args:
            user_id: User UUID
            role_name: Name of role to assign

        Returns:
            True if assigned, False if role not found
        """
        role = self.find_by_name(role_name)
        if not role:
            return False

        # Check if already assigned
        existing = (
            self._session.query(user_roles)
            .filter(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role.id
            )
            .first()
        )

        if existing:
            return True  # Already assigned

        # Insert new assignment
        self._session.execute(
            user_roles.insert().values(user_id=user_id, role_id=role.id)
        )
        self._session.commit()
        return True

    def revoke_role(self, user_id: UUID, role_name: str) -> bool:
        """
        Revoke a role from a user.

        Args:
            user_id: User UUID
            role_name: Name of role to revoke

        Returns:
            True if revoked, False if role not found
        """
        role = self.find_by_name(role_name)
        if not role:
            return False

        self._session.execute(
            user_roles.delete().where(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role.id
            )
        )
        self._session.commit()
        return True

    def user_has_role(self, user_id: UUID, role_name: str) -> bool:
        """Check if user has a specific role."""
        role = self.find_by_name(role_name)
        if not role:
            return False

        result = (
            self._session.query(user_roles)
            .filter(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role.id
            )
            .first()
        )
        return result is not None


class PermissionRepository(BaseRepository[Permission]):
    """Repository for Permission operations."""

    def __init__(self, session):
        """Initialize with Permission model."""
        super().__init__(session, Permission)

    def find_by_name(self, name: str) -> Optional[Permission]:
        """Find permission by name."""
        return self._session.query(Permission).filter(Permission.name == name).first()

    def find_by_resource(self, resource: str) -> List[Permission]:
        """Find all permissions for a resource."""
        return (
            self._session.query(Permission)
            .filter(Permission.resource == resource)
            .all()
        )
