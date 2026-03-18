"""Event context for request-scoped data caching."""
from typing import Dict, Any, Optional, Callable, TypeVar

T = TypeVar("T")


class EventContext:
    """
    Request-scoped cache for event processing.

    Provides a way to share data between event handlers
    during a single request/operation without passing
    data through event payloads.
    """

    def __init__(self):
        """Initialize empty context."""
        self._cache: Dict[str, Any] = {}

    def get(self, key: str, default: Optional[T] = None) -> Optional[T]:
        """
        Get value from context.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        return self._cache.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set value in context.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = value

    def has(self, key: str) -> bool:
        """
        Check if key exists in context.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        return key in self._cache

    def delete(self, key: str) -> None:
        """
        Delete key from context.

        Args:
            key: Cache key to delete
        """
        if key in self._cache:
            del self._cache[key]

    def get_or_compute(self, key: str, factory: Callable[[], T]) -> T:
        """
        Get value or compute and cache it.

        If key exists, returns cached value.
        Otherwise, calls factory(), caches result, and returns it.

        Args:
            key: Cache key
            factory: Callable that produces the value

        Returns:
            Cached or computed value
        """
        if key not in self._cache:
            self._cache[key] = factory()
        return self._cache[key]

    def clear(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
