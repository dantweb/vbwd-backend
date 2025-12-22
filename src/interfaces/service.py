"""Service interface (Interface Segregation Principle)."""
from abc import ABC, abstractmethod


class IService(ABC):
    """
    Base service interface.

    Marker interface for business logic services.
    Services contain business logic and orchestrate repositories.
    """

    pass
