"""
Integration tests for checkout with token bundles.

TDD-First: These tests define expected API behavior.
Expected Result: ALL TESTS FAIL until checkout with token bundles is implemented.

Run with:
    docker-compose run --rm test pytest tests/integration/test_checkout_token_bundles.py -v
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
    create_test_token_bundle,
    create_inactive_token_bundle,
)


class TestCheckoutWithTokenBundles:
    """Tests for adding token bundles to checkout."""

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
    def test_token_bundle(self, admin_headers) -> Optional[Dict]:
        """Create a test token bundle."""
        bundle = create_test_token_bundle(
            admin_headers, token_amount=1000, price="10.00"
        )
        if not bundle:
            pytest.skip("Could not create test token bundle")
        return bundle

    @pytest.fixture
    def test_token_bundle_large(self, admin_headers) -> Optional[Dict]:
        """Create a large test token bundle."""
        bundle = create_test_token_bundle(
            admin_headers, token_amount=5000, price="45.00"
        )
        if not bundle:
            pytest.skip("Could not create large test token bundle")
        return bundle

    @pytest.fixture
    def inactive_bundle(self, admin_headers) -> Optional[Dict]:
        """Create an inactive token bundle."""
        bundle = create_inactive_token_bundle(admin_headers)
        if not bundle:
            pytest.skip("Could not create inactive token bundle")
        return bundle

    def test_checkout_with_single_bundle(
        self, auth_headers, test_plan, test_token_bundle
    ):
        """Can add single token bundle to checkout."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "token_bundle_ids": [test_token_bundle["id"]],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert (
            response.status_code == 201
        ), f"Got {response.status_code}: {response.text}"
        data = response.json()
        assert "token_bundles" in data
        assert len(data["token_bundles"]) == 1
        assert data["token_bundles"][0]["status"] == "pending"

    def test_checkout_with_multiple_bundles(
        self, auth_headers, test_plan, test_token_bundle, test_token_bundle_large
    ):
        """Can add multiple token bundles to checkout."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "token_bundle_ids": [
                    test_token_bundle["id"],
                    test_token_bundle_large["id"],
                ],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data["token_bundles"]) == 2

    def test_checkout_bundle_appears_in_invoice(
        self, auth_headers, test_plan, test_token_bundle
    ):
        """Token bundle appears as invoice line item."""
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
        line_items = data["invoice"]["line_items"]
        bundle_items = [i for i in line_items if i["type"] == "token_bundle"]
        assert len(bundle_items) == 1

    def test_checkout_invalid_bundle_id(self, auth_headers, test_plan):
        """Invalid bundle ID returns error."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "token_bundle_ids": [str(uuid4())],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 400

    def test_checkout_inactive_bundle(self, auth_headers, test_plan, inactive_bundle):
        """Inactive bundle returns error."""
        response = requests.post(
            f"{BASE_URL}/user/checkout",
            json={
                "plan_id": test_plan["id"],
                "token_bundle_ids": [inactive_bundle["id"]],
            },
            headers=auth_headers,
            timeout=10,
        )
        assert response.status_code == 400

    def test_checkout_bundle_not_credited_before_payment(
        self, auth_headers, test_plan, test_token_bundle
    ):
        """Tokens not credited until payment."""
        # First, get current balance
        balance_before = requests.get(
            f"{BASE_URL}/user/tokens/balance",
            headers=auth_headers,
            timeout=10,
        )

        # Create checkout with bundle
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

        # Check balance is still the same (tokens not credited yet)
        balance_after = requests.get(
            f"{BASE_URL}/user/tokens/balance",
            headers=auth_headers,
            timeout=10,
        )

        # Balance should not have increased
        if balance_before.status_code == 200 and balance_after.status_code == 200:
            assert balance_after.json()["balance"] == balance_before.json()["balance"]

    def test_checkout_bundle_has_pending_status(
        self, auth_headers, test_plan, test_token_bundle
    ):
        """Token bundle purchase has pending status until payment."""
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

        # Each bundle should have pending status
        for bundle in data["token_bundles"]:
            assert bundle["status"] == "pending"
