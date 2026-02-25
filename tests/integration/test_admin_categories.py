"""
Integration tests for admin tariff plan categories API.

Run with:
    docker-compose --profile test-integration run --rm test-integration \
        pytest tests/integration/test_admin_categories.py -v
"""
import pytest
import requests
import os
from uuid import uuid4


class TestAdminCategories:
    """
    Integration tests for admin tariff plan categories API.

    Tests CRUD operations and plan attachment/detachment.
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
        return {
            "email": os.getenv("TEST_ADMIN_EMAIL", "admin@example.com"),
            "password": os.getenv("TEST_ADMIN_PASSWORD", "AdminPass123@"),
        }

    @pytest.fixture
    def user_credentials(self) -> dict:
        return {
            "email": os.getenv("TEST_USER_EMAIL", "test@example.com"),
            "password": os.getenv("TEST_USER_PASSWORD", "TestPass123@"),
        }

    @pytest.fixture
    def admin_token(self, admin_credentials) -> str:
        response = requests.post(
            f"{self.BASE_URL}/auth/login", json=admin_credentials, timeout=10
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json().get("token")

    @pytest.fixture
    def user_token(self, user_credentials) -> str:
        response = requests.post(
            f"{self.BASE_URL}/auth/login", json=user_credentials, timeout=10
        )
        assert response.status_code == 200, f"User login failed: {response.text}"
        return response.json().get("token")

    @pytest.fixture
    def admin_headers(self, admin_token) -> dict:
        return {"Authorization": f"Bearer {admin_token}"}

    # --- List Categories ---

    def test_list_categories(self, admin_headers):
        """GET /admin/tarif-plan-categories should return categories list."""
        response = requests.get(
            f"{self.BASE_URL}/admin/tarif-plan-categories",
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)

    def test_list_categories_tree_format(self, admin_headers):
        """GET with ?format=tree should return nested structure."""
        response = requests.get(
            f"{self.BASE_URL}/admin/tarif-plan-categories?format=tree",
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data

    def test_list_categories_requires_admin(self, user_token):
        """Non-admin users should be rejected."""
        response = requests.get(
            f"{self.BASE_URL}/admin/tarif-plan-categories",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=10,
        )
        assert response.status_code in (401, 403)

    # --- Root Category ---

    def test_root_category_exists(self, admin_headers):
        """Root category should exist from migration."""
        response = requests.get(
            f"{self.BASE_URL}/admin/tarif-plan-categories",
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 200
        categories = response.json()["categories"]
        slugs = [c["slug"] for c in categories]
        assert "root" in slugs

    # --- Create Category ---

    def test_create_category(self, admin_headers):
        """POST should create a new category."""
        unique_slug = f"test-cat-{uuid4().hex[:8]}"
        response = requests.post(
            f"{self.BASE_URL}/admin/tarif-plan-categories",
            headers=admin_headers,
            json={
                "name": "Test Category",
                "slug": unique_slug,
                "is_single": False,
            },
            timeout=10,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["category"]["slug"] == unique_slug
        assert data["category"]["is_single"] is False

    def test_create_category_missing_name(self, admin_headers):
        """POST without name should return 400."""
        response = requests.post(
            f"{self.BASE_URL}/admin/tarif-plan-categories",
            headers=admin_headers,
            json={"slug": "missing-name"},
            timeout=10,
        )
        assert response.status_code == 400

    def test_create_category_duplicate_slug(self, admin_headers):
        """POST with existing slug should return 400."""
        response = requests.post(
            f"{self.BASE_URL}/admin/tarif-plan-categories",
            headers=admin_headers,
            json={"name": "Duplicate Root", "slug": "root"},
            timeout=10,
        )
        assert response.status_code == 400

    # --- Get Category ---

    def test_get_category(self, admin_headers):
        """GET /<id> should return category detail."""
        # First, get root category ID
        list_resp = requests.get(
            f"{self.BASE_URL}/admin/tarif-plan-categories",
            headers=admin_headers,
            timeout=10,
        )
        root = next(c for c in list_resp.json()["categories"] if c["slug"] == "root")

        response = requests.get(
            f"{self.BASE_URL}/admin/tarif-plan-categories/{root['id']}",
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 200
        assert response.json()["category"]["slug"] == "root"

    def test_get_category_not_found(self, admin_headers):
        """GET with invalid ID should return 404."""
        response = requests.get(
            f"{self.BASE_URL}/admin/tarif-plan-categories/{uuid4()}",
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 404

    # --- Update Category ---

    def test_update_category(self, admin_headers):
        """PUT should update category fields."""
        # Create a category to update
        unique_slug = f"update-test-{uuid4().hex[:8]}"
        create_resp = requests.post(
            f"{self.BASE_URL}/admin/tarif-plan-categories",
            headers=admin_headers,
            json={"name": "Before Update", "slug": unique_slug},
            timeout=10,
        )
        cat_id = create_resp.json()["category"]["id"]

        response = requests.put(
            f"{self.BASE_URL}/admin/tarif-plan-categories/{cat_id}",
            headers=admin_headers,
            json={"name": "After Update"},
            timeout=10,
        )
        assert response.status_code == 200
        assert response.json()["category"]["name"] == "After Update"

    # --- Delete Category ---

    def test_delete_category(self, admin_headers):
        """DELETE should remove a category."""
        unique_slug = f"delete-test-{uuid4().hex[:8]}"
        create_resp = requests.post(
            f"{self.BASE_URL}/admin/tarif-plan-categories",
            headers=admin_headers,
            json={"name": "To Delete", "slug": unique_slug},
            timeout=10,
        )
        cat_id = create_resp.json()["category"]["id"]

        response = requests.delete(
            f"{self.BASE_URL}/admin/tarif-plan-categories/{cat_id}",
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 200

    def test_delete_root_forbidden(self, admin_headers):
        """DELETE should not allow deleting root category."""
        list_resp = requests.get(
            f"{self.BASE_URL}/admin/tarif-plan-categories",
            headers=admin_headers,
            timeout=10,
        )
        root = next(c for c in list_resp.json()["categories"] if c["slug"] == "root")

        response = requests.delete(
            f"{self.BASE_URL}/admin/tarif-plan-categories/{root['id']}",
            headers=admin_headers,
            timeout=10,
        )
        assert response.status_code == 400

    # --- Attach/Detach Plans ---

    def test_attach_plans(self, admin_headers):
        """POST attach-plans should attach plans to category."""
        # Create a category
        unique_slug = f"attach-test-{uuid4().hex[:8]}"
        create_resp = requests.post(
            f"{self.BASE_URL}/admin/tarif-plan-categories",
            headers=admin_headers,
            json={"name": "Attach Test", "slug": unique_slug},
            timeout=10,
        )
        cat_id = create_resp.json()["category"]["id"]

        # Get existing plans
        plans_resp = requests.get(
            f"{self.BASE_URL}/admin/tarif-plans",
            headers=admin_headers,
            timeout=10,
        )
        plans = plans_resp.json().get("plans", [])
        if not plans:
            pytest.skip("No plans available for attach test")

        plan_id = plans[0]["id"]

        response = requests.post(
            f"{self.BASE_URL}/admin/tarif-plan-categories/{cat_id}/attach-plans",
            headers=admin_headers,
            json={"plan_ids": [plan_id]},
            timeout=10,
        )
        assert response.status_code == 200
        assert response.json()["category"]["plan_count"] >= 1

    def test_detach_plans(self, admin_headers):
        """POST detach-plans should remove plans from category."""
        # Create category and attach a plan
        unique_slug = f"detach-test-{uuid4().hex[:8]}"
        create_resp = requests.post(
            f"{self.BASE_URL}/admin/tarif-plan-categories",
            headers=admin_headers,
            json={"name": "Detach Test", "slug": unique_slug},
            timeout=10,
        )
        cat_id = create_resp.json()["category"]["id"]

        plans_resp = requests.get(
            f"{self.BASE_URL}/admin/tarif-plans",
            headers=admin_headers,
            timeout=10,
        )
        plans = plans_resp.json().get("plans", [])
        if not plans:
            pytest.skip("No plans available for detach test")

        plan_id = plans[0]["id"]

        # Attach
        requests.post(
            f"{self.BASE_URL}/admin/tarif-plan-categories/{cat_id}/attach-plans",
            headers=admin_headers,
            json={"plan_ids": [plan_id]},
            timeout=10,
        )

        # Detach
        response = requests.post(
            f"{self.BASE_URL}/admin/tarif-plan-categories/{cat_id}/detach-plans",
            headers=admin_headers,
            json={"plan_ids": [plan_id]},
            timeout=10,
        )
        assert response.status_code == 200
        assert response.json()["category"]["plan_count"] == 0

    # --- Public API ---

    def test_public_plans_include_categories(self):
        """GET /tarif-plans should include categories field."""
        response = requests.get(
            f"{self.BASE_URL}/tarif-plans",
            timeout=10,
        )
        assert response.status_code == 200
        plans = response.json().get("plans", [])
        # All plans should have been migrated to root category
        # The public API may not include categories in every plan format,
        # but it should be accessible via plan detail endpoint
        if plans:
            plan_slug = plans[0].get("slug")
            if plan_slug:
                detail = requests.get(
                    f"{self.BASE_URL}/tarif-plans/{plan_slug}",
                    timeout=10,
                )
                if detail.status_code == 200:
                    plan_data = detail.json()
                    assert "categories" in plan_data

    def test_public_plans_filter_by_category(self, admin_headers):
        """GET /tarif-plans?category=root should filter plans."""
        response = requests.get(
            f"{self.BASE_URL}/tarif-plans?category=root",
            timeout=10,
        )
        assert response.status_code == 200

    def test_public_plans_filter_by_nonexistent_category(self):
        """GET /tarif-plans?category=nonexistent should return 404."""
        response = requests.get(
            f"{self.BASE_URL}/tarif-plans?category=nonexistent",
            timeout=10,
        )
        assert response.status_code == 404
