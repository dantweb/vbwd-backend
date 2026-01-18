"""
E2E tests for admin add-ons API.

TDD RED PHASE: These tests are written BEFORE implementation.
All tests should FAIL initially until the AddOn backend is implemented.

Run with:
    docker-compose --profile test-integration run --rm test-integration \
        pytest tests/integration/test_admin_addons.py -v
"""
import pytest
import requests
import os
from uuid import uuid4


class TestAdminAddOns:
    """
    Integration tests for admin add-ons API.

    Tests the full CRUD operations for add-ons:
    - List add-ons
    - Create add-on
    - Get add-on details
    - Update add-on
    - Activate/Deactivate add-on
    - Delete add-on
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
    def admin_credentials(self) -> dict:
        """Get test admin credentials."""
        return {
            "email": os.getenv("TEST_ADMIN_EMAIL", "admin@example.com"),
            "password": os.getenv("TEST_ADMIN_PASSWORD", "AdminPass123@"),
        }

    @pytest.fixture
    def user_credentials(self) -> dict:
        """Get test user credentials (non-admin)."""
        return {
            "email": os.getenv("TEST_USER_EMAIL", "test@example.com"),
            "password": os.getenv("TEST_USER_PASSWORD", "TestPass123@"),
        }

    @pytest.fixture
    def admin_token(self, admin_credentials) -> str:
        """Get auth token for admin user."""
        response = requests.post(
            f"{self.BASE_URL}/auth/login", json=admin_credentials, timeout=10
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json().get("token")

    @pytest.fixture
    def user_token(self, user_credentials) -> str:
        """Get auth token for regular user."""
        response = requests.post(
            f"{self.BASE_URL}/auth/login", json=user_credentials, timeout=10
        )
        assert response.status_code == 200, f"User login failed: {response.text}"
        return response.json().get("token")

    @pytest.fixture
    def admin_headers(self, admin_token) -> dict:
        """Get headers with admin auth token."""
        return {"Authorization": f"Bearer {admin_token}"}

    @pytest.fixture
    def user_headers(self, user_token) -> dict:
        """Get headers with regular user auth token."""
        return {"Authorization": f"Bearer {user_token}"}

    @pytest.fixture
    def test_addon_data(self) -> dict:
        """Sample add-on data for creation."""
        unique_id = uuid4().hex[:8]
        return {
            "name": f"Test Support {unique_id}",
            "slug": f"test-support-{unique_id}",
            "description": "24/7 priority support add-on",
            "price": "15.00",
            "currency": "EUR",
            "billing_period": "monthly",
            "config": {
                "type": "support",
                "response_time_hours": 4,
                "channels": ["email", "chat", "phone"],
                "24x7": True
            },
            "is_active": True,
            "sort_order": 0
        }

    @pytest.fixture
    def created_addon(self, admin_headers, test_addon_data) -> dict:
        """Create an add-on for testing and return it."""
        response = requests.post(
            f"{self.BASE_URL}/admin/addons/",
            json=test_addon_data,
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 201, f"Failed to create addon: {response.text}"
        return response.json()["addon"]

    # =========================================
    # Authentication Tests
    # =========================================

    def test_list_requires_auth(self):
        """
        Test: GET /api/v1/admin/addons without auth
        Expected: 401 Unauthorized
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/addons/",
            timeout=5
        )
        assert response.status_code == 401

    def test_list_requires_admin_role(self, user_headers):
        """
        Test: GET /api/v1/admin/addons with regular user
        Expected: 403 Forbidden
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/addons/",
            headers=user_headers,
            timeout=5
        )
        assert response.status_code == 403

    # =========================================
    # List Add-ons Tests
    # =========================================

    def test_list_addons_success(self, admin_headers):
        """
        Test: GET /api/v1/admin/addons
        Expected: 200 with paginated list
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/addons/",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data

    def test_list_addons_pagination(self, admin_headers):
        """
        Test: GET /api/v1/admin/addons?page=1&per_page=5
        Expected: 200 with pagination params respected
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/addons/?page=1&per_page=5",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 5
        assert len(data["items"]) <= 5

    # =========================================
    # Create Add-on Tests
    # =========================================

    def test_create_addon_success(self, admin_headers, test_addon_data):
        """
        Test: POST /api/v1/admin/addons
        Expected: 201 with created add-on
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/addons/",
            json=test_addon_data,
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 201
        data = response.json()
        assert "addon" in data
        assert data["addon"]["name"] == test_addon_data["name"]
        assert data["addon"]["slug"] == test_addon_data["slug"]
        assert data["addon"]["config"]["type"] == "support"
        assert data["addon"]["is_active"] == True

    def test_create_addon_requires_name(self, admin_headers):
        """
        Test: POST /api/v1/admin/addons without name
        Expected: 400 Bad Request
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/addons/",
            json={"price": "10.00", "billing_period": "monthly"},
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 400
        assert "name" in response.json()["error"].lower()

    def test_create_addon_requires_price(self, admin_headers):
        """
        Test: POST /api/v1/admin/addons without price
        Expected: 400 Bad Request
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/addons/",
            json={"name": "Test Addon", "billing_period": "monthly"},
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 400
        assert "price" in response.json()["error"].lower()

    def test_create_addon_auto_generates_slug(self, admin_headers):
        """
        Test: POST /api/v1/admin/addons without slug
        Expected: 201 with auto-generated slug
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/addons/",
            json={
                "name": "Premium Support Feature",
                "price": "25.00",
                "billing_period": "monthly"
            },
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 201
        data = response.json()
        # Slug should be auto-generated from name
        assert data["addon"]["slug"] == "premium-support-feature"

    def test_create_addon_duplicate_slug_fails(self, admin_headers, created_addon):
        """
        Test: POST /api/v1/admin/addons with duplicate slug
        Expected: 400 Bad Request
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/addons/",
            json={
                "name": "Another Addon",
                "slug": created_addon["slug"],  # Duplicate slug
                "price": "10.00",
                "billing_period": "monthly"
            },
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 400
        assert "slug" in response.json()["error"].lower()

    def test_create_addon_with_config(self, admin_headers):
        """
        Test: POST /api/v1/admin/addons with complex config
        Expected: 201 with config preserved
        """
        config = {
            "type": "storage",
            "limits": {
                "storage_gb": 100,
                "bandwidth_gb": 500
            },
            "features": ["cdn", "backup"],
            "enabled": True
        }
        response = requests.post(
            f"{self.BASE_URL}/admin/addons/",
            json={
                "name": f"Storage Addon {uuid4().hex[:6]}",
                "price": "20.00",
                "billing_period": "monthly",
                "config": config
            },
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 201
        data = response.json()
        assert data["addon"]["config"]["limits"]["storage_gb"] == 100
        assert data["addon"]["config"]["features"] == ["cdn", "backup"]

    def test_create_addon_one_time_billing(self, admin_headers):
        """
        Test: POST /api/v1/admin/addons with one_time billing
        Expected: 201 with is_recurring=false
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/addons/",
            json={
                "name": f"Setup Fee {uuid4().hex[:6]}",
                "price": "50.00",
                "billing_period": "one_time",
                "config": {"type": "fee"}
            },
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 201
        data = response.json()
        assert data["addon"]["billing_period"] == "one_time"
        assert data["addon"]["is_recurring"] == False

    # =========================================
    # Get Add-on Tests
    # =========================================

    def test_get_addon_success(self, admin_headers, created_addon):
        """
        Test: GET /api/v1/admin/addons/{id}
        Expected: 200 with add-on details
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/addons/{created_addon['id']}",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data["addon"]["id"] == created_addon["id"]
        assert data["addon"]["name"] == created_addon["name"]

    def test_get_addon_not_found(self, admin_headers):
        """
        Test: GET /api/v1/admin/addons/{non_existent_id}
        Expected: 404 Not Found
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/addons/{uuid4()}",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 404

    def test_get_addon_by_slug(self, admin_headers, created_addon):
        """
        Test: GET /api/v1/admin/addons/slug/{slug}
        Expected: 200 with add-on details
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/addons/slug/{created_addon['slug']}",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data["addon"]["slug"] == created_addon["slug"]

    # =========================================
    # Update Add-on Tests
    # =========================================

    def test_update_addon_success(self, admin_headers, created_addon):
        """
        Test: PUT /api/v1/admin/addons/{id}
        Expected: 200 with updated add-on
        """
        response = requests.put(
            f"{self.BASE_URL}/admin/addons/{created_addon['id']}",
            json={
                "name": "Updated Addon Name",
                "price": "25.00",
                "config": {"updated": True}
            },
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert data["addon"]["name"] == "Updated Addon Name"
        assert data["addon"]["price"] == "25.00"
        assert data["addon"]["config"]["updated"] == True

    def test_update_addon_not_found(self, admin_headers):
        """
        Test: PUT /api/v1/admin/addons/{non_existent_id}
        Expected: 404 Not Found
        """
        response = requests.put(
            f"{self.BASE_URL}/admin/addons/{uuid4()}",
            json={"name": "Test"},
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 404

    def test_update_addon_duplicate_slug_fails(self, admin_headers, created_addon, test_addon_data):
        """
        Test: PUT /api/v1/admin/addons/{id} with duplicate slug
        Expected: 400 Bad Request
        """
        # Create another addon first
        test_addon_data["name"] = f"Another Addon {uuid4().hex[:6]}"
        test_addon_data["slug"] = f"another-addon-{uuid4().hex[:6]}"
        response = requests.post(
            f"{self.BASE_URL}/admin/addons/",
            json=test_addon_data,
            headers=admin_headers,
            timeout=10
        )
        another_addon = response.json()["addon"]

        # Try to update with duplicate slug
        response = requests.put(
            f"{self.BASE_URL}/admin/addons/{another_addon['id']}",
            json={"slug": created_addon["slug"]},  # Duplicate
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 400

    # =========================================
    # Activate/Deactivate Tests
    # =========================================

    def test_deactivate_addon(self, admin_headers, created_addon):
        """
        Test: POST /api/v1/admin/addons/{id}/deactivate
        Expected: 200 with is_active=false
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/addons/{created_addon['id']}/deactivate",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data["addon"]["is_active"] == False

    def test_activate_addon(self, admin_headers, created_addon):
        """
        Test: POST /api/v1/admin/addons/{id}/activate
        Expected: 200 with is_active=true
        """
        # First deactivate
        requests.post(
            f"{self.BASE_URL}/admin/addons/{created_addon['id']}/deactivate",
            headers=admin_headers,
            timeout=5
        )

        # Then activate
        response = requests.post(
            f"{self.BASE_URL}/admin/addons/{created_addon['id']}/activate",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data["addon"]["is_active"] == True

    # =========================================
    # Delete Add-on Tests
    # =========================================

    def test_delete_addon_success(self, admin_headers, created_addon):
        """
        Test: DELETE /api/v1/admin/addons/{id}
        Expected: 200 success
        """
        response = requests.delete(
            f"{self.BASE_URL}/admin/addons/{created_addon['id']}",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200

        # Verify deleted
        get_response = requests.get(
            f"{self.BASE_URL}/admin/addons/{created_addon['id']}",
            headers=admin_headers,
            timeout=5
        )
        assert get_response.status_code == 404

    def test_delete_addon_not_found(self, admin_headers):
        """
        Test: DELETE /api/v1/admin/addons/{non_existent_id}
        Expected: 404 Not Found
        """
        response = requests.delete(
            f"{self.BASE_URL}/admin/addons/{uuid4()}",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 404

    # =========================================
    # Public Add-ons Endpoint Tests (for user checkout)
    # =========================================

    def test_public_list_addons(self, created_addon):
        """
        Test: GET /api/v1/addons (public endpoint for users)
        Expected: 200 with only active add-ons
        """
        response = requests.get(
            f"{self.BASE_URL}/addons/",
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert "addons" in data
        # Should only return active addons
        for addon in data["addons"]:
            assert addon["is_active"] == True
