"""
Integration tests for admin payment methods API.

TDD RED PHASE: These tests are written BEFORE implementation.
All tests should FAIL initially until the PaymentMethod backend is implemented.

Run with:
    docker-compose --profile test-integration run --rm test-integration \
        pytest tests/integration/test_admin_payment_methods.py -v
"""
import pytest
import requests
import os
from uuid import uuid4


class TestAdminPaymentMethods:
    """
    Integration tests for admin payment methods API.

    Tests the full CRUD operations for payment methods:
    - List payment methods
    - Create payment method
    - Get payment method details
    - Update payment method
    - Activate/Deactivate payment method
    - Delete payment method
    - Reorder payment methods
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
    def test_payment_method_data(self) -> dict:
        """Sample payment method data for creation."""
        unique_id = uuid4().hex[:8]
        return {
            "code": f"test-method-{unique_id}",
            "name": f"Test Method {unique_id}",
            "description": "A test payment method",
            "short_description": "Test method",
            "icon": "credit-card",
            "is_active": True,
            "is_default": False,
            "position": 10,
            "min_amount": "1.00",
            "max_amount": "10000.00",
            "currencies": ["EUR", "USD"],
            "countries": ["DE", "AT", "CH"],
            "fee_type": "percentage",
            "fee_amount": "2.5",
            "fee_charged_to": "customer",
            "instructions": "Test payment instructions",
            "config": {"test_mode": True},
        }

    @pytest.fixture
    def created_payment_method(self, admin_headers, test_payment_method_data) -> dict:
        """Create a payment method for testing and return it."""
        response = requests.post(
            f"{self.BASE_URL}/admin/payment-methods/",
            json=test_payment_method_data,
            headers=admin_headers,
            timeout=10,
        )
        assert (
            response.status_code == 201
        ), f"Failed to create payment method: {response.text}"
        return response.json()["payment_method"]

    # =========================================
    # Authentication Tests
    # =========================================

    def test_list_requires_auth(self):
        """
        Test: GET /api/v1/admin/payment-methods without auth
        Expected: 401 Unauthorized
        """
        response = requests.get(f"{self.BASE_URL}/admin/payment-methods/", timeout=5)
        assert response.status_code == 401

    def test_list_requires_admin_role(self, user_headers):
        """
        Test: GET /api/v1/admin/payment-methods with regular user
        Expected: 403 Forbidden
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/payment-methods/",
            headers=user_headers,
            timeout=5,
        )
        assert response.status_code == 403

    # =========================================
    # List Payment Methods Tests
    # =========================================

    def test_list_payment_methods_success(self, admin_headers):
        """
        Test: GET /api/v1/admin/payment-methods
        Expected: 200 with list of payment methods
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/payment-methods/",
            headers=admin_headers,
            timeout=5,
        )
        assert response.status_code == 200
        data = response.json()
        assert "payment_methods" in data
        assert isinstance(data["payment_methods"], list)

    def test_list_includes_default_invoice_method(self, admin_headers):
        """
        Test: GET /api/v1/admin/payment-methods
        Expected: Default 'invoice' method should exist
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/payment-methods/",
            headers=admin_headers,
            timeout=5,
        )
        assert response.status_code == 200
        data = response.json()

        # Find invoice method
        invoice = next(
            (m for m in data["payment_methods"] if m["code"] == "invoice"), None
        )
        assert invoice is not None, "Default invoice method should exist"
        assert invoice["name"] == "Invoice"
        assert invoice["is_active"] is True

    # =========================================
    # Create Payment Method Tests
    # =========================================

    def test_create_payment_method_success(
        self, admin_headers, test_payment_method_data
    ):
        """
        Test: POST /api/v1/admin/payment-methods
        Expected: 201 with created payment method
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/payment-methods/",
            json=test_payment_method_data,
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        assert "payment_method" in data
        assert data["payment_method"]["code"] == test_payment_method_data["code"]
        assert data["payment_method"]["name"] == test_payment_method_data["name"]
        assert data["payment_method"]["fee_type"] == "percentage"
        assert data["payment_method"]["fee_charged_to"] == "customer"

    def test_create_payment_method_requires_code(self, admin_headers):
        """
        Test: POST /api/v1/admin/payment-methods without code
        Expected: 400 Bad Request
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/payment-methods/",
            json={"name": "Test Method"},
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 400
        assert "code" in response.json()["error"].lower()

    def test_create_payment_method_requires_name(self, admin_headers):
        """
        Test: POST /api/v1/admin/payment-methods without name
        Expected: 400 Bad Request
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/payment-methods/",
            json={"code": "test-method"},
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 400
        assert "name" in response.json()["error"].lower()

    def test_create_payment_method_duplicate_code_fails(
        self, admin_headers, created_payment_method
    ):
        """
        Test: POST /api/v1/admin/payment-methods with duplicate code
        Expected: 400 Bad Request
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/payment-methods/",
            json={
                "code": created_payment_method["code"],  # Duplicate
                "name": "Another Method",
            },
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 400
        assert "code" in response.json()["error"].lower()

    def test_create_payment_method_with_fee_fixed(self, admin_headers):
        """
        Test: POST /api/v1/admin/payment-methods with fixed fee
        Expected: 201 with fee settings
        """
        unique_id = uuid4().hex[:8]
        response = requests.post(
            f"{self.BASE_URL}/admin/payment-methods/",
            json={
                "code": f"fee-test-{unique_id}",
                "name": "Fee Test",
                "fee_type": "fixed",
                "fee_amount": "1.50",
                "fee_charged_to": "merchant",
            },
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["payment_method"]["fee_type"] == "fixed"
        assert data["payment_method"]["fee_amount"] == "1.5000"
        assert data["payment_method"]["fee_charged_to"] == "merchant"

    # =========================================
    # Get Payment Method Tests
    # =========================================

    def test_get_payment_method_success(self, admin_headers, created_payment_method):
        """
        Test: GET /api/v1/admin/payment-methods/{id}
        Expected: 200 with payment method details
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/payment-methods/{created_payment_method['id']}",
            headers=admin_headers,
            timeout=5,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment_method"]["id"] == created_payment_method["id"]
        assert data["payment_method"]["code"] == created_payment_method["code"]

    def test_get_payment_method_not_found(self, admin_headers):
        """
        Test: GET /api/v1/admin/payment-methods/{non_existent_id}
        Expected: 404 Not Found
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/payment-methods/{uuid4()}",
            headers=admin_headers,
            timeout=5,
        )
        assert response.status_code == 404

    def test_get_payment_method_by_code(self, admin_headers, created_payment_method):
        """
        Test: GET /api/v1/admin/payment-methods/code/{code}
        Expected: 200 with payment method details
        """
        response = requests.get(
            f"{self.BASE_URL}/admin/payment-methods/code/{created_payment_method['code']}",
            headers=admin_headers,
            timeout=5,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment_method"]["code"] == created_payment_method["code"]

    # =========================================
    # Update Payment Method Tests
    # =========================================

    def test_update_payment_method_success(self, admin_headers, created_payment_method):
        """
        Test: PUT /api/v1/admin/payment-methods/{id}
        Expected: 200 with updated payment method
        """
        response = requests.put(
            f"{self.BASE_URL}/admin/payment-methods/{created_payment_method['id']}",
            json={
                "name": "Updated Name",
                "description": "Updated description",
                "fee_type": "fixed",
                "fee_amount": "2.00",
            },
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment_method"]["name"] == "Updated Name"
        assert data["payment_method"]["description"] == "Updated description"
        assert data["payment_method"]["fee_type"] == "fixed"

    def test_update_payment_method_code_immutable(
        self, admin_headers, created_payment_method
    ):
        """
        Test: PUT /api/v1/admin/payment-methods/{id} trying to change code
        Expected: 400 Bad Request (code is immutable)
        """
        response = requests.put(
            f"{self.BASE_URL}/admin/payment-methods/{created_payment_method['id']}",
            json={"code": "new-code"},  # Should not be allowed
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 400
        assert "immutable" in response.json()["error"].lower()

    def test_update_payment_method_not_found(self, admin_headers):
        """
        Test: PUT /api/v1/admin/payment-methods/{non_existent_id}
        Expected: 404 Not Found
        """
        response = requests.put(
            f"{self.BASE_URL}/admin/payment-methods/{uuid4()}",
            json={"name": "Test"},
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 404

    # =========================================
    # Activate/Deactivate Tests
    # =========================================

    def test_deactivate_payment_method(self, admin_headers, created_payment_method):
        """
        Test: POST /api/v1/admin/payment-methods/{id}/deactivate
        Expected: 200 with is_active=false
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/payment-methods/{created_payment_method['id']}/deactivate",
            headers=admin_headers,
            timeout=5,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment_method"]["is_active"] is False

    def test_activate_payment_method(self, admin_headers, created_payment_method):
        """
        Test: POST /api/v1/admin/payment-methods/{id}/activate
        Expected: 200 with is_active=true
        """
        # First deactivate
        requests.post(
            f"{self.BASE_URL}/admin/payment-methods/{created_payment_method['id']}/deactivate",
            headers=admin_headers,
            timeout=5,
        )

        # Then activate
        response = requests.post(
            f"{self.BASE_URL}/admin/payment-methods/{created_payment_method['id']}/activate",
            headers=admin_headers,
            timeout=5,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment_method"]["is_active"] is True

    def test_cannot_deactivate_default_method(self, admin_headers):
        """
        Test: POST /api/v1/admin/payment-methods/{invoice_id}/deactivate
        Expected: 400 Bad Request (cannot deactivate default)
        """
        # First get the invoice method
        list_response = requests.get(
            f"{self.BASE_URL}/admin/payment-methods/",
            headers=admin_headers,
            timeout=5,
        )
        invoice = next(
            (
                m
                for m in list_response.json()["payment_methods"]
                if m["code"] == "invoice"
            ),
            None,
        )

        if invoice and invoice.get("is_default"):
            response = requests.post(
                f"{self.BASE_URL}/admin/payment-methods/{invoice['id']}/deactivate",
                headers=admin_headers,
                timeout=5,
            )
            assert response.status_code == 400
            assert "default" in response.json()["error"].lower()

    # =========================================
    # Delete Payment Method Tests
    # =========================================

    def test_delete_payment_method_success(self, admin_headers, created_payment_method):
        """
        Test: DELETE /api/v1/admin/payment-methods/{id}
        Expected: 200 success
        """
        response = requests.delete(
            f"{self.BASE_URL}/admin/payment-methods/{created_payment_method['id']}",
            headers=admin_headers,
            timeout=5,
        )
        assert response.status_code == 200

        # Verify deleted
        get_response = requests.get(
            f"{self.BASE_URL}/admin/payment-methods/{created_payment_method['id']}",
            headers=admin_headers,
            timeout=5,
        )
        assert get_response.status_code == 404

    def test_delete_payment_method_not_found(self, admin_headers):
        """
        Test: DELETE /api/v1/admin/payment-methods/{non_existent_id}
        Expected: 404 Not Found
        """
        response = requests.delete(
            f"{self.BASE_URL}/admin/payment-methods/{uuid4()}",
            headers=admin_headers,
            timeout=5,
        )
        assert response.status_code == 404

    def test_cannot_delete_default_method(self, admin_headers):
        """
        Test: DELETE /api/v1/admin/payment-methods/{invoice_id}
        Expected: 400 Bad Request (cannot delete default)
        """
        # First get the invoice method
        list_response = requests.get(
            f"{self.BASE_URL}/admin/payment-methods/",
            headers=admin_headers,
            timeout=5,
        )
        invoice = next(
            (
                m
                for m in list_response.json()["payment_methods"]
                if m["code"] == "invoice"
            ),
            None,
        )

        if invoice and invoice.get("is_default"):
            response = requests.delete(
                f"{self.BASE_URL}/admin/payment-methods/{invoice['id']}",
                headers=admin_headers,
                timeout=5,
            )
            assert response.status_code == 400
            assert "default" in response.json()["error"].lower()

    # =========================================
    # Reorder Tests
    # =========================================

    def test_reorder_payment_methods(self, admin_headers):
        """
        Test: PUT /api/v1/admin/payment-methods/reorder
        Expected: 200 with updated positions
        """
        # Get current methods
        list_response = requests.get(
            f"{self.BASE_URL}/admin/payment-methods/",
            headers=admin_headers,
            timeout=5,
        )
        methods = list_response.json()["payment_methods"]

        if len(methods) >= 2:
            # Reorder
            new_order = [{"id": m["id"], "position": i} for i, m in enumerate(methods)]
            response = requests.put(
                f"{self.BASE_URL}/admin/payment-methods/reorder",
                json={"order": new_order},
                headers=admin_headers,
                timeout=10,
            )
            assert response.status_code == 200

    # =========================================
    # Set Default Tests
    # =========================================

    def test_set_default_payment_method(self, admin_headers, created_payment_method):
        """
        Test: POST /api/v1/admin/payment-methods/{id}/set-default
        Expected: 200, method becomes default, others are not default
        """
        response = requests.post(
            f"{self.BASE_URL}/admin/payment-methods/{created_payment_method['id']}/set-default",
            headers=admin_headers,
            timeout=5,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["payment_method"]["is_default"] is True

        # Verify only one default
        list_response = requests.get(
            f"{self.BASE_URL}/admin/payment-methods/",
            headers=admin_headers,
            timeout=5,
        )
        defaults = [
            m for m in list_response.json()["payment_methods"] if m["is_default"]
        ]
        assert len(defaults) == 1

    # =========================================
    # Public Endpoint Tests
    # =========================================

    def test_public_list_payment_methods(self, created_payment_method):
        """
        Test: GET /api/v1/settings/payment-methods (public endpoint)
        Expected: 200 with only active methods
        """
        response = requests.get(f"{self.BASE_URL}/settings/payment-methods", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "methods" in data
        # All returned methods should be active
        for method in data["methods"]:
            assert method["is_active"] is True
            # Should not contain sensitive config
            assert "config" not in method or method.get("config") is None

    def test_public_list_excludes_inactive(self, admin_headers, created_payment_method):
        """
        Test: Deactivated methods should not appear in public list
        """
        # Deactivate the method
        requests.post(
            f"{self.BASE_URL}/admin/payment-methods/{created_payment_method['id']}/deactivate",
            headers=admin_headers,
            timeout=5,
        )

        # Check public list
        response = requests.get(f"{self.BASE_URL}/settings/payment-methods", timeout=5)
        data = response.json()

        # Should not contain the deactivated method
        codes = [m["code"] for m in data["methods"]]
        assert created_payment_method["code"] not in codes


class TestPaymentMethodTranslations:
    """Integration tests for payment method translations."""

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
    def admin_headers(self) -> dict:
        """Get headers with admin auth token."""
        credentials = {
            "email": os.getenv("TEST_ADMIN_EMAIL", "admin@example.com"),
            "password": os.getenv("TEST_ADMIN_PASSWORD", "AdminPass123@"),
        }
        response = requests.post(
            f"{self.BASE_URL}/auth/login", json=credentials, timeout=10
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}

    def test_add_translation(self, admin_headers):
        """
        Test: POST /api/v1/admin/payment-methods/{id}/translations
        Expected: 201 with translation added
        """
        # Get invoice method
        list_response = requests.get(
            f"{self.BASE_URL}/admin/payment-methods/",
            headers=admin_headers,
            timeout=5,
        )
        invoice = next(
            (
                m
                for m in list_response.json()["payment_methods"]
                if m["code"] == "invoice"
            ),
            None,
        )

        if invoice:
            response = requests.post(
                f"{self.BASE_URL}/admin/payment-methods/{invoice['id']}/translations",
                json={
                    "locale": "de",
                    "name": "Rechnung",
                    "description": "Zahlung per Rechnung",
                },
                headers=admin_headers,
                timeout=10,
            )
            assert response.status_code in [200, 201]

    def test_get_translated_method(self):
        """
        Test: GET /api/v1/settings/payment-methods?locale=de
        Expected: 200 with translated names
        """
        response = requests.get(
            f"{self.BASE_URL}/settings/payment-methods?locale=de", timeout=5
        )
        assert response.status_code == 200
        # Translation should be applied if exists
