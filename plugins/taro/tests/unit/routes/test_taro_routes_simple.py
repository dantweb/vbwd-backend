"""Tests for Taro plugin routes - simplified version without complex mocking."""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4


@pytest.fixture
def app():
    """Create Flask app for testing."""
    from flask import Flask
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret"
    from plugins.taro.src.routes import taro_bp
    app.register_blueprint(taro_bp, url_prefix="/api/v1/taro")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def mock_auth_header():
    """Fixture providing valid auth header."""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_current_user():
    """Fixture providing mock current user."""
    user = Mock()
    user.id = str(uuid4())
    user.user_profile = Mock()
    user.user_profile.current_tarif_plan = Mock()
    user.user_profile.current_tarif_plan.id = "plan-star"
    user.user_profile.current_tarif_plan.daily_taro_limit = 3
    user.user_profile.current_tarif_plan.max_taro_follow_ups = 3
    return user


@pytest.fixture
def mock_dispatcher():
    """Fixture providing mock event dispatcher."""
    dispatcher = Mock()
    dispatcher.emit = Mock()
    return dispatcher


class TestTaroRoutes:
    """Test Taro routes with proper mocking."""

    def test_session_route_exists(self, client):
        """Test that session route is accessible."""
        # This tests that the route exists and is registered
        with patch("plugins.taro.src.routes.verify_jwt_in_request") as mock_verify_jwt:
            with patch("plugins.taro.src.routes.get_jwt_identity", return_value=str(uuid4())):
                with patch("plugins.taro.src.routes.get_user_tarif_plan_limits", return_value=(3, 3)):
                    with patch("plugins.taro.src.routes.check_token_balance", return_value=True):
                        # The route should exist and handle the request
                        response = client.post("/api/v1/taro/session", json={})
                        # Should not get 404 (route exists)
                        assert response.status_code != 404
