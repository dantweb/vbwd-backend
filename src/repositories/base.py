"""Base repository implementation with optimistic locking."""
from typing import Generic, TypeVar, Optional, List, Type, Union
from uuid import UUID
from sqlalchemy.orm.exc import StaleDataError
from src.models.base import ConcurrentModificationError

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base repository with optimistic locking support.

    All save operations check version numbers.
    """

    def __init__(self, session, model: Type[T]):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session.
            model: SQLAlchemy model class.
        """
        self._session = session
        self._model = model

    def find_by_id(self, id: Union[UUID, str]) -> Optional[T]:
        """Find entity by ID."""
        return self._session.get(self._model, id)

    def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Find all entities with pagination."""
        return (
            self._session.query(self._model)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count(self) -> int:
        """Count total entities."""
        return self._session.query(self._model).count()

    def save(self, entity: T, expected_version: Optional[int] = None) -> T:
        """
        Save entity with optimistic locking.

        Args:
            entity: Entity to save
            expected_version: Expected version number (for updates)

        Returns:
            Saved entity with incremented version

        Raises:
            ConcurrentModificationError: If version mismatch detected
        """
        if entity.id and expected_version is not None:
            # Update with version check
            current = self.find_by_id(entity.id)
            if current is None:
                raise ValueError(f"Entity {entity.id} not found")

            if current.version != expected_version:
                raise ConcurrentModificationError(
                    f"Entity {entity.id} was modified by another transaction. "
                    f"Expected version {expected_version}, found {current.version}"
                )

        try:
            if not entity.id:
                self._session.add(entity)
            self._session.commit()
            self._session.refresh(entity)
            return entity
        except StaleDataError:
            self._session.rollback()
            raise ConcurrentModificationError(
                "Concurrent modification detected during save"
            )

    def delete(self, id: Union[UUID, str]) -> bool:
        """Delete entity by ID."""
        entity = self.find_by_id(id)
        if entity:
            self._session.delete(entity)
            self._session.commit()
            return True
        return False
