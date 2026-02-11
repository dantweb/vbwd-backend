"""Tests for user addon detail and cancel endpoints."""
from unittest.mock import patch, MagicMock
from uuid import uuid4
from src.models.enums import SubscriptionStatus, InvoiceStatus


class TestGetAddonDetail:
    """Tests for GET /api/v1/user/addons/<addon_sub_id>."""

    def _mock_user_auth(self, mock_auth_user_repo_class, mock_auth_class, user_id=None):
        """Helper to set up user authentication mocks."""
        if user_id is None:
            user_id = uuid4()

        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.status.value = "active"

        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = mock_user
        mock_auth_user_repo_class.return_value = mock_user_repo

        mock_auth = MagicMock()
        mock_auth.verify_token.return_value = str(user_id)
        mock_auth_class.return_value = mock_auth

        return user_id

    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_returns_addon_detail_with_addon_info(
        self, mock_auth_user_repo_class, mock_auth_class, client, app
    ):
        """Returns addon subscription with addon and invoice details."""
        user_id = self._mock_user_auth(mock_auth_user_repo_class, mock_auth_class)
        addon_sub_id = uuid4()
        invoice_id = uuid4()

        mock_addon = MagicMock()
        mock_addon.name = "Extra Storage"
        mock_addon.slug = "extra-storage"
        mock_addon.description = "More storage"
        mock_addon.price = 9.99
        mock_addon.billing_period = "monthly"

        mock_addon_sub = MagicMock()
        mock_addon_sub.id = addon_sub_id
        mock_addon_sub.user_id = user_id
        mock_addon_sub.addon_id = uuid4()
        mock_addon_sub.subscription_id = None
        mock_addon_sub.invoice_id = invoice_id
        mock_addon_sub.status = SubscriptionStatus.ACTIVE
        mock_addon_sub.is_valid = True
        mock_addon_sub.starts_at = None
        mock_addon_sub.expires_at = None
        mock_addon_sub.cancelled_at = None
        mock_addon_sub.created_at = None
        mock_addon_sub.addon = mock_addon
        mock_addon_sub.to_dict.return_value = {
            "id": str(addon_sub_id),
            "user_id": str(user_id),
            "addon_id": str(mock_addon_sub.addon_id),
            "subscription_id": None,
            "invoice_id": str(invoice_id),
            "status": "active",
            "is_valid": True,
            "starts_at": None,
            "expires_at": None,
            "cancelled_at": None,
            "created_at": None,
        }

        mock_invoice = MagicMock()
        mock_invoice.id = invoice_id
        mock_invoice.invoice_number = "INV-001"
        mock_invoice.status = InvoiceStatus.PAID
        mock_invoice.amount = 9.99
        mock_invoice.currency = "USD"

        mock_addon_sub_repo = MagicMock()
        mock_addon_sub_repo.find_by_id.return_value = mock_addon_sub

        mock_invoice_repo = MagicMock()
        mock_invoice_repo.find_by_id.return_value = mock_invoice

        with app.app_context():
            app.container = MagicMock()
            app.container.addon_subscription_repository.return_value = (
                mock_addon_sub_repo
            )
            app.container.invoice_repository.return_value = mock_invoice_repo

            response = client.get(
                f"/api/v1/user/addons/{addon_sub_id}",
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert "addon_subscription" in data
        assert data["addon_subscription"]["addon"]["name"] == "Extra Storage"
        assert data["addon_subscription"]["invoice"]["invoice_number"] == "INV-001"

    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_returns_404_for_nonexistent(
        self, mock_auth_user_repo_class, mock_auth_class, client, app
    ):
        """Returns 404 when addon subscription does not exist."""
        self._mock_user_auth(mock_auth_user_repo_class, mock_auth_class)

        mock_addon_sub_repo = MagicMock()
        mock_addon_sub_repo.find_by_id.return_value = None

        with app.app_context():
            app.container = MagicMock()
            app.container.addon_subscription_repository.return_value = (
                mock_addon_sub_repo
            )

            response = client.get(
                f"/api/v1/user/addons/{uuid4()}",
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 404

    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_returns_403_for_other_users_addon(
        self, mock_auth_user_repo_class, mock_auth_class, client, app
    ):
        """Returns 403 when accessing another user's addon subscription."""
        self._mock_user_auth(mock_auth_user_repo_class, mock_auth_class)
        other_user_id = uuid4()

        mock_addon_sub = MagicMock()
        mock_addon_sub.id = uuid4()
        mock_addon_sub.user_id = other_user_id  # Different user

        mock_addon_sub_repo = MagicMock()
        mock_addon_sub_repo.find_by_id.return_value = mock_addon_sub

        with app.app_context():
            app.container = MagicMock()
            app.container.addon_subscription_repository.return_value = (
                mock_addon_sub_repo
            )

            response = client.get(
                f"/api/v1/user/addons/{mock_addon_sub.id}",
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 403


class TestCancelAddon:
    """Tests for POST /api/v1/user/addons/<addon_sub_id>/cancel."""

    def _mock_user_auth(self, mock_auth_user_repo_class, mock_auth_class, user_id=None):
        """Helper to set up user authentication mocks."""
        if user_id is None:
            user_id = uuid4()

        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.status.value = "active"

        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = mock_user
        mock_auth_user_repo_class.return_value = mock_user_repo

        mock_auth = MagicMock()
        mock_auth.verify_token.return_value = str(user_id)
        mock_auth_class.return_value = mock_auth

        return user_id

    @patch("src.routes.user.db")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_cancel_succeeds_for_active_addon(
        self, mock_auth_user_repo_class, mock_auth_class, mock_db, client, app
    ):
        """Successfully cancels an active addon subscription."""
        user_id = self._mock_user_auth(mock_auth_user_repo_class, mock_auth_class)
        addon_sub_id = uuid4()

        mock_addon_sub = MagicMock()
        mock_addon_sub.id = addon_sub_id
        mock_addon_sub.user_id = user_id
        mock_addon_sub.status = SubscriptionStatus.ACTIVE
        mock_addon_sub.to_dict.return_value = {
            "id": str(addon_sub_id),
            "status": "cancelled",
        }

        mock_addon_sub_repo = MagicMock()
        mock_addon_sub_repo.find_by_id.return_value = mock_addon_sub

        with app.app_context():
            app.container = MagicMock()
            app.container.addon_subscription_repository.return_value = (
                mock_addon_sub_repo
            )

            response = client.post(
                f"/api/v1/user/addons/{addon_sub_id}/cancel",
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert "addon_subscription" in data
        assert "message" in data
        mock_addon_sub.cancel.assert_called_once()

    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_cancel_fails_for_already_cancelled(
        self, mock_auth_user_repo_class, mock_auth_class, client, app
    ):
        """Cannot cancel an already cancelled addon subscription."""
        user_id = self._mock_user_auth(mock_auth_user_repo_class, mock_auth_class)
        addon_sub_id = uuid4()

        mock_addon_sub = MagicMock()
        mock_addon_sub.id = addon_sub_id
        mock_addon_sub.user_id = user_id
        mock_addon_sub.status = SubscriptionStatus.CANCELLED

        mock_addon_sub_repo = MagicMock()
        mock_addon_sub_repo.find_by_id.return_value = mock_addon_sub

        with app.app_context():
            app.container = MagicMock()
            app.container.addon_subscription_repository.return_value = (
                mock_addon_sub_repo
            )

            response = client.post(
                f"/api/v1/user/addons/{addon_sub_id}/cancel",
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 400

    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_cancel_returns_403_for_other_users_addon(
        self, mock_auth_user_repo_class, mock_auth_class, client, app
    ):
        """Cannot cancel another user's addon subscription."""
        self._mock_user_auth(mock_auth_user_repo_class, mock_auth_class)
        other_user_id = uuid4()

        mock_addon_sub = MagicMock()
        mock_addon_sub.id = uuid4()
        mock_addon_sub.user_id = other_user_id  # Different user

        mock_addon_sub_repo = MagicMock()
        mock_addon_sub_repo.find_by_id.return_value = mock_addon_sub

        with app.app_context():
            app.container = MagicMock()
            app.container.addon_subscription_repository.return_value = (
                mock_addon_sub_repo
            )

            response = client.post(
                f"/api/v1/user/addons/{mock_addon_sub.id}/cancel",
                headers={"Authorization": "Bearer valid_token"},
            )

        assert response.status_code == 403
