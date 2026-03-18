"""Repository interface (Interface Segregation Principle)."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """
    Base repository interface.

    Defines CRUD operations for data access.
    Follows Interface Segregation Principle - only essential methods.
    """

    @abstractmethod
    def find_by_id(self, id: int) -> Optional[T]:
        """
        Find entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        """
        Find all entities.

        Returns:
            List of all entities
        """
        pass

    @abstractmethod
    def save(self, entity: T, expected_version: Optional[int] = None) -> T:
        """
        Save entity (create or update).

        Args:
            entity: Entity to save
            expected_version: Expected version for optimistic locking (Sprint 1)

        Returns:
            Saved entity with updated version

        Raises:
            ConcurrentModificationError: If version mismatch (Sprint 1)
        """
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        pass
