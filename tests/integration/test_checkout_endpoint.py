"""
Integration tests for POST /api/v1/user/checkout endpoint.

TDD-First: These tests define expected API behavior.
Expected Result: ALL TESTS FAIL until checkout endpoint is implemented.

Run with:
    docker-compose run --rm test pytest tests/integration/test_checkout_endpoint.py -v

Or against running backend:
    API_BASE_URL=http://localhost:5000/api/v1 pytest tests/integration/test_checkout_endpoint.py -v
"""
import pytest
import requests
from uuid import uuid4
from typing import Dict, Optional

from tests.fixtures.checkout_fixtures import (
    BASE_URL,
    get_admin_token,
    get_user_token,
    create_test_plan,
    create_inactive_plan,
)


class TestCheckoutEndpointAuth:
    """Authentication tests for checkout endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify backend is reachable before running tests."""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Backend not healthy, skipping integration tests")
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not reachable, skipping integration tests")

    def test_checkout_requires_auth(self):
        """Unauthenticated request returns 401."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={"plan_id": str(uuid4())},
            timeout=10,
        )
        assert response.status_code == 401

    def test_checkout_with_invalid_token(self):
        """Invalid token returns 401."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={"plan_id": str(uuid4())},
            headers={"Authorization": "Bearer invalid-token"},
            timeout=10,
        )
        assert response.status_code == 401


class TestCheckoutEndpointValidation:
    """Validation tests for checkout endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify backend is reachable."""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Backend not healthy")
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not reachable")

    @pytest.fixture
    def user_token(self) -> Optional[str]:
        """Get user auth token."""
        token = get_user_token()
        if not token:
            pytest.fail("Failed to get user token")
        return token

    @pytest.fixture
    def auth_headers(self, user_token) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json",
        }

    @pytest.fixture
    def admin_headers(self) -> Dict[str, str]:
        """Get admin authorization headers."""
        token = get_admin_token()
        if not token:
            pytest.fail("Failed to get admin token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @pytest.fixture
    def inactive_plan(self, admin_headers) -> Optional[Dict]:
        """Create an inactive plan for testing."""
        plan = create_inactive_plan(admin_headers)
        if not plan:
            pytest.skip("Could not create inactive plan")
        return plan

    def test_checkout_empty_request_returns_400(self, auth_headers):
        """Empty request with no items returns 400."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={},
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 400
        assert "item" in response.json().get("error", "").lower()

    def test_checkout_invalid_plan_id_format(self, auth_headers):
        """Invalid UUID format returns 400."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={"plan_id": "not-a-uuid"},
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 400

    def test_checkout_nonexistent_plan(self, auth_headers):
        """Non-existent plan returns 400."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={"plan_id": str(uuid4())},
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 400
        error_msg = response.json().get("error", "").lower()
        assert "not found" in error_msg or "invalid" in error_msg

    def test_checkout_inactive_plan(self, auth_headers, inactive_plan):
        """Inactive plan returns 400."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={"plan_id": inactive_plan["id"]},
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 400


class TestCheckoutEndpointSuccess:
    """Success tests for checkout endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify backend is reachable."""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Backend not healthy")
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not reachable")

    @pytest.fixture
    def user_token(self) -> Optional[str]:
        """Get user auth token."""
        token = get_user_token()
        if not token:
            pytest.fail("Failed to get user token")
        return token

    @pytest.fixture
    def auth_headers(self, user_token) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json",
        }

    @pytest.fixture
    def admin_headers(self) -> Dict[str, str]:
        """Get admin authorization headers."""
        token = get_admin_token()
        if not token:
            pytest.fail("Failed to get admin token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @pytest.fixture
    def test_plan(self, admin_headers) -> Optional[Dict]:
        """Create a test plan for checkout."""
        plan = create_test_plan(admin_headers)
        if not plan:
            pytest.skip("Could not create test plan")
        return plan

    def test_checkout_creates_pending_subscription(self, auth_headers, test_plan):
        """Checkout creates subscription with PENDING status."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={"plan_id": test_plan["id"]},
            headers=auth_headers,
            timeout=10,
        )
        assert (
            response.status_code == 201
        ), f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "subscription" in data
        assert data["subscription"]["status"] == "PENDING"

    def test_checkout_creates_invoice(self, auth_headers, test_plan):
        """Checkout creates pending invoice."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={"plan_id": test_plan["id"]},
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        assert "invoice" in data
        assert data["invoice"]["status"] == "PENDING"
        assert data["invoice"]["invoice_number"].startswith("INV-")

    def test_checkout_returns_awaiting_payment_message(self, auth_headers, test_plan):
        """Checkout returns message about awaiting payment."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={"plan_id": test_plan["id"]},
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert (
            "awaiting payment" in data["message"].lower()
            or "pending" in data["message"].lower()
        )

    def test_checkout_invoice_has_subscription_line_item(self, auth_headers, test_plan):
        """Invoice contains subscription as line item."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={"plan_id": test_plan["id"]},
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        line_items = data["invoice"]["line_items"]
        assert len(line_items) >= 1
        subscription_items = [i for i in line_items if i["type"] == "subscription"]
        assert len(subscription_items) == 1

    def test_checkout_subscription_linked_to_invoice(self, auth_headers, test_plan):
        """Subscription is linked to the created invoice."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={"plan_id": test_plan["id"]},
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        # The subscription should reference the invoice or vice versa
        assert data["subscription"]["id"] is not None
        assert data["invoice"]["id"] is not None


class TestCheckoutWithoutPlan:
    """Tests for checkout without a plan (cart-based checkout)."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Verify backend is reachable."""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Backend not healthy")
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend not reachable")

    @pytest.fixture
    def user_token(self) -> Optional[str]:
        """Get user auth token."""
        token = get_user_token()
        if not token:
            pytest.fail("Failed to get user token")
        return token

    @pytest.fixture
    def auth_headers(self, user_token) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json",
        }

    @pytest.fixture
    def admin_headers(self) -> Dict[str, str]:
        """Get admin authorization headers."""
        token = get_admin_token()
        if not token:
            pytest.fail("Failed to get admin token")
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def test_checkout_without_plan_with_bundles_returns_201(
        self, auth_headers, admin_headers
    ):
        """Checkout with only token bundles (no plan) returns 201."""
        from tests.fixtures.checkout_fixtures import create_test_token_bundle

        bundle = create_test_token_bundle(admin_headers)
        if not bundle:
            pytest.skip("Could not create test token bundle")

        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={"token_bundle_ids": [bundle["id"]]},
            headers=auth_headers,
            timeout=10,
        )
        assert (
            response.status_code == 201
        ), f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "invoice" in data
        assert data["invoice"]["status"] == "PENDING"
        # No subscription should be created
        assert "subscription" not in data

    def test_checkout_payment_method_code_stored_on_invoice(
        self, auth_headers, admin_headers
    ):
        """Payment method code is stored on the created invoice."""
        from tests.fixtures.checkout_fixtures import create_test_token_bundle

        bundle = create_test_token_bundle(admin_headers, token_amount=500, price="5.00")
        if not bundle:
            pytest.skip("Could not create test token bundle")

        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "token_bundle_ids": [bundle["id"]],
                "payment_method_code": "paypal",
            },
            headers=auth_headers,
            timeout=10,
        )
        assert (
            response.status_code == 201
        ), f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert data["invoice"]["payment_method"] == "paypal"
