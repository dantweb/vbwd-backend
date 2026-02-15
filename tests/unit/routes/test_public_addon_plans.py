"""Tests for public add-on route with plan filtering (Sprint 13)."""
from unittest.mock import patch, MagicMock
from uuid import uuid4
from src.models.enums import SubscriptionStatus


class TestPublicAddonPlanFiltering:
    """Tests for GET /api/v1/addons/ with plan-based filtering."""

    @patch("src.routes.addons.AddOnRepository")
    def test_unauthenticated_user_gets_independent_addons(
        self, mock_addon_repo_class, client
    ):
        """Unauthenticated user should see only independent add-ons."""
        mock_addon_1 = MagicMock()
        mock_addon_1.to_dict.return_value = {
            "id": str(uuid4()),
            "name": "Independent Addon",
            "tarif_plan_ids": [],
        }

        mock_repo = MagicMock()
        mock_repo.find_available_for_plan.return_value = [mock_addon_1]
        mock_addon_repo_class.return_value = mock_repo

        response = client.get("/api/v1/addons/")

        assert response.status_code == 200
        # Called with plan_id=None for unauthenticated user
        mock_repo.find_available_for_plan.assert_called_once_with(None)

    @patch("src.routes.addons.db")
    @patch("src.routes.addons.AddOnRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_authenticated_user_with_subscription_gets_plan_addons(
        self,
        mock_auth_user_repo_class,
        mock_auth_class,
        mock_addon_repo_class,
        mock_db,
        client,
    ):
        """Authenticated user with active subscription should get plan-specific addons."""
        user_id = uuid4()
        plan_id = uuid4()

        # Mock auth
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.status.value = "ACTIVE"

        mock_auth_user_repo = MagicMock()
        mock_auth_user_repo.find_by_id.return_value = mock_user
        mock_auth_user_repo_class.return_value = mock_auth_user_repo

        mock_auth = MagicMock()
        mock_auth.verify_token.return_value = str(user_id)
        mock_auth_class.return_value = mock_auth

        # Mock subscription query
        mock_subscription = MagicMock()
        mock_subscription.tarif_plan_id = plan_id
        mock_subscription.status = SubscriptionStatus.ACTIVE

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_subscription
        mock_db.session.query.return_value = mock_query

        # Mock addons
        mock_repo = MagicMock()
        mock_repo.find_available_for_plan.return_value = []
        mock_addon_repo_class.return_value = mock_repo

        response = client.get(
            "/api/v1/addons/",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 200
        mock_repo.find_available_for_plan.assert_called_once_with(plan_id)

    @patch("src.routes.addons.db")
    @patch("src.routes.addons.AddOnRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_authenticated_user_without_subscription_gets_independent_only(
        self,
        mock_auth_user_repo_class,
        mock_auth_class,
        mock_addon_repo_class,
        mock_db,
        client,
    ):
        """Authenticated user without subscription should get only independent addons."""
        user_id = uuid4()

        # Mock auth
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.status.value = "ACTIVE"

        mock_auth_user_repo = MagicMock()
        mock_auth_user_repo.find_by_id.return_value = mock_user
        mock_auth_user_repo_class.return_value = mock_auth_user_repo

        mock_auth = MagicMock()
        mock_auth.verify_token.return_value = str(user_id)
        mock_auth_class.return_value = mock_auth

        # No active subscription
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.session.query.return_value = mock_query

        # Mock addons
        mock_repo = MagicMock()
        mock_repo.find_available_for_plan.return_value = []
        mock_addon_repo_class.return_value = mock_repo

        response = client.get(
            "/api/v1/addons/",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 200
        mock_repo.find_available_for_plan.assert_called_once_with(None)

    @patch("src.routes.addons.AddOnRepository")
    def test_public_addons_returns_correct_structure(
        self, mock_addon_repo_class, client
    ):
        """Response should have addons list with tarif_plan fields."""
        plan_id = str(uuid4())

        mock_addon = MagicMock()
        mock_addon.to_dict.return_value = {
            "id": str(uuid4()),
            "name": "Extra Storage",
            "tarif_plan_ids": [plan_id],
            "tarif_plans": [{"id": plan_id, "name": "Pro"}],
            "is_active": True,
        }

        mock_repo = MagicMock()
        mock_repo.find_available_for_plan.return_value = [mock_addon]
        mock_addon_repo_class.return_value = mock_repo

        response = client.get("/api/v1/addons/")

        assert response.status_code == 200
        data = response.get_json()
        assert "addons" in data
        assert len(data["addons"]) == 1
        assert "tarif_plan_ids" in data["addons"][0]
        assert "tarif_plans" in data["addons"][0]
