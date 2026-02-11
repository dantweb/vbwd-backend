"""Tests for admin user addons endpoint."""
from unittest.mock import patch, MagicMock
from uuid import uuid4
from src.models.enums import UserRole, SubscriptionStatus, InvoiceStatus


class TestAdminGetUserAddons:
    """Tests for GET /api/v1/admin/users/<user_id>/addons."""

    def _mock_admin_auth(self, mock_auth_user_repo_class, mock_auth_class):
        """Helper to set up admin authentication mocks."""
        admin_id = uuid4()
        mock_admin = MagicMock()
        mock_admin.id = admin_id
        mock_admin.status.value = "active"
        mock_admin.role = UserRole.ADMIN

        mock_auth_user_repo = MagicMock()
        mock_auth_user_repo.find_by_id.return_value = mock_admin
        mock_auth_user_repo_class.return_value = mock_auth_user_repo

        mock_auth = MagicMock()
        mock_auth.verify_token.return_value = str(admin_id)
        mock_auth_class.return_value = mock_auth

        return admin_id

    @patch("src.routes.admin.users.UserRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_returns_addon_subscriptions_for_user(
        self,
        mock_auth_user_repo_class,
        mock_auth_class,
        mock_user_repo_class,
        client,
        app,
    ):
        """Admin can get addon subscriptions for a user."""
        self._mock_admin_auth(mock_auth_user_repo_class, mock_auth_class)

        user_id = uuid4()
        addon_sub_id = uuid4()
        invoice_id = uuid4()

        # Mock user exists
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = mock_user
        mock_user_repo_class.return_value = mock_user_repo

        # Mock addon subscription
        mock_addon = MagicMock()
        mock_addon.name = "Extra Storage"

        mock_addon_sub = MagicMock()
        mock_addon_sub.id = addon_sub_id
        mock_addon_sub.addon = mock_addon
        mock_addon_sub.status = SubscriptionStatus.ACTIVE
        mock_addon_sub.starts_at = None
        mock_addon_sub.expires_at = None
        mock_addon_sub.created_at = None
        mock_addon_sub.invoice_id = invoice_id

        # Mock invoice
        mock_invoice = MagicMock()
        mock_invoice.id = invoice_id
        mock_invoice.invoice_number = "INV-001"
        mock_invoice.status = InvoiceStatus.PAID
        mock_invoice.invoiced_at = None

        # Set up container mocks
        mock_addon_sub_repo = MagicMock()
        mock_addon_sub_repo.find_by_user.return_value = [mock_addon_sub]

        mock_invoice_repo = MagicMock()
        mock_invoice_repo.find_by_id.return_value = mock_invoice

        with app.app_context():
            app.container = MagicMock()
            app.container.addon_subscription_repository.return_value = (
                mock_addon_sub_repo
            )
            app.container.invoice_repository.return_value = mock_invoice_repo

            response = client.get(
                f"/api/v1/admin/users/{user_id}/addons",
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert "addon_subscriptions" in data
        assert len(data["addon_subscriptions"]) == 1
        assert data["addon_subscriptions"][0]["addon_name"] == "Extra Storage"
        assert data["addon_subscriptions"][0]["status"] == "active"

    @patch("src.routes.admin.users.UserRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_returns_empty_list_for_user_with_no_addons(
        self,
        mock_auth_user_repo_class,
        mock_auth_class,
        mock_user_repo_class,
        client,
        app,
    ):
        """Returns empty list when user has no addon subscriptions."""
        self._mock_admin_auth(mock_auth_user_repo_class, mock_auth_class)

        user_id = uuid4()

        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = mock_user
        mock_user_repo_class.return_value = mock_user_repo

        mock_addon_sub_repo = MagicMock()
        mock_addon_sub_repo.find_by_user.return_value = []

        with app.app_context():
            app.container = MagicMock()
            app.container.addon_subscription_repository.return_value = (
                mock_addon_sub_repo
            )

            response = client.get(
                f"/api/v1/admin/users/{user_id}/addons",
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["addon_subscriptions"] == []

    @patch("src.routes.admin.users.UserRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_includes_invoice_data_in_response(
        self,
        mock_auth_user_repo_class,
        mock_auth_class,
        mock_user_repo_class,
        client,
        app,
    ):
        """Invoice data is included when addon has a linked invoice."""
        self._mock_admin_auth(mock_auth_user_repo_class, mock_auth_class)

        user_id = uuid4()
        invoice_id = uuid4()

        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = mock_user
        mock_user_repo_class.return_value = mock_user_repo

        mock_addon = MagicMock()
        mock_addon.name = "Priority Support"

        mock_addon_sub = MagicMock()
        mock_addon_sub.id = uuid4()
        mock_addon_sub.addon = mock_addon
        mock_addon_sub.status = SubscriptionStatus.ACTIVE
        mock_addon_sub.starts_at = None
        mock_addon_sub.expires_at = None
        mock_addon_sub.created_at = None
        mock_addon_sub.invoice_id = invoice_id

        mock_invoice = MagicMock()
        mock_invoice.id = invoice_id
        mock_invoice.invoice_number = "INV-100"
        mock_invoice.status = InvoiceStatus.PAID
        mock_invoice.invoiced_at = None

        mock_addon_sub_repo = MagicMock()
        mock_addon_sub_repo.find_by_user.return_value = [mock_addon_sub]

        mock_invoice_repo = MagicMock()
        mock_invoice_repo.find_by_id.return_value = mock_invoice

        with app.app_context():
            app.container = MagicMock()
            app.container.addon_subscription_repository.return_value = (
                mock_addon_sub_repo
            )
            app.container.invoice_repository.return_value = mock_invoice_repo

            response = client.get(
                f"/api/v1/admin/users/{user_id}/addons",
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 200
        data = response.get_json()
        addon = data["addon_subscriptions"][0]
        assert addon["invoice_status"] == "paid"
        assert addon["first_invoice"]["invoice_number"] == "INV-100"
        assert addon["last_invoice"]["invoice_number"] == "INV-100"

    @patch("src.routes.admin.users.UserRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_returns_404_for_nonexistent_user(
        self, mock_auth_user_repo_class, mock_auth_class, mock_user_repo_class, client
    ):
        """Returns 404 when user does not exist."""
        self._mock_admin_auth(mock_auth_user_repo_class, mock_auth_class)

        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = None
        mock_user_repo_class.return_value = mock_user_repo

        response = client.get(
            f"/api/v1/admin/users/{uuid4()}/addons",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 404

    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_requires_admin_auth(self, mock_user_repo_class, mock_auth_class, client):
        """Regular user cannot access admin addon endpoint."""
        user_id = uuid4()

        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.status.value = "active"
        mock_user.role = UserRole.USER

        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = mock_user
        mock_user_repo_class.return_value = mock_user_repo

        mock_auth = MagicMock()
        mock_auth.verify_token.return_value = str(user_id)
        mock_auth_class.return_value = mock_auth

        response = client.get(
            f"/api/v1/admin/users/{uuid4()}/addons",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 403
