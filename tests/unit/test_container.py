"""Tests for dependency injection container."""
import pytest
from unittest.mock import MagicMock, patch


class TestContainer:
    """Tests for DI Container configuration."""

    def test_container_provides_user_repository(self):
        """Container provides UserRepository instance."""
        from src.container import Container
        from src.repositories.user_repository import UserRepository

        container = Container()
        # Provide a mock session
        mock_session = MagicMock()
        container.db_session.override(mock_session)

        repo = container.user_repository()

        assert isinstance(repo, UserRepository)

    def test_container_provides_subscription_repository(self):
        """Container provides SubscriptionRepository instance."""
        from src.container import Container
        from src.repositories.subscription_repository import SubscriptionRepository

        container = Container()
        mock_session = MagicMock()
        container.db_session.override(mock_session)

        repo = container.subscription_repository()

        assert isinstance(repo, SubscriptionRepository)

    def test_container_provides_auth_service(self):
        """Container provides AuthService with injected dependencies."""
        from src.container import Container
        from src.services.auth_service import AuthService

        container = Container()
        mock_session = MagicMock()
        container.db_session.override(mock_session)

        service = container.auth_service()

        assert isinstance(service, AuthService)

    def test_container_provides_user_service(self):
        """Container provides UserService with injected dependencies."""
        from src.container import Container
        from src.services.user_service import UserService

        container = Container()
        mock_session = MagicMock()
        container.db_session.override(mock_session)

        service = container.user_service()

        assert isinstance(service, UserService)

    def test_container_provides_subscription_service(self):
        """Container provides SubscriptionService with injected dependencies."""
        from src.container import Container
        from src.services.subscription_service import SubscriptionService

        container = Container()
        mock_session = MagicMock()
        container.db_session.override(mock_session)

        service = container.subscription_service()

        assert isinstance(service, SubscriptionService)

    def test_container_services_use_same_session(self):
        """Services from same container use same db session."""
        from src.container import Container

        container = Container()
        mock_session = MagicMock()
        container.db_session.override(mock_session)

        auth_service = container.auth_service()
        user_service = container.user_service()

        # Both services should use repositories with the same session
        assert auth_service._user_repo._session is mock_session
        assert user_service._user_repo._session is mock_session

    def test_container_reset_singletons(self):
        """Container can reset singleton providers."""
        from src.container import Container

        container = Container()
        mock_session1 = MagicMock()
        container.db_session.override(mock_session1)

        service1 = container.auth_service()

        # Reset and use different session
        container.db_session.reset_override()
        mock_session2 = MagicMock()
        container.db_session.override(mock_session2)

        service2 = container.auth_service()

        # Should be different instances
        assert service1._user_repo._session is mock_session1
        assert service2._user_repo._session is mock_session2
