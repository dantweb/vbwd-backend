"""Base SDK adapter with common functionality."""
import time
from abc import ABC
from typing import Callable, Optional, TYPE_CHECKING

from src.sdk.interface import ISDKAdapter, SDKConfig, SDKResponse

if TYPE_CHECKING:
    from src.sdk.idempotency_service import IdempotencyService


class TransientError(Exception):
    """Transient error that can be retried."""

    pass


class BaseSDKAdapter(ISDKAdapter, ABC):
    """Base class for SDK adapters with retry and idempotency support.

    Provides:
    - _with_idempotency(): Idempotency key handling
    - _with_retry(): Automatic retry for transient errors

    Subclasses must implement:
    - provider_name property
    - create_payment_intent()
    - capture_payment()
    - refund_payment()
    - get_payment_status()
    """

    def __init__(
        self,
        config: SDKConfig,
        idempotency_service: Optional['IdempotencyService'] = None
    ):
        """Initialize base adapter.

        Args:
            config: SDK configuration
            idempotency_service: Optional idempotency service for caching
        """
        self._config = config
        self._idempotency = idempotency_service

    def _with_idempotency(
        self,
        idempotency_key: Optional[str],
        operation: Callable[[], SDKResponse]
    ) -> SDKResponse:
        """Execute operation with idempotency support.

        If idempotency_key is provided and response is cached, returns cached.
        Otherwise executes operation and caches successful responses.

        Args:
            idempotency_key: Optional idempotency key
            operation: Callable that returns SDKResponse

        Returns:
            SDKResponse (cached or fresh)
        """
        # Skip idempotency if no key or no service
        if not idempotency_key or not self._idempotency:
            return operation()

        # Check for cached response
        cached = self._idempotency.check(idempotency_key)
        if cached:
            return SDKResponse(
                success=cached.get('success', False),
                data=cached.get('data', {}),
                error=cached.get('error'),
                error_code=cached.get('error_code')
            )

        # Execute operation
        response = operation()

        # Cache successful responses only
        if response.success:
            self._idempotency.store(idempotency_key, response.to_dict())

        return response

    def _with_retry(
        self,
        operation: Callable[[], SDKResponse],
        max_retries: Optional[int] = None
    ) -> SDKResponse:
        """Execute operation with automatic retry for transient errors.

        Uses exponential backoff between retries.

        Args:
            operation: Callable that returns SDKResponse
            max_retries: Max retry attempts (default: config.max_retries)

        Returns:
            SDKResponse on success

        Raises:
            TransientError: After max retries exhausted
        """
        retries = max_retries if max_retries is not None else self._config.max_retries
        last_error = None

        for attempt in range(retries + 1):
            try:
                return operation()
            except TransientError as e:
                last_error = e
                if attempt < retries:
                    # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
                    time.sleep(0.1 * (2 ** attempt))

        # Re-raise the last error after all retries exhausted
        raise last_error
