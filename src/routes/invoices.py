"""Invoice routes."""
from flask import Blueprint, jsonify, g
from src.middleware.auth import require_auth
from src.services.invoice_service import InvoiceService
from src.repositories.invoice_repository import InvoiceRepository
from src.extensions import db

# Create blueprint
invoices_bp = Blueprint("invoices", __name__, url_prefix="/api/v1/user/invoices")


@invoices_bp.route("/", methods=["GET"])
@require_auth
def get_invoices():
    """
    List user's invoices.

    Returns:
        200: List of user's invoices
        401: If not authenticated
    """
    # Initialize service
    invoice_repo = InvoiceRepository(db.session)
    invoice_service = InvoiceService(invoice_repository=invoice_repo)

    # Get user's invoices
    invoices = invoice_service.get_user_invoices(str(g.user_id))

    return jsonify({"invoices": [inv.to_dict() for inv in invoices]}), 200


@invoices_bp.route("/<invoice_id>", methods=["GET"])
@require_auth
def get_invoice(invoice_id):
    """
    Get invoice detail.

    Args:
        invoice_id: ID of the invoice

    Returns:
        200: Invoice details
        401: If not authenticated
        403: If user doesn't own the invoice
        404: If invoice not found
    """
    # Initialize service
    invoice_repo = InvoiceRepository(db.session)
    invoice_service = InvoiceService(invoice_repository=invoice_repo)

    # Get invoice
    invoice = invoice_service.get_invoice(invoice_id)

    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    # Check ownership
    if str(invoice.user_id) != str(g.user_id):
        return jsonify({"error": "Access denied"}), 403

    return jsonify({"invoice": invoice.to_dict()}), 200
