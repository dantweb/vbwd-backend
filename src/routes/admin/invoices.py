"""Admin invoice management routes."""
from flask import Blueprint, jsonify, request
from src.middleware.auth import require_auth, require_admin
from src.repositories.invoice_repository import InvoiceRepository
from src.repositories.user_repository import UserRepository
from src.services.invoice_service import InvoiceService
from src.extensions import db

admin_invoices_bp = Blueprint(
    "admin_invoices", __name__, url_prefix="/api/v1/admin/invoices"
)


@admin_invoices_bp.route("/", methods=["GET"])
@require_auth
@require_admin
def list_invoices():
    """
    List all invoices with pagination and filters.

    Query params:
        - limit: int (default 20, max 100)
        - offset: int (default 0)
        - status: str (pending, paid, failed, cancelled, refunded)
        - user_id: str (filter by user)

    Returns:
        200: List of invoices with pagination info
    """
    limit = min(int(request.args.get("limit", 20)), 100)
    offset = int(request.args.get("offset", 0))
    status = request.args.get("status")
    user_id = request.args.get("user_id")

    invoice_repo = InvoiceRepository(db.session)
    user_repo = UserRepository(db.session)

    invoices, total = invoice_repo.find_all_paginated(
        limit=limit, offset=offset, status=status, user_id=user_id
    )

    # Enrich invoices with user info for admin display
    result = []
    for inv in invoices:
        inv_dict = inv.to_dict()
        # Add user email
        user = user_repo.find_by_id(str(inv.user_id))
        inv_dict["user_email"] = user.email if user else ""
        # Add created_at for sorting
        inv_dict["created_at"] = inv.created_at.isoformat() if inv.created_at else None
        result.append(inv_dict)

    return (
        jsonify({"invoices": result, "total": total, "limit": limit, "offset": offset}),
        200,
    )


@admin_invoices_bp.route("/<invoice_id>", methods=["GET"])
@require_auth
@require_admin
def get_invoice(invoice_id):
    """
    Get invoice detail with enriched user, plan, and subscription data.

    Args:
        invoice_id: UUID of the invoice

    Returns:
        200: Invoice details with user, plan, subscription info
        404: Invoice not found
    """
    from src.repositories.tarif_plan_repository import TarifPlanRepository
    from src.repositories.subscription_repository import SubscriptionRepository

    invoice_repo = InvoiceRepository(db.session)
    user_repo = UserRepository(db.session)
    plan_repo = TarifPlanRepository(db.session)
    subscription_repo = SubscriptionRepository(db.session)

    invoice = invoice_repo.find_by_id(invoice_id)

    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    inv_dict = invoice.to_dict()

    # Enrich with user info
    user = user_repo.find_by_id(str(invoice.user_id))
    if user:
        inv_dict["user_email"] = user.email
        inv_dict["user_name"] = (
            user.details.first_name + " " + user.details.last_name
            if user.details
            else ""
        )

    # Enrich with tariff plan info
    plan = plan_repo.find_by_id(str(invoice.tarif_plan_id))
    if plan:
        inv_dict["plan_name"] = plan.name
        inv_dict["plan_description"] = plan.description
        inv_dict["plan_billing_period"] = (
            plan.billing_period.value if plan.billing_period else None
        )
        inv_dict["plan_price"] = str(plan.price) if plan.price else None

    # Enrich with subscription info
    if invoice.subscription_id:
        subscription = subscription_repo.find_by_id(str(invoice.subscription_id))
        if subscription:
            inv_dict["subscription_status"] = (
                subscription.status.value if subscription.status else None
            )
            inv_dict["subscription_start_date"] = (
                subscription.started_at.isoformat() if subscription.started_at else None
            )
            inv_dict["subscription_end_date"] = (
                subscription.expires_at.isoformat() if subscription.expires_at else None
            )
            inv_dict["subscription_is_trial"] = False  # No trial flag in current model
            inv_dict["subscription_trial_end"] = None

    # Add line items (for now, generate from invoice data)
    inv_dict["line_items"] = [
        {
            "description": inv_dict.get("plan_name", "Subscription"),
            "quantity": 1,
            "unit_price": float(invoice.amount),
            "amount": float(invoice.amount),
        }
    ]

    # Add due_date and created_at
    inv_dict["due_date"] = (
        invoice.expires_at.isoformat()
        if invoice.expires_at
        else invoice.invoiced_at.isoformat()
        if invoice.invoiced_at
        else None
    )
    inv_dict["created_at"] = (
        invoice.created_at.isoformat() if invoice.created_at else None
    )

    return jsonify({"invoice": inv_dict}), 200


@admin_invoices_bp.route("/<invoice_id>/duplicate", methods=["POST"])
@require_auth
@require_admin
def duplicate_invoice(invoice_id):
    """
    Create a new invoice based on an existing one.

    Creates a new invoice for the same user, plan, and subscription
    but with a new invoice number and current date.

    Args:
        invoice_id: UUID of the source invoice

    Returns:
        201: New invoice created
        404: Source invoice not found
    """
    from src.models.invoice import UserInvoice
    from datetime import datetime, timedelta

    invoice_repo = InvoiceRepository(db.session)
    source_invoice = invoice_repo.find_by_id(invoice_id)

    if not source_invoice:
        return jsonify({"error": "Invoice not found"}), 404

    # Create new invoice with same data but new number and date
    new_invoice = UserInvoice(
        user_id=source_invoice.user_id,
        tarif_plan_id=source_invoice.tarif_plan_id,
        subscription_id=source_invoice.subscription_id,
        invoice_number=UserInvoice.generate_invoice_number(),
        amount=source_invoice.amount,
        currency=source_invoice.currency,
        invoiced_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
    )

    db.session.add(new_invoice)
    db.session.commit()

    return (
        jsonify(
            {
                "invoice": new_invoice.to_dict(),
                "message": "Invoice duplicated successfully",
            }
        ),
        201,
    )


@admin_invoices_bp.route("/<invoice_id>/mark-paid", methods=["POST"])
@require_auth
@require_admin
def mark_paid(invoice_id):
    """
    Mark invoice as paid manually.

    Args:
        invoice_id: UUID of the invoice

    Body:
        - payment_reference: str (required)
        - payment_method: str (default: 'manual')

    Returns:
        200: Invoice marked as paid
        404: Invoice not found
        400: Invalid operation
    """
    data = request.get_json() or {}
    payment_reference = data.get("payment_reference", "MANUAL")
    payment_method = data.get("payment_method", "manual")

    invoice_repo = InvoiceRepository(db.session)
    invoice_service = InvoiceService(invoice_repository=invoice_repo)

    result = invoice_service.mark_paid(invoice_id, payment_reference, payment_method)

    if not result.success:
        if "not found" in result.error.lower():
            return jsonify({"error": result.error}), 404
        return jsonify({"error": result.error}), 400

    return (
        jsonify(
            {"invoice": result.invoice.to_dict(), "message": "Invoice marked as paid"}
        ),
        200,
    )


@admin_invoices_bp.route("/<invoice_id>/void", methods=["POST"])
@require_auth
@require_admin
def void_invoice(invoice_id):
    """
    Void/cancel an invoice.

    Args:
        invoice_id: UUID of the invoice

    Returns:
        200: Invoice voided
        404: Invoice not found
    """
    invoice_repo = InvoiceRepository(db.session)
    invoice_service = InvoiceService(invoice_repository=invoice_repo)

    result = invoice_service.mark_cancelled(invoice_id)

    if not result.success:
        if "not found" in result.error.lower():
            return jsonify({"error": result.error}), 404
        return jsonify({"error": result.error}), 400

    return (
        jsonify({"invoice": result.invoice.to_dict(), "message": "Invoice voided"}),
        200,
    )


@admin_invoices_bp.route("/<invoice_id>/refund", methods=["POST"])
@require_auth
@require_admin
def refund_invoice(invoice_id):
    """
    Refund a paid invoice.

    Args:
        invoice_id: UUID of the invoice

    Body:
        - refund_reference: str (optional)

    Returns:
        200: Invoice refunded
        404: Invoice not found
        400: Invoice cannot be refunded
    """
    data = request.get_json() or {}
    refund_reference = data.get("refund_reference", "ADMIN_REFUND")

    invoice_repo = InvoiceRepository(db.session)
    invoice_service = InvoiceService(invoice_repository=invoice_repo)

    result = invoice_service.mark_refunded(invoice_id, refund_reference)

    if not result.success:
        if "not found" in result.error.lower():
            return jsonify({"error": result.error}), 404
        return jsonify({"error": result.error}), 400

    return (
        jsonify({"invoice": result.invoice.to_dict(), "message": "Invoice refunded"}),
        200,
    )


@admin_invoices_bp.route("/<invoice_id>/pdf", methods=["GET"])
@require_auth
@require_admin
def download_pdf(invoice_id):
    """
    Download invoice PDF.

    Args:
        invoice_id: UUID of the invoice

    Returns:
        200: PDF file
        404: Invoice not found
    """
    invoice_repo = InvoiceRepository(db.session)
    invoice = invoice_repo.find_by_id(invoice_id)

    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    # For now, return invoice data as JSON (PDF generation would be a separate service)
    return (
        jsonify(
            {"invoice": invoice.to_dict(), "message": "PDF generation not implemented"}
        ),
        200,
    )
