"""SDK adapter registry for managing payment providers."""
from typing import Dict, List

from src.sdk.interface import ISDKAdapter


class SDKAdapterRegistry:
    """Registry for SDK adapters.

    Manages registration and lookup of payment provider adapters.
    Follows Single Responsibility: only handles adapter registration.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._adapters: Dict[str, ISDKAdapter] = {}

    def register(self, provider_name: str, adapter: ISDKAdapter) -> None:
        """Register adapter for provider.

        Args:
            provider_name: Unique provider identifier (e.g., 'stripe')
            adapter: ISDKAdapter implementation
        """
        self._adapters[provider_name] = adapter

    def get(self, provider_name: str) -> ISDKAdapter:
        """Get adapter by provider name.

        Args:
            provider_name: Provider identifier

        Returns:
            Registered adapter

        Raises:
            ValueError: If provider not registered
        """
        if provider_name not in self._adapters:
            raise ValueError(f"Unknown provider: {provider_name}")
        return self._adapters[provider_name]

    def has(self, provider_name: str) -> bool:
        """Check if provider is registered.

        Args:
            provider_name: Provider identifier

        Returns:
            True if provider is registered
        """
        return provider_name in self._adapters

    def list_providers(self) -> List[str]:
        """List all registered provider names.

        Returns:
            List of provider names
        """
        return list(self._adapters.keys())

    def unregister(self, provider_name: str) -> None:
        """Remove provider from registry.

        Args:
            provider_name: Provider to remove
        """
        if provider_name in self._adapters:
            del self._adapters[provider_name]
