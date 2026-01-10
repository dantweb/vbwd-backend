"""Idempotency service for SDK requests."""
import hashlib
import json
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from redis import Redis


class IdempotencyService:
    """
    Manages idempotency keys for SDK requests.

    Uses Redis to cache responses and prevent duplicate API calls
    to payment providers.
    """

    DEFAULT_TTL = 86400  # 24 hours

    def __init__(self, redis_client: "Redis"):
        """
        Initialize idempotency service.

        Args:
            redis_client: Redis client for caching
        """
        self._redis = redis_client

    def generate_key(self, provider: str, operation: str, *args) -> str:
        """
        Generate deterministic idempotency key.

        Creates a SHA256 hash from provider, operation, and arguments
        to ensure same inputs always produce same key.

        Args:
            provider: Provider name (e.g., 'stripe', 'paypal')
            operation: Operation name (e.g., 'create_payment')
            *args: Additional arguments to include in key

        Returns:
            32-character hex string
        """
        data = f"{provider}:{operation}:{':'.join(str(a) for a in args)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def check(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Check if response exists for key.

        Args:
            key: Idempotency key to check

        Returns:
            Cached response dict or None if not found
        """
        cached = self._redis.get(f"idempotency:{key}")
        if cached:
            return json.loads(cached)
        return None

    def store(
        self, key: str, response: Dict[str, Any], ttl: Optional[int] = None
    ) -> None:
        """
        Store response with TTL.

        Args:
            key: Idempotency key
            response: Response data to cache
            ttl: Time-to-live in seconds (default: 24 hours)
        """
        self._redis.setex(
            f"idempotency:{key}", ttl or self.DEFAULT_TTL, json.dumps(response)
        )

    def delete(self, key: str) -> None:
        """
        Delete key from cache.

        Args:
            key: Idempotency key to delete
        """
        self._redis.delete(f"idempotency:{key}")
