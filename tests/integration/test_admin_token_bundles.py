"""
E2E tests for admin token bundles API.

These tests require:
1. Backend services running (docker-compose up)
2. PostgreSQL with test data seeded
3. Admin user exists (admin@example.com / AdminPass123@)

Run with:
    docker-compose run --rm test pytest tests/integration/test_admin_token_bundles.py -v
"""
import pytest
import requests
import os
from uuid import uuid4


class TestAdminTokenBundles:
    """
    Integration tests for admin token bundles API.

    Tests the full CRUD operations for token bundles:
    - List token bundles
    - Create token bundle
    - Get token bundle details
    - Update token bundle
    - Activate/Deactivate token bundle
    - Delete token bundle
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
    def test_bundle_data(self) -> dict:
        """Sample token bundle data for creation."""
        return {
            "name": f"Test Bundle {uuid4().hex[:8]}",
            "description": "Test bundle for E2E testing",
            "token_amount": 1000,
            "price": "10.00",
            "is_active": True,
            "sort_order": 0
        }

    @pytest.fixture
    def created_bundle(self, admin_headers, test_bundle_data) -> dict:
        """Create a token bundle for testing and return it."""
        response = requests.post(
            f"{self.BASE_URL}/admin/token-bundles/",
            json=test_bundle_data,
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 201, f"Failed to create bundle: {response.text}"
        return response.json()["bundle"]

    # =========================================
    # Authentication Tests
    # =========================================

    def test_list_requires_auth(self):
        """
        Test: GET /api/v1/admin/token-bundles without auth
        Expected: 401 Unauthorized
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/token-bundles/",
            timeout=5
        )
        assert response.status_code == 401

    def test_list_requires_admin_role(self, user_headers):
        """
        Test: GET /api/v1/admin/token-bundles with regular user
        Expected: 403 Forbidden
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/token-bundles/",
            headers=user_headers,
            timeout=5
        )
        assert response.status_code == 403

    # =========================================
    # List Token Bundles Tests
    # =========================================

    def test_list_token_bundles_success(self, admin_headers):
        """
        Test: GET /api/v1/admin/token-bundles
        Expected: 200 with paginated list
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/token-bundles/",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "pages" in data

    def test_list_token_bundles_pagination(self, admin_headers):
        """
        Test: GET /api/v1/admin/token-bundles?page=1&per_page=5
        Expected: 200 with pagination params respected
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/token-bundles/?page=1&per_page=5",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 5
        assert len(data["items"]) <= 5

    def test_list_token_bundles_include_inactive(self, admin_headers, created_bundle):
        """
        Test: GET /api/v1/admin/token-bundles?include_inactive=true
        Expected: 200 with inactive bundles included
        """
        # First deactivate the bundle
        requests.post(
            f"{self.BASE_URL}/admin/token-bundles/{created_bundle['id']}/deactivate",
            headers=admin_headers,
            timeout=5
        )

        # List with include_inactive=true
        response = requests.get(
            f"{self.BASE_URL}/admin/token-bundles/?include_inactive=true",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        # Should include the inactive bundle
        bundle_ids = [b["id"] for b in data["items"]]
        assert created_bundle["id"] in bundle_ids

    # =========================================
    # Create Token Bundle Tests
    # =========================================

    def test_create_token_bundle_success(self, admin_headers, test_bundle_data):
        """
        Test: POST /api/v1/admin/token-bundles
        Expected: 201 with created bundle
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/token-bundles/",
            json=test_bundle_data,
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 201
        data = response.json()
        assert "bundle" in data
        assert data["bundle"]["name"] == test_bundle_data["name"]
        assert data["bundle"]["token_amount"] == test_bundle_data["token_amount"]
        assert data["bundle"]["is_active"] == True

    def test_create_token_bundle_requires_name(self, admin_headers):
        """
        Test: POST /api/v1/admin/token-bundles without name
        Expected: 400 Bad Request
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/token-bundles/",
            json={"token_amount": 100, "price": "10.00"},
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 400
        assert "name" in response.json()["error"].lower()

    def test_create_token_bundle_requires_token_amount(self, admin_headers):
        """
        Test: POST /api/v1/admin/token-bundles without token_amount
        Expected: 400 Bad Request
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/token-bundles/",
            json={"name": "Test", "price": "10.00"},
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 400
        assert "token" in response.json()["error"].lower()

    def test_create_token_bundle_requires_price(self, admin_headers):
        """
        Test: POST /api/v1/admin/token-bundles without price
        Expected: 400 Bad Request
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/token-bundles/",
            json={"name": "Test", "token_amount": 100},
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 400
        assert "price" in response.json()["error"].lower()

    def test_create_token_bundle_positive_token_amount(self, admin_headers):
        """
        Test: POST /api/v1/admin/token-bundles with zero token_amount
        Expected: 400 Bad Request
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/token-bundles/",
            json={"name": "Test", "token_amount": 0, "price": "10.00"},
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 400

    def test_create_token_bundle_non_negative_price(self, admin_headers):
        """
        Test: POST /api/v1/admin/token-bundles with negative price
        Expected: 400 Bad Request
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/token-bundles/",
            json={"name": "Test", "token_amount": 100, "price": "-10.00"},
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 400

    # =========================================
    # Get Token Bundle Tests
    # =========================================

    def test_get_token_bundle_success(self, admin_headers, created_bundle):
        """
        Test: GET /api/v1/admin/token-bundles/{id}
        Expected: 200 with bundle details
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/token-bundles/{created_bundle['id']}",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bundle"]["id"] == created_bundle["id"]
        assert data["bundle"]["name"] == created_bundle["name"]

    def test_get_token_bundle_not_found(self, admin_headers):
        """
        Test: GET /api/v1/admin/token-bundles/{non_existent_id}
        Expected: 404 Not Found
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/token-bundles/{uuid4()}",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 404

    # =========================================
    # Update Token Bundle Tests
    # =========================================

    def test_update_token_bundle_success(self, admin_headers, created_bundle):
        """
        Test: PUT /api/v1/admin/token-bundles/{id}
        Expected: 200 with updated bundle
        """
        response = requests.put(
            f"{self.BASE_URL}/admin/token-bundles/{created_bundle['id']}",
            json={"name": "Updated Bundle Name", "token_amount": 2000},
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bundle"]["name"] == "Updated Bundle Name"
        assert data["bundle"]["token_amount"] == 2000

    def test_update_token_bundle_not_found(self, admin_headers):
        """
        Test: PUT /api/v1/admin/token-bundles/{non_existent_id}
        Expected: 404 Not Found
        """
        response = requests.put(
            f"{self.BASE_URL}/admin/token-bundles/{uuid4()}",
            json={"name": "Test"},
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 404

    def test_update_token_bundle_empty_name(self, admin_headers, created_bundle):
        """
        Test: PUT /api/v1/admin/token-bundles/{id} with empty name
        Expected: 400 Bad Request
        """
        response = requests.put(
            f"{self.BASE_URL}/admin/token-bundles/{created_bundle['id']}",
            json={"name": ""},
            headers=admin_headers,
            timeout=10
        )
        assert response.status_code == 400

    # =========================================
    # Activate/Deactivate Tests
    # =========================================

    def test_deactivate_token_bundle(self, admin_headers, created_bundle):
        """
        Test: POST /api/v1/admin/token-bundles/{id}/deactivate
        Expected: 200 with is_active=false
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/token-bundles/{created_bundle['id']}/deactivate",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bundle"]["is_active"] == False

    def test_activate_token_bundle(self, admin_headers, created_bundle):
        """
        Test: POST /api/v1/admin/token-bundles/{id}/activate
        Expected: 200 with is_active=true
        """
        # First deactivate
        requests.post(
            f"{self.BASE_URL}/admin/token-bundles/{created_bundle['id']}/deactivate",
            headers=admin_headers,
            timeout=5
        )

        # Then activate
        response = requests.post(
            f"{self.BASE_URL}/admin/token-bundles/{created_bundle['id']}/activate",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200
        data = response.json()
        assert data["bundle"]["is_active"] == True

    # =========================================
    # Delete Token Bundle Tests
    # =========================================

    def test_delete_token_bundle_success(self, admin_headers, created_bundle):
        """
        Test: DELETE /api/v1/admin/token-bundles/{id}
        Expected: 200 success
        """
        response = requests.delete(
            f"{self.BASE_URL}/admin/token-bundles/{created_bundle['id']}",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 200

        # Verify deleted
        get_response = requests.get(
            f"{self.BASE_URL}/admin/token-bundles/{created_bundle['id']}",
            headers=admin_headers,
            timeout=5
        )
        assert get_response.status_code == 404

    def test_delete_token_bundle_not_found(self, admin_headers):
        """
        Test: DELETE /api/v1/admin/token-bundles/{non_existent_id}
        Expected: 404 Not Found
        """
        response = requests.delete(
            f"{self.BASE_URL}/admin/token-bundles/{uuid4()}",
            headers=admin_headers,
            timeout=5
        )
        assert response.status_code == 404
