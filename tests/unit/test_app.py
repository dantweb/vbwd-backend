"""Tests for Flask application factory."""
import pytest


class TestAppFactory:
    """Test cases for create_app factory function."""

    def test_create_app_returns_flask_instance(self, app):
        """create_app should return a Flask application instance."""
        assert app is not None
        assert app.name == "src.app"

    def test_create_app_with_test_config(self):
        """create_app should accept test configuration."""
        from src.app import create_app
        from src.config import get_database_url

        app = create_app({
            "TESTING": True,
            "DEBUG": False,
            "SQLALCHEMY_DATABASE_URI": get_database_url(),
            "SQLALCHEMY_TRACK_MODIFICATIONS": False
        })

        assert app.config["TESTING"] is True
        assert app.config["DEBUG"] is False

    def test_health_endpoint_returns_ok(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        assert response.json["status"] == "ok"
        assert response.json["service"] == "vbwd-api"
        assert "version" in response.json

    def test_root_endpoint_returns_info(self, client):
        """Root endpoint should return API information."""
        response = client.get("/")

        assert response.status_code == 200
        assert "message" in response.json
        assert "version" in response.json
        assert response.json["health"] == "/api/v1/health"

    def test_404_error_handler(self, client):
        """404 errors should be handled properly."""
        response = client.get("/nonexistent")

        assert response.status_code == 404
        assert "error" in response.json
        assert response.json["error"] == "Not found"


class TestContainerWiring:
    """Test cases for DI container wiring."""

    def test_app_has_container(self, app):
        """Application should have container attribute."""
        assert hasattr(app, 'container')

    def test_container_has_db_session_override(self, app, client):
        """Container should have db_session properly configured."""
        from src.extensions import db

        # Make a request to trigger before_request hook
        client.get('/api/v1/health')

        # Now container should be able to provide services
        with app.app_context():
            app.container.db_session.override(db.session)
            auth_service = app.container.auth_service()
            assert auth_service is not None

    def test_container_provides_working_services(self, app, client):
        """Container services should work with db session."""
        from src.extensions import db
        from src.services.auth_service import AuthService
        from src.services.user_service import UserService
        from src.services.subscription_service import SubscriptionService

        with app.app_context():
            # Override db_session to simulate request context
            app.container.db_session.override(db.session)

            # Get services from container
            auth_service = app.container.auth_service()
            user_service = app.container.user_service()
            sub_service = app.container.subscription_service()

            assert isinstance(auth_service, AuthService)
            assert isinstance(user_service, UserService)
            assert isinstance(sub_service, SubscriptionService)


class TestConfig:
    """Test cases for configuration."""

    def test_config_loads_from_environment(self):
        """Configuration should load from environment variables."""
        import os
        from src.config import get_config

        os.environ["FLASK_ENV"] = "testing"
        config = get_config("testing")

        assert config.TESTING is True
        assert config.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"

    def test_database_url_helper(self):
        """get_database_url should return correct URL."""
        from src.config import get_database_url

        url = get_database_url()
        assert url is not None
        assert "postgresql://" in url or "sqlite://" in url

    def test_redis_url_helper(self):
        """get_redis_url should return correct URL."""
        from src.config import get_redis_url

        url = get_redis_url()
        assert url is not None
        assert "redis://" in url
