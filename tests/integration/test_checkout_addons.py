"""
Integration tests for checkout with add-ons.

TDD-First: These tests define expected API behavior.
Expected Result: ALL TESTS FAIL until checkout with add-ons is implemented.

Run with:
    docker-compose run --rm test pytest tests/integration/test_checkout_addons.py -v
"""
import pytest
import requests
import os
from uuid import uuid4
from typing import Dict, Optional

from tests.fixtures.checkout_fixtures import (
    BASE_URL,
    get_admin_token,
    get_user_token,
    create_test_plan,
    create_test_addon,
    create_inactive_addon,
)


class TestCheckoutWithAddons:
    """Tests for adding add-ons to checkout."""

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

    @pytest.fixture
    def test_addon(self, admin_headers) -> Optional[Dict]:
        """Create a test add-on."""
        addon = create_test_addon(admin_headers, name="Priority Support", price="15.00")
        if not addon:
            pytest.skip("Could not create test add-on")
        return addon

    @pytest.fixture
    def test_addon_premium(self, admin_headers) -> Optional[Dict]:
        """Create a premium test add-on."""
        addon = create_test_addon(admin_headers, name="Premium Analytics", price="25.00")
        if not addon:
            pytest.skip("Could not create premium test add-on")
        return addon

    @pytest.fixture
    def inactive_addon(self, admin_headers) -> Optional[Dict]:
        """Create an inactive add-on."""
        addon = create_inactive_addon(admin_headers)
        if not addon:
            pytest.skip("Could not create inactive add-on")
        return addon

    def test_checkout_with_single_addon(self, auth_headers, test_plan, test_addon):
        """Can add single add-on to checkout."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "add_on_ids": [test_addon["id"]],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201, f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "add_ons" in data
        assert len(data["add_ons"]) == 1
        assert data["add_ons"][0]["status"] == "pending"

    def test_checkout_with_multiple_addons(
        self, auth_headers, test_plan, test_addon, test_addon_premium
    ):
        """Can add multiple add-ons to checkout."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "add_on_ids": [test_addon["id"], test_addon_premium["id"]],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["add_ons"]) == 2

    def test_checkout_addon_appears_in_invoice(self, auth_headers, test_plan, test_addon):
        """Add-on appears as invoice line item."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "add_on_ids": [test_addon["id"]],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        line_items = data["invoice"]["line_items"]
        addon_items = [i for i in line_items if i["type"] == "add_on"]
        assert len(addon_items) == 1

    def test_checkout_addon_linked_to_subscription(
        self, auth_headers, test_plan, test_addon
    ):
        """Add-on is linked to parent subscription."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "add_on_ids": [test_addon["id"]],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["add_ons"][0]["subscription_id"] == data["subscription"]["id"]

    def test_checkout_invalid_addon_id(self, auth_headers, test_plan):
        """Invalid add-on ID returns error."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "add_on_ids": [str(uuid4())],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 400

    def test_checkout_inactive_addon(self, auth_headers, test_plan, inactive_addon):
        """Inactive add-on returns error."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "add_on_ids": [inactive_addon["id"]],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 400

    def test_checkout_addon_has_pending_status(self, auth_headers, test_plan, test_addon):
        """Add-on has pending status until payment."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "add_on_ids": [test_addon["id"]],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()

        # Each add-on should have pending status
        for addon in data["add_ons"]:
            assert addon["status"] == "pending"

    def test_checkout_addon_not_active_before_payment(
        self, auth_headers, test_plan, test_addon
    ):
        """Add-on is not activated until payment is confirmed."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "add_on_ids": [test_addon["id"]],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()

        # Add-on should NOT be active
        assert data["add_ons"][0]["status"] != "active"
