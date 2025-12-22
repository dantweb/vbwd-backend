"""Base interfaces for the application."""
from .repository import IRepository
from .service import IService

__all__ = ["IRepository", "IService"]
