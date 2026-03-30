"""Shipping provider interface — plugins implement this to provide shipping methods.

Same pattern as payment plugins: core defines the interface, plugins implement.
Shipping plugins register via BasePlugin.register_shipping_providers(registry).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional


@dataclass
class ShippingRate:
    """A shipping rate option returned by a provider."""

    provider_slug: str
    name: str
    cost: Decimal
    currency: str
    estimated_days: int
    description: str = ""


@dataclass
class ShipmentResult:
    """Result of creating a shipment with a carrier."""

    success: bool
    tracking_number: str = ""
    tracking_url: str = ""
    label_url: str = ""
    error: Optional[str] = None


@dataclass
class TrackingInfo:
    """Tracking status for a shipment."""

    status: str
    location: str = ""
    estimated_delivery: str = ""
    events: List[Dict[str, Any]] = field(default_factory=list)


class IShippingProvider(ABC):
    """Interface for shipping method plugins."""

    @property
    @abstractmethod
    def slug(self) -> str:
        """Unique identifier: 'flat-rate', 'dhl-express'."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name: 'Flat Rate Shipping'."""

    @abstractmethod
    def calculate_rate(
        self, items: List[Dict[str, Any]], address: Dict[str, Any], currency: str
    ) -> List[ShippingRate]:
        """Calculate shipping rates for items to address.

        Returns list of available rate options (e.g., standard + express).
        """

    @abstractmethod
    def create_shipment(self, order: Dict[str, Any]) -> ShipmentResult:
        """Create shipment with carrier. Returns tracking info."""

    @abstractmethod
    def get_tracking(self, tracking_number: str) -> TrackingInfo:
        """Get tracking status for a shipment."""
