"""
Integration tests for User-Subscription-Invoice flow.

Tests validate the API against a running backend.

NOTE: TDD Discovery - The following admin endpoints are MISSING and should be added:
- POST /admin/users - Create user (admin can only list/view/modify, not create)
- POST /admin/subscriptions - Create subscription (admin can only list/view/modify, not create)

Current workaround: Use /auth/register for user creation.
Subscriptions cannot be created via API - they need a purchase/checkout flow.

Run with:
    docker-compose run --rm -e API_BASE_URL=http://api:5000/api/v1 test pytest tests/integration/test_user_subscription_flow.py -v

Methodology: TDD-First, Event-Driven, SOLID
"""
import pytest
import requests
import os
from datetime import datetime
from typing import Optional, Dict


class TestUserCreationViaAuth:
    """
    Integration tests for user creation via /auth/register.

    NOTE: Admin panel creates users through /auth/register endpoint.
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
    def admin_token(self) -> Optional[str]:
        """Get admin auth token."""
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json={
                "email": os.getenv("TEST_ADMIN_EMAIL", "admin@example.com"),
                "password": os.getenv("TEST_ADMIN_PASSWORD", "AdminPass123@"),
            },
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        return None

    @pytest.fixture
    def auth_headers(self, admin_token) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }

    def test_register_user_returns_200(self):
        """
        Test: POST /api/v1/auth/register
        Expected: 200 OK with token and user_id
        """
        timestamp = datetime.utcnow().timestamp()
        user_data = {
            "email": f"integration.test.{timestamp}@example.com",
            "password": "TestPass123@",
        }

        response = requests.post(
            f"{self.BASE_URL}/auth/register", json=user_data, timeout=10
        )

        assert (
            response.status_code == 200
        ), f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") is True
        assert data.get("token") is not None or data.get("access_token") is not None
        assert data.get("user_id") is not None

    def test_admin_can_list_users(self, auth_headers):
        """
        Test: GET /api/v1/admin/users
        Expected: 200 OK with list of users
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/users/", headers=auth_headers, timeout=10
        )

        assert (
            response.status_code == 200
        ), f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)

    def test_admin_can_get_user_by_id(self, auth_headers):
        """
        Test: GET /api/v1/admin/users/:id
        Expected: 200 OK with user data
        """
        # First get list of users
        list_response = requests.get(
            f"{self.BASE_URL}/admin/users/", headers=auth_headers, timeout=10
        )
        assert list_response.status_code == 200
        users = list_response.json().get("users", [])

        if len(users) == 0:
            pytest.skip("No users available to test")

        user_id = users[0].get("id")

        # Get user by ID
        response = requests.get(
            f"{self.BASE_URL}/admin/users/{user_id}", headers=auth_headers, timeout=10
        )

        assert (
            response.status_code == 200
        ), f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "user" in data
        assert data["user"]["id"] == user_id


class TestAdminSubscriptionManagement:
    """
    Integration tests for subscription management via admin API.

    NOTE: POST /admin/subscriptions does NOT exist.
    Subscriptions are created via checkout/purchase flow.
    """

    BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000/api/v1")

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify backend is reachable."""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Backend not healthy")
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not reachable")

    @pytest.fixture
    def admin_token(self) -> Optional[str]:
        """Get admin token."""
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json={"email": "admin@example.com", "password": "AdminPass123@"},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        return None

    @pytest.fixture
    def auth_headers(self, admin_token):
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }

    def test_admin_can_list_subscriptions(self, auth_headers):
        """
        Test: GET /api/v1/admin/subscriptions/
        Expected: 200 OK with list of subscriptions
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/subscriptions/", headers=auth_headers, timeout=10
        )

        assert (
            response.status_code == 200
        ), f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "subscriptions" in data
        assert "total" in data
        assert isinstance(data["subscriptions"], list)

    def test_admin_can_get_subscription_by_id(self, auth_headers):
        """
        Test: GET /api/v1/admin/subscriptions/:id
        Expected: 200 OK with subscription data
        """
        # First get list of subscriptions
        list_response = requests.get(
            f"{self.BASE_URL}/admin/subscriptions/", headers=auth_headers, timeout=10
        )
        subscriptions = list_response.json().get("subscriptions", [])

        if len(subscriptions) == 0:
            pytest.skip("No subscriptions available to test")

        subscription_id = subscriptions[0].get("id")

        # Get subscription by ID
        response = requests.get(
            f"{self.BASE_URL}/admin/subscriptions/{subscription_id}",
            headers=auth_headers,
            timeout=10,
        )

        assert (
            response.status_code == 200
        ), f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "subscription" in data
        assert data["subscription"]["id"] == subscription_id


class TestAdminInvoiceManagement:
    """
    Integration tests for invoice management via admin API.
    """

    BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000/api/v1")

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify backend is reachable."""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Backend not healthy")
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not reachable")

    @pytest.fixture
    def admin_token(self) -> Optional[str]:
        """Get admin token."""
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json={"email": "admin@example.com", "password": "AdminPass123@"},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        return None

    @pytest.fixture
    def auth_headers(self, admin_token):
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }

    def test_admin_can_list_invoices(self, auth_headers):
        """
        Test: GET /api/v1/admin/invoices/
        Expected: 200 OK with list of invoices
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/invoices/", headers=auth_headers, timeout=10
        )

        assert (
            response.status_code == 200
        ), f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "invoices" in data
        assert "total" in data
        assert isinstance(data["invoices"], list)

    def test_admin_can_get_invoice_by_id(self, auth_headers):
        """
        Test: GET /api/v1/admin/invoices/:id
        Expected: 200 OK with invoice data
        """
        # First get list of invoices
        list_response = requests.get(
            f"{self.BASE_URL}/admin/invoices/", headers=auth_headers, timeout=10
        )
        invoices = list_response.json().get("invoices", [])

        if len(invoices) == 0:
            pytest.skip("No invoices available to test")

        invoice_id = invoices[0].get("id")

        # Get invoice by ID
        response = requests.get(
            f"{self.BASE_URL}/admin/invoices/{invoice_id}",
            headers=auth_headers,
            timeout=10,
        )

        assert (
            response.status_code == 200
        ), f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "invoice" in data
        assert data["invoice"]["id"] == invoice_id


class TestTarifPlansEndpoint:
    """
    Integration tests for tarif plans endpoint.
    """

    BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000/api/v1")

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify backend is reachable."""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Backend not healthy")
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not reachable")

    @pytest.fixture
    def admin_token(self) -> Optional[str]:
        """Get admin token."""
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json={"email": "admin@example.com", "password": "AdminPass123@"},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        return None

    @pytest.fixture
    def auth_headers(self, admin_token):
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }

    def test_can_list_tarif_plans(self, auth_headers):
        """
        Test: GET /api/v1/tarif-plans
        Expected: 200 OK with list of plans
        """
        response = requests.get(
            f"{self.BASE_URL}/tarif-plans", headers=auth_headers, timeout=10
        )

        assert (
            response.status_code == 200
        ), f"Got {response.status_code}: {response.text}"
        data = response.json()
        # Response could be list or dict with items
        if isinstance(data, list):
            plans = data
        else:
            plans = data.get("items") or data.get("plans") or []
        assert isinstance(plans, list)


class TestAPIEndpointExistence:
    """
    Verify all required API endpoints exist.

    TDD Discovery: Tests that FAIL indicate MISSING features.
    """

    BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000/api/v1")

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify backend is reachable."""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Backend not healthy")
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not reachable")

    @pytest.fixture
    def admin_token(self) -> Optional[str]:
        """Get admin token."""
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json={"email": "admin@example.com", "password": "AdminPass123@"},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        return None

    @pytest.fixture
    def auth_headers(self, admin_token):
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }

    # === EXISTING ENDPOINTS (should pass) ===

    def test_auth_login_endpoint_exists(self):
        """Verify POST /auth/login exists."""
        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            json={"email": "test@test.com", "password": "test"},
            timeout=10,
        )
        # Should not be 404 (401 is expected for bad creds)
        assert response.status_code != 404, "POST /auth/login endpoint not found"

    def test_auth_register_endpoint_exists(self):
        """Verify POST /auth/register exists."""
        response = requests.post(
            f"{self.BASE_URL}/auth/register",
            json={"email": "test@test.com", "password": "test"},
            timeout=10,
        )
        assert response.status_code != 404, "POST /auth/register endpoint not found"

    def test_admin_users_list_endpoint_exists(self, auth_headers):
        """Verify GET /admin/users/ exists."""
        response = requests.get(
            f"{self.BASE_URL}/admin/users/", headers=auth_headers, timeout=10
        )
        assert response.status_code != 404, "GET /admin/users/ endpoint not found"

    def test_admin_subscriptions_list_endpoint_exists(self, auth_headers):
        """Verify GET /admin/subscriptions/ exists."""
        response = requests.get(
            f"{self.BASE_URL}/admin/subscriptions/", headers=auth_headers, timeout=10
        )
        assert (
            response.status_code != 404
        ), "GET /admin/subscriptions/ endpoint not found"

    def test_admin_invoices_endpoint_exists(self, auth_headers):
        """Verify GET /admin/invoices exists."""
        response = requests.get(
            f"{self.BASE_URL}/admin/invoices/", headers=auth_headers, timeout=10
        )
        assert response.status_code != 404, "GET /admin/invoices endpoint not found"

    def test_tarif_plans_endpoint_exists(self, auth_headers):
        """Verify GET /tarif-plans exists."""
        response = requests.get(
            f"{self.BASE_URL}/tarif-plans", headers=auth_headers, timeout=10
        )
        assert response.status_code != 404, "GET /tarif-plans endpoint not found"

    # === MISSING ENDPOINTS (expected to FAIL - TDD discovery) ===
    # These tests document what SHOULD exist but doesn't yet

    @pytest.mark.xfail(reason="TDD: POST /admin/users not implemented yet")
    def test_admin_create_user_endpoint_exists(self, auth_headers):
        """
        TDD Discovery: POST /admin/users should exist for admin user creation.

        Currently MISSING - admin must use /auth/register workaround.
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/users", json={}, headers=auth_headers, timeout=10
        )
        assert response.status_code != 404, "POST /admin/users endpoint not found"

    @pytest.mark.xfail(reason="TDD: POST /admin/subscriptions not implemented yet")
    def test_admin_create_subscription_endpoint_exists(self, auth_headers):
        """
        TDD Discovery: POST /admin/subscriptions should exist for admin subscription creation.

        Currently MISSING - no way to create subscriptions via admin API.
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/subscriptions",
            json={},
            headers=auth_headers,
            timeout=10,
        )
        assert (
            response.status_code != 404
        ), "POST /admin/subscriptions endpoint not found"
