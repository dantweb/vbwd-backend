"""Tests for invoice routes."""
from unittest.mock import patch, MagicMock
from uuid import uuid4


class TestInvoiceRoutes:
    """Tests for invoice route endpoints."""

    @patch("src.routes.invoices.InvoiceService")
    @patch("src.routes.invoices.InvoiceRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_get_invoices_authenticated(
        self,
        mock_user_repo_class,
        mock_auth_class,
        mock_invoice_repo_class,
        mock_service_class,
        client,
    ):
        """Get invoices returns list for authenticated user."""
        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.status.value = "ACTIVE"
        mock_user.id = user_id

        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = mock_user
        mock_user_repo_class.return_value = mock_user_repo

        mock_auth = MagicMock()
        mock_auth.verify_token.return_value = str(user_id)
        mock_auth_class.return_value = mock_auth

        mock_invoices = [
            MagicMock(to_dict=lambda: {"id": str(uuid4()), "amount": "99.99"}),
            MagicMock(to_dict=lambda: {"id": str(uuid4()), "amount": "49.99"}),
        ]
        mock_service = MagicMock()
        mock_service.get_user_invoices.return_value = mock_invoices
        mock_service_class.return_value = mock_service

        response = client.get(
            "/api/v1/user/invoices/", headers={"Authorization": "Bearer valid_token"}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "invoices" in data
        assert len(data["invoices"]) == 2

    def test_get_invoices_unauthenticated(self, client):
        """Get invoices returns 401 for unauthenticated user."""
        response = client.get("/api/v1/user/invoices/")

        assert response.status_code == 401

    @patch("src.routes.invoices.InvoiceService")
    @patch("src.routes.invoices.InvoiceRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_get_invoice_detail(
        self,
        mock_user_repo_class,
        mock_auth_class,
        mock_invoice_repo_class,
        mock_service_class,
        client,
    ):
        """Get invoice detail returns invoice."""
        user_id = uuid4()
        invoice_id = uuid4()

        mock_user = MagicMock()
        mock_user.status.value = "ACTIVE"
        mock_user.id = user_id

        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = mock_user
        mock_user_repo_class.return_value = mock_user_repo

        mock_auth = MagicMock()
        mock_auth.verify_token.return_value = str(user_id)
        mock_auth_class.return_value = mock_auth

        mock_invoice = MagicMock()
        mock_invoice.user_id = user_id
        mock_invoice.to_dict.return_value = {
            "id": str(invoice_id),
            "user_id": str(user_id),
            "amount": "99.99",
            "status": "pending",
        }

        mock_service = MagicMock()
        mock_service.get_invoice.return_value = mock_invoice
        mock_service_class.return_value = mock_service

        response = client.get(
            f"/api/v1/user/invoices/{invoice_id}",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "invoice" in data
        assert data["invoice"]["id"] == str(invoice_id)

    @patch("src.routes.invoices.InvoiceService")
    @patch("src.routes.invoices.InvoiceRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_get_invoice_not_found(
        self,
        mock_user_repo_class,
        mock_auth_class,
        mock_invoice_repo_class,
        mock_service_class,
        client,
    ):
        """Get invoice returns 404 when not found."""
        user_id = uuid4()

        mock_user = MagicMock()
        mock_user.status.value = "ACTIVE"
        mock_user.id = user_id

        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = mock_user
        mock_user_repo_class.return_value = mock_user_repo

        mock_auth = MagicMock()
        mock_auth.verify_token.return_value = str(user_id)
        mock_auth_class.return_value = mock_auth

        mock_service = MagicMock()
        mock_service.get_invoice.return_value = None
        mock_service_class.return_value = mock_service

        response = client.get(
            f"/api/v1/user/invoices/{uuid4()}",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 404

    @patch("src.routes.invoices.InvoiceService")
    @patch("src.routes.invoices.InvoiceRepository")
    @patch("src.middleware.auth.AuthService")
    @patch("src.middleware.auth.UserRepository")
    def test_get_invoice_not_owned(
        self,
        mock_user_repo_class,
        mock_auth_class,
        mock_invoice_repo_class,
        mock_service_class,
        client,
    ):
        """Get invoice returns 403 when user doesn't own it."""
        user_id = uuid4()
        other_user_id = uuid4()
        invoice_id = uuid4()

        mock_user = MagicMock()
        mock_user.status.value = "ACTIVE"
        mock_user.id = user_id

        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = mock_user
        mock_user_repo_class.return_value = mock_user_repo

        mock_auth = MagicMock()
        mock_auth.verify_token.return_value = str(user_id)
        mock_auth_class.return_value = mock_auth

        mock_invoice = MagicMock()
        mock_invoice.user_id = other_user_id  # Different user

        mock_service = MagicMock()
        mock_service.get_invoice.return_value = mock_invoice
        mock_service_class.return_value = mock_service

        response = client.get(
            f"/api/v1/user/invoices/{invoice_id}",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == 403
