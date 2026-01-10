"""
Integration tests that send real HTTP requests to the backend.

These tests require:
1. Backend services running (docker-compose up)
2. PostgreSQL with test data seeded (TEST_DATA_SEED=true)
3. Environment variables configured

Run with:
    make test-integration
    # or
    TEST_DATA_SEED=true docker-compose run --rm test pytest tests/integration/test_api_endpoints.py -v
"""
import pytest
import requests
import os
from typing import Optional


class TestAPIEndpoints:
    """
    Integration tests using real HTTP requests (curl-equivalent).

    These tests validate the full request/response cycle including:
    - Network connectivity
    - JSON serialization/deserialization
    - Authentication flow
    - Database interactions
    """

    BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000/api/v1")

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify backend is reachable before running tests."""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Backend not healthy, skipping integration tests")
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not reachable, skipping integration tests")

    @pytest.fixture
    def test_user_credentials(self) -> dict:
        """Get test user credentials from environment."""
        return {
            "email": os.getenv("TEST_USER_EMAIL", "test@example.com"),
            "password": os.getenv("TEST_USER_PASSWORD", "TestPass123@"),
        }

    @pytest.fixture
    def test_admin_credentials(self) -> dict:
        """Get test admin credentials from environment."""
        return {
            "email": os.getenv("TEST_ADMIN_EMAIL", "admin@example.com"),
            "password": os.getenv("TEST_ADMIN_PASSWORD", "AdminPass123@"),
        }

    @pytest.fixture
    def auth_token(self, test_user_credentials) -> Optional[str]:
        """Get auth token by logging in test user."""
        response = requests.post(
            f"{self.BASE_URL}/auth/login", json=test_user_credentials, timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None

    @pytest.fixture
    def admin_token(self, test_admin_credentials) -> Optional[str]:
        """Get auth token by logging in test admin."""
        response = requests.post(
            f"{self.BASE_URL}/auth/login", json=test_admin_credentials, timeout=10
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None

    # =========================================
    # Health Endpoint Tests
    # =========================================

    def test_health_endpoint_returns_ok(self):
        """
        Test: GET /api/v1/health
        Expected: 200 OK with status='ok'

        Equivalent curl:
            curl -X GET http://localhost:5000/api/v1/health
        """
        response = requests.get(f"{self.BASE_URL}/health", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "vbwd-api"

    # =========================================
    # Authentication Endpoint Tests
    # =========================================

    def test_login_with_valid_credentials(self, test_user_credentials):
        """
        Test: POST /api/v1/auth/login
        Expected: 200 OK with access_token

        Equivalent curl:
            curl -X POST http://localhost:5000/api/v1/auth/login \
                 -H "Content-Type: application/json" \
                 -d '{"email": "test@example.com", "password": "TestPass123@"}'
        """
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json=test_user_credentials,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert len(data["token"]) > 0

    def test_login_with_invalid_credentials(self):
        """
        Test: POST /api/v1/auth/login with wrong password
        Expected: 401 Unauthorized

        Equivalent curl:
            curl -X POST http://localhost:5000/api/v1/auth/login \
                 -H "Content-Type: application/json" \
                 -d '{"email": "test@example.com", "password": "wrongpass"}'
        """
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        assert response.status_code == 401

    def test_login_with_nonexistent_user(self):
        """
        Test: POST /api/v1/auth/login with unknown email
        Expected: 401 Unauthorized

        Equivalent curl:
            curl -X POST http://localhost:5000/api/v1/auth/login \
                 -H "Content-Type: application/json" \
                 -d '{"email": "nobody@example.com", "password": "anypass"}'
        """
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json={"email": "nobody@example.com", "password": "anypassword"},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        assert response.status_code == 401

    # =========================================
    # User Profile Endpoint Tests
    # =========================================

    def test_get_profile_without_auth(self):
        """
        Test: GET /api/v1/user/profile without token
        Expected: 401 Unauthorized

        Equivalent curl:
            curl -X GET http://localhost:5000/api/v1/user/profile
        """
        response = requests.get(f"{self.BASE_URL}/user/profile", timeout=10)

        assert response.status_code == 401

    def test_get_profile_with_auth(self, auth_token):
        """
        Test: GET /api/v1/user/profile with valid token
        Expected: 200 OK with user profile data

        Equivalent curl:
            curl -X GET http://localhost:5000/api/v1/user/profile \
                 -H "Authorization: Bearer <token>"
        """
        if not auth_token:
            pytest.skip("Could not obtain auth token - test user may not exist")

        response = requests.get(
            f"{self.BASE_URL}/user/profile",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert "email" in data

    # =========================================
    # Tariff Plans Endpoint Tests
    # =========================================

    def test_get_tariff_plans_public(self):
        """
        Test: GET /api/v1/tarif-plans (public endpoint)
        Expected: 200 OK with list of plans

        Equivalent curl:
            curl -X GET http://localhost:5000/api/v1/tarif-plans
        """
        response = requests.get(f"{self.BASE_URL}/tarif-plans", timeout=10)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "plans" in data
        assert isinstance(data["plans"], list)

    # =========================================
    # Subscription Endpoint Tests
    # =========================================

    def test_get_subscription_with_auth(self, auth_token):
        """
        Test: GET /api/v1/user/subscriptions with valid token
        Expected: 200 OK with subscription data (or empty list)

        Equivalent curl:
            curl -X GET http://localhost:5000/api/v1/user/subscriptions \
                 -H "Authorization: Bearer <token>"
        """
        if not auth_token:
            pytest.skip("Could not obtain auth token - test user may not exist")

        response = requests.get(
            f"{self.BASE_URL}/user/subscriptions",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10,
        )

        # 200 with list (may be empty)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    # =========================================
    # Admin Endpoint Tests
    # =========================================

    def test_admin_users_without_admin_role(self, auth_token):
        """
        Test: GET /api/v1/admin/users with regular user token
        Expected: 403 Forbidden

        Equivalent curl:
            curl -X GET http://localhost:5000/api/v1/admin/users \
                 -H "Authorization: Bearer <regular_user_token>"
        """
        if not auth_token:
            pytest.skip("Could not obtain auth token - test user may not exist")

        response = requests.get(
            f"{self.BASE_URL}/admin/users",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10,
        )

        assert response.status_code == 403

    def test_admin_users_with_admin_role(self, admin_token):
        """
        Test: GET /api/v1/admin/users with admin token
        Expected: 200 OK with list of users

        Equivalent curl:
            curl -X GET http://localhost:5000/api/v1/admin/users \
                 -H "Authorization: Bearer <admin_token>"
        """
        if not admin_token:
            pytest.skip("Could not obtain admin token - test admin may not exist")

        response = requests.get(
            f"{self.BASE_URL}/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    # =========================================
    # Invoice Endpoint Tests
    # =========================================

    def test_get_invoices_with_auth(self, auth_token):
        """
        Test: GET /api/v1/user/invoices with valid token
        Expected: 200 OK with list of invoices (may be empty)

        Equivalent curl:
            curl -X GET http://localhost:5000/api/v1/user/invoices \
                 -H "Authorization: Bearer <token>"
        """
        if not auth_token:
            pytest.skip("Could not obtain auth token - test user may not exist")

        response = requests.get(
            f"{self.BASE_URL}/user/invoices",
            headers={"Authorization": f"Bearer {auth_token}"},
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAPIErrorHandling:
    """Test API error handling with malformed requests."""

    BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000/api/v1")

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify backend is reachable."""
        try:
            requests.get(f"{self.BASE_URL}/health", timeout=5)
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not reachable")

    def test_invalid_json_returns_400(self):
        """
        Test: POST with invalid JSON
        Expected: 400 Bad Request

        Equivalent curl:
            curl -X POST http://localhost:5000/api/v1/auth/login \
                 -H "Content-Type: application/json" \
                 -d 'not valid json'
        """
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            data="not valid json",
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        # Accept 400 (bad request) or 429 (rate limited - auth endpoints have strict limits)
        assert response.status_code in [400, 429]

    def test_missing_required_fields_returns_400(self):
        """
        Test: POST with missing required fields
        Expected: 400 Bad Request with validation error

        Equivalent curl:
            curl -X POST http://localhost:5000/api/v1/auth/login \
                 -H "Content-Type: application/json" \
                 -d '{}'
        """
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json={},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        # Accept 400 (bad request) or 429 (rate limited - auth endpoints have strict limits)
        assert response.status_code in [400, 429]

    def test_nonexistent_endpoint_returns_404(self):
        """
        Test: GET nonexistent endpoint
        Expected: 404 Not Found

        Equivalent curl:
            curl -X GET http://localhost:5000/api/v1/nonexistent
        """
        response = requests.get(f"{self.BASE_URL}/nonexistent", timeout=10)

        assert response.status_code == 404
