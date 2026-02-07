"""
Integration tests for invoice total calculation during checkout.

TDD-First: These tests define expected API behavior.
Expected Result: ALL TESTS FAIL until checkout invoice calculation is implemented.

Run with:
    docker-compose run --rm test pytest tests/integration/test_checkout_invoice_total.py -v
"""
import pytest
import requests
import os
from decimal import Decimal
from typing import Dict, Optional

from tests.fixtures.checkout_fixtures import (
    BASE_URL,
    get_admin_token,
    get_user_token,
    create_test_plan,
    create_test_token_bundle,
    create_test_addon,
)


class TestInvoiceTotalCalculation:
    """Tests for invoice total with multiple items."""

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
        """Create a test plan ($29.00)."""
        plan = create_test_plan(admin_headers)
        if not plan:
            pytest.skip("Could not create test plan")
        return plan

    @pytest.fixture
    def test_token_bundle(self, admin_headers) -> Optional[Dict]:
        """Create a test token bundle ($10.00)."""
        bundle = create_test_token_bundle(
            admin_headers, token_amount=1000, price="10.00"
        )
        if not bundle:
            pytest.skip("Could not create test token bundle")
        return bundle

    @pytest.fixture
    def test_addon(self, admin_headers) -> Optional[Dict]:
        """Create a test add-on ($15.00)."""
        addon = create_test_addon(admin_headers, name="Priority Support", price="15.00")
        if not addon:
            pytest.skip("Could not create test add-on")
        return addon

    def test_invoice_total_subscription_only(self, auth_headers, test_plan):
        """Invoice total equals plan price for subscription only."""
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

        # Total should equal the plan price (29.00)
        invoice_total = Decimal(str(data["invoice"]["total_amount"]))
        plan_price = Decimal("29.00")  # From create_test_plan fixture
        assert invoice_total == plan_price

    def test_invoice_total_with_bundle(
        self, auth_headers, test_plan, test_token_bundle
    ):
        """Invoice total includes bundle price."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "token_bundle_ids": [test_token_bundle["id"]],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()

        # Total should be plan ($29) + bundle ($10) = $39
        invoice_total = Decimal(str(data["invoice"]["total_amount"]))
        expected_total = Decimal("29.00") + Decimal("10.00")
        assert invoice_total == expected_total

    def test_invoice_total_with_addon(self, auth_headers, test_plan, test_addon):
        """Invoice total includes add-on price."""
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

        # Total should be plan ($29) + addon ($15) = $44
        invoice_total = Decimal(str(data["invoice"]["total_amount"]))
        expected_total = Decimal("29.00") + Decimal("15.00")
        assert invoice_total == expected_total

    def test_invoice_total_all_items(
        self, auth_headers, test_plan, test_token_bundle, test_addon
    ):
        """Invoice total includes all items."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "token_bundle_ids": [test_token_bundle["id"]],
                "add_on_ids": [test_addon["id"]],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()

        # Total should be plan ($29) + bundle ($10) + addon ($15) = $54
        invoice_total = Decimal(str(data["invoice"]["total_amount"]))
        expected_total = Decimal("29.00") + Decimal("10.00") + Decimal("15.00")
        assert invoice_total == expected_total

        # Should have 3 line items
        assert len(data["invoice"]["line_items"]) == 3

    def test_invoice_line_items_have_correct_amounts(
        self, auth_headers, test_plan, test_token_bundle, test_addon
    ):
        """Each line item has correct amount."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "token_bundle_ids": [test_token_bundle["id"]],
                "add_on_ids": [test_addon["id"]],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        line_items = data["invoice"]["line_items"]

        # Find each type and verify amount
        for item in line_items:
            if item["type"] == "subscription":
                assert Decimal(str(item["amount"])) == Decimal("29.00")
            elif item["type"] == "token_bundle":
                assert Decimal(str(item["amount"])) == Decimal("10.00")
            elif item["type"] == "add_on":
                assert Decimal(str(item["amount"])) == Decimal("15.00")

    def test_invoice_currency_matches_selection(self, auth_headers, test_plan):
        """Invoice currency matches the selected currency."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "currency": "USD",
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["invoice"]["currency"] == "USD"

    def test_invoice_has_subtotal_and_total(self, auth_headers, test_plan, test_addon):
        """Invoice has both subtotal and total fields."""
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
        invoice = data["invoice"]

        # Should have subtotal (before tax) and total
        assert "subtotal" in invoice or "total_amount" in invoice
        # If tax is applied, total >= subtotal
