"""Fixtures for checkout integration tests."""
import pytest
import requests
import os
from uuid import uuid4
from typing import Optional, Dict, Any


# Base configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000/api/v1")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "AdminPass123@")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@example.com")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "TestPass123@")


def get_admin_token() -> Optional[str]:
    """Get admin auth token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10,
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    return None


def get_user_token() -> Optional[str]:
    """Get user auth token."""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
        timeout=10,
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    return None


def create_test_plan(admin_headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Create a test tarif plan via admin API."""
    plan_data = {
        "name": f"Test Checkout Plan {uuid4().hex[:6]}",
        "slug": f"test-checkout-{uuid4().hex[:8]}",
        "description": "Test plan for checkout integration tests",
        "price": "29.00",
        "currency": "USD",
        "billing_period": "MONTHLY",
        "features": ["Feature 1", "Feature 2"],
        "is_active": True,
    }
    response = requests.post(
        f"{BASE_URL}/admin/tarif-plans/",
        json=plan_data,
        headers=admin_headers,
        timeout=10,
    )
    if response.status_code in [200, 201]:
        return response.json().get("plan") or response.json()
    return None


def create_inactive_plan(admin_headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Create an inactive test plan."""
    plan_data = {
        "name": f"Inactive Plan {uuid4().hex[:6]}",
        "slug": f"inactive-{uuid4().hex[:8]}",
        "description": "Inactive test plan",
        "price": "19.00",
        "currency": "USD",
        "billing_period": "MONTHLY",
        "is_active": False,
    }
    response = requests.post(
        f"{BASE_URL}/admin/tarif-plans/",
        json=plan_data,
        headers=admin_headers,
        timeout=10,
    )
    if response.status_code in [200, 201]:
        return response.json().get("plan") or response.json()
    return None


def create_test_token_bundle(
    admin_headers: Dict[str, str], token_amount: int = 1000, price: str = "10.00"
) -> Optional[Dict[str, Any]]:
    """Create a test token bundle via admin API."""
    bundle_data = {
        "name": f"Token Bundle {token_amount}",
        "description": f"Test bundle with {token_amount} tokens",
        "token_amount": token_amount,
        "price": price,
        "is_active": True,
    }
    response = requests.post(
        f"{BASE_URL}/admin/token-bundles/",
        json=bundle_data,
        headers=admin_headers,
        timeout=10,
    )
    if response.status_code in [200, 201]:
        return response.json().get("bundle") or response.json().get("token_bundle") or response.json()
    return None


def create_inactive_token_bundle(admin_headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Create an inactive token bundle."""
    bundle_data = {
        "name": f"Inactive Bundle {uuid4().hex[:6]}",
        "token_amount": 500,
        "price": "5.00",
        "is_active": False,
    }
    response = requests.post(
        f"{BASE_URL}/admin/token-bundles/",
        json=bundle_data,
        headers=admin_headers,
        timeout=10,
    )
    if response.status_code in [200, 201]:
        return response.json().get("bundle") or response.json().get("token_bundle") or response.json()
    return None


def create_test_addon(
    admin_headers: Dict[str, str], name: str = "Priority Support", price: str = "15.00"
) -> Optional[Dict[str, Any]]:
    """Create a test add-on via admin API."""
    addon_data = {
        "name": name,
        "slug": f"addon-{uuid4().hex[:8]}",
        "description": "Test add-on for checkout",
        "price": price,
        "currency": "USD",
        "billing_period": "monthly",
        "is_active": True,
    }
    response = requests.post(
        f"{BASE_URL}/admin/addons/",
        json=addon_data,
        headers=admin_headers,
        timeout=10,
    )
    if response.status_code in [200, 201]:
        return response.json().get("addon") or response.json()
    return None


def create_inactive_addon(admin_headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Create an inactive add-on."""
    addon_data = {
        "name": f"Inactive Addon {uuid4().hex[:6]}",
        "slug": f"inactive-addon-{uuid4().hex[:8]}",
        "price": "5.00",
        "is_active": False,
    }
    response = requests.post(
        f"{BASE_URL}/admin/addons/",
        json=addon_data,
        headers=admin_headers,
        timeout=10,
    )
    if response.status_code in [200, 201]:
        return response.json().get("addon") or response.json()
    return None
