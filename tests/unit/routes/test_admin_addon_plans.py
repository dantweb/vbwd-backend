"""Tests for admin add-on tarif_plan_ids handling in routes (Sprint 13)."""
from unittest.mock import patch, MagicMock
from uuid import uuid4
from src.models.enums import UserRole


def _mock_admin_auth(mock_auth_user_repo_class, mock_auth_class):
    """Helper: set up mocked admin authentication."""
    admin_id = uuid4()

    mock_admin = MagicMock()
    mock_admin.id = admin_id
    mock_admin.status.value = "ACTIVE"
    mock_admin.role = UserRole.ADMIN

    mock_auth_user_repo = MagicMock()
    mock_auth_user_repo.find_by_id.return_value = mock_admin
    mock_auth_user_repo_class.return_value = mock_auth_user_repo

    mock_auth = MagicMock()
    mock_auth.verify_token.return_value = str(admin_id)
    mock_auth_class.return_value = mock_auth

    return admin_id


class TestAdminCreateAddonWithPlans:
    """Tests for POST /admin/addons/ with tarif_plan_ids."""

    @patch("src.routes.admin.addons.db")
    @patch("src.routes.admin.addons.AddOnRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_create_addon_with_tarif_plan_ids(
        self,
        mock_auth_user_repo_class,
        mock_auth_class,
        mock_addon_repo_class,
        mock_db,
        client,
    ):
        """Creating an addon with tarif_plan_ids should look up plans."""
        _mock_admin_auth(mock_auth_user_repo_class, mock_auth_class)

        plan_id_1 = str(uuid4())
        plan_id_2 = str(uuid4())

        # Mock TarifPlan query
        mock_plan_1 = MagicMock()
        mock_plan_1.id = plan_id_1
        mock_plan_1.name = "Basic"
        mock_plan_2 = MagicMock()
        mock_plan_2.id = plan_id_2
        mock_plan_2.name = "Pro"

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_plan_1, mock_plan_2]
        mock_db.session.query.return_value = mock_query

        # Mock addon repo
        mock_repo = MagicMock()
        mock_repo.slug_exists.return_value = False

        mock_saved = MagicMock()
        mock_saved.to_dict.return_value = {
            "id": str(uuid4()),
            "name": "Support",
            "tarif_plan_ids": [plan_id_1, plan_id_2],
        }
        mock_repo.save.return_value = mock_saved
        mock_addon_repo_class.return_value = mock_repo

        response = client.post(
            "/api/v1/admin/addons/",
            json={
                "name": "Support",
                "price": "10.00",
                "tarif_plan_ids": [plan_id_1, plan_id_2],
            },
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 201
        data = response.get_json()
        assert "addon" in data
        assert data["addon"]["tarif_plan_ids"] == [plan_id_1, plan_id_2]

    @patch("src.routes.admin.addons.db")
    @patch("src.routes.admin.addons.AddOnRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_create_addon_without_plan_ids(
        self,
        mock_auth_user_repo_class,
        mock_auth_class,
        mock_addon_repo_class,
        mock_db,
        client,
    ):
        """Creating an addon without tarif_plan_ids should create independent addon."""
        _mock_admin_auth(mock_auth_user_repo_class, mock_auth_class)

        mock_repo = MagicMock()
        mock_repo.slug_exists.return_value = False

        mock_saved = MagicMock()
        mock_saved.to_dict.return_value = {
            "id": str(uuid4()),
            "name": "Support",
            "tarif_plan_ids": [],
        }
        mock_repo.save.return_value = mock_saved
        mock_addon_repo_class.return_value = mock_repo

        response = client.post(
            "/api/v1/admin/addons/",
            json={"name": "Support", "price": "10.00"},
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 201
        # db.session.query should not be called for TarifPlan when no IDs given
        mock_db.session.query.assert_not_called()

    @patch("src.routes.admin.addons.db")
    @patch("src.routes.admin.addons.AddOnRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_create_addon_with_invalid_plan_id(
        self,
        mock_auth_user_repo_class,
        mock_auth_class,
        mock_addon_repo_class,
        mock_db,
        client,
    ):
        """Creating an addon with non-existent plan IDs should return 400."""
        _mock_admin_auth(mock_auth_user_repo_class, mock_auth_class)

        fake_plan_id = str(uuid4())

        # Return empty — no plans found for given IDs
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db.session.query.return_value = mock_query

        mock_repo = MagicMock()
        mock_repo.slug_exists.return_value = False
        mock_addon_repo_class.return_value = mock_repo

        response = client.post(
            "/api/v1/admin/addons/",
            json={
                "name": "Support",
                "price": "10.00",
                "tarif_plan_ids": [fake_plan_id],
            },
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "invalid" in data["error"].lower()


class TestAdminUpdateAddonWithPlans:
    """Tests for PUT /admin/addons/<id> with tarif_plan_ids."""

    @patch("src.routes.admin.addons.db")
    @patch("src.routes.admin.addons.AddOnRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_update_addon_set_plan_ids(
        self,
        mock_auth_user_repo_class,
        mock_auth_class,
        mock_addon_repo_class,
        mock_db,
        client,
    ):
        """Updating addon with tarif_plan_ids should bind plans."""
        _mock_admin_auth(mock_auth_user_repo_class, mock_auth_class)

        addon_id = str(uuid4())
        plan_id = str(uuid4())

        # Mock existing addon
        mock_addon = MagicMock()
        mock_addon.id = addon_id
        mock_addon.tarif_plans = []

        mock_repo = MagicMock()
        mock_repo.find_by_id.return_value = mock_addon

        mock_saved = MagicMock()
        mock_saved.to_dict.return_value = {
            "id": addon_id,
            "tarif_plan_ids": [plan_id],
        }
        mock_repo.save.return_value = mock_saved
        mock_addon_repo_class.return_value = mock_repo

        # Mock plan lookup
        mock_plan = MagicMock()
        mock_plan.id = plan_id
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_plan]
        mock_db.session.query.return_value = mock_query

        response = client.put(
            f"/api/v1/admin/addons/{addon_id}",
            json={"tarif_plan_ids": [plan_id]},
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 200
        # Verify addon.tarif_plans was set
        assert mock_addon.tarif_plans == [mock_plan]

    @patch("src.routes.admin.addons.db")
    @patch("src.routes.admin.addons.AddOnRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_update_addon_clear_plan_ids(
        self,
        mock_auth_user_repo_class,
        mock_auth_class,
        mock_addon_repo_class,
        mock_db,
        client,
    ):
        """Updating addon with empty tarif_plan_ids should make it independent."""
        _mock_admin_auth(mock_auth_user_repo_class, mock_auth_class)

        addon_id = str(uuid4())

        mock_addon = MagicMock()
        mock_addon.id = addon_id
        mock_addon.tarif_plans = [MagicMock()]  # had a plan

        mock_repo = MagicMock()
        mock_repo.find_by_id.return_value = mock_addon

        mock_saved = MagicMock()
        mock_saved.to_dict.return_value = {"id": addon_id, "tarif_plan_ids": []}
        mock_repo.save.return_value = mock_saved
        mock_addon_repo_class.return_value = mock_repo

        response = client.put(
            f"/api/v1/admin/addons/{addon_id}",
            json={"tarif_plan_ids": []},
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 200
        assert mock_addon.tarif_plans == []

    @patch("src.routes.admin.addons.db")
    @patch("src.routes.admin.addons.AddOnRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_update_addon_with_invalid_plan_id(
        self,
        mock_auth_user_repo_class,
        mock_auth_class,
        mock_addon_repo_class,
        mock_db,
        client,
    ):
        """Updating addon with non-existent plan IDs should return 400."""
        _mock_admin_auth(mock_auth_user_repo_class, mock_auth_class)

        addon_id = str(uuid4())

        mock_addon = MagicMock()
        mock_addon.id = addon_id
        mock_repo = MagicMock()
        mock_repo.find_by_id.return_value = mock_addon
        mock_addon_repo_class.return_value = mock_repo

        # Return fewer plans than requested
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db.session.query.return_value = mock_query

        response = client.put(
            f"/api/v1/admin/addons/{addon_id}",
            json={"tarif_plan_ids": [str(uuid4())]},
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "invalid" in data["error"].lower()


class TestAdminGetAddonIncludesPlanData:
    """Tests for GET /admin/addons/<id> returning plan info."""

    @patch("src.routes.admin.addons.AddOnRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_get_addon_response_includes_tarif_plans(
        self,
        mock_auth_user_repo_class,
        mock_auth_class,
        mock_addon_repo_class,
        client,
    ):
        """GET addon should include tarif_plan_ids and tarif_plans in response."""
        _mock_admin_auth(mock_auth_user_repo_class, mock_auth_class)

        addon_id = str(uuid4())
        plan_id = str(uuid4())

        mock_addon = MagicMock()
        mock_addon.to_dict.return_value = {
            "id": addon_id,
            "name": "Support",
            "tarif_plan_ids": [plan_id],
            "tarif_plans": [{"id": plan_id, "name": "Basic"}],
        }

        mock_repo = MagicMock()
        mock_repo.find_by_id.return_value = mock_addon
        mock_addon_repo_class.return_value = mock_repo

        response = client.get(
            f"/api/v1/admin/addons/{addon_id}",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "tarif_plan_ids" in data["addon"]
        assert "tarif_plans" in data["addon"]
        assert data["addon"]["tarif_plan_ids"] == [plan_id]
        assert data["addon"]["tarif_plans"][0]["name"] == "Basic"
