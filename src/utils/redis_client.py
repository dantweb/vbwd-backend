"""Redis client utilities for distributed locking and caching."""
import redis  # type: ignore[import-untyped]
from contextlib import contextmanager
from typing import Optional, Generator
from src.config import get_redis_url
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper with distributed lock support."""

    def __init__(self, url: Optional[str] = None):
        """Initialize Redis client."""
        self._url = url or get_redis_url()
        self._client = redis.from_url(
            self._url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )

    @property
    def client(self) -> redis.Redis:
        """Get raw Redis client."""
        return self._client

    @contextmanager
    def lock(
        self,
        key: str,
        timeout: int = 10,
        blocking_timeout: int = 5,
    ) -> Generator[bool, None, None]:
        """
        Acquire distributed lock.

        Args:
            key: Lock key name (e.g., "generate_invoice:user_123")
            timeout: Lock expiration time in seconds
            blocking_timeout: Max time to wait for lock

        Usage:
            with redis_client.lock("generate_invoice:123"):
                # Critical section - only one process can execute
                generate_invoice(123)

        Yields:
            True if lock acquired, False otherwise
        """
        lock = self._client.lock(
            f"lock:{key}",
            timeout=timeout,
            blocking_timeout=blocking_timeout,
        )

        acquired = False
        try:
            acquired = lock.acquire(blocking=True)
            if acquired:
                logger.debug(f"Lock acquired: {key}")
                yield True
            else:
                logger.warning(f"Failed to acquire lock: {key}")
                yield False
        finally:
            if acquired:
                try:
                    lock.release()
                    logger.debug(f"Lock released: {key}")
                except redis.exceptions.LockNotOwnedError:
                    logger.warning(f"Lock expired before release: {key}")

    def set_idempotency_key(
        self,
        key: str,
        value: str,
        ttl: int = 86400,
    ) -> bool:
        """
        Set idempotency key (24-hour default TTL).

        Args:
            key: Idempotency key from request header
            value: Response data to cache
            ttl: Time to live in seconds

        Returns:
            True if key was set, False if already exists
        """
        result = self._client.set(
            f"idempotency:{key}",
            value,
            ex=ttl,
            nx=True,  # Only set if not exists
        )
        return result or False

    def get_idempotency_key(self, key: str) -> Optional[str]:
        """Get cached response for idempotency key."""
        return self._client.get(f"idempotency:{key}")

    def ping(self) -> bool:
        """Test Redis connection."""
        try:
            return self._client.ping()
        except redis.ConnectionError:
            return False


# Global Redis client instance
redis_client = RedisClient()
