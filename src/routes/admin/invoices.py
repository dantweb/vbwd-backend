"""Admin invoice management routes."""
from flask import Blueprint, jsonify, request
from src.middleware.auth import require_auth, require_admin
from src.repositories.invoice_repository import InvoiceRepository
from src.services.invoice_service import InvoiceService
from src.extensions import db

admin_invoices_bp = Blueprint('admin_invoices', __name__, url_prefix='/api/v1/admin/invoices')


@admin_invoices_bp.route('/', methods=['GET'])
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
    limit = min(int(request.args.get('limit', 20)), 100)
    offset = int(request.args.get('offset', 0))
    status = request.args.get('status')
    user_id = request.args.get('user_id')

    invoice_repo = InvoiceRepository(db.session)

    invoices, total = invoice_repo.find_all_paginated(
        limit=limit,
        offset=offset,
        status=status,
        user_id=user_id
    )

    return jsonify({
        'invoices': [inv.to_dict() for inv in invoices],
        'total': total,
        'limit': limit,
        'offset': offset
    }), 200


@admin_invoices_bp.route('/<invoice_id>', methods=['GET'])
@require_auth
@require_admin
def get_invoice(invoice_id):
    """
    Get invoice detail.

    Args:
        invoice_id: UUID of the invoice

    Returns:
        200: Invoice details
        404: Invoice not found
    """
    invoice_repo = InvoiceRepository(db.session)
    invoice = invoice_repo.find_by_id(invoice_id)

    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    return jsonify({
        'invoice': invoice.to_dict()
    }), 200


@admin_invoices_bp.route('/<invoice_id>/mark-paid', methods=['POST'])
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
    payment_reference = data.get('payment_reference', 'MANUAL')
    payment_method = data.get('payment_method', 'manual')

    invoice_repo = InvoiceRepository(db.session)
    invoice_service = InvoiceService(invoice_repository=invoice_repo)

    result = invoice_service.mark_paid(invoice_id, payment_reference, payment_method)

    if not result.success:
        if "not found" in result.error.lower():
            return jsonify({'error': result.error}), 404
        return jsonify({'error': result.error}), 400

    return jsonify({
        'invoice': result.invoice.to_dict(),
        'message': 'Invoice marked as paid'
    }), 200


@admin_invoices_bp.route('/<invoice_id>/void', methods=['POST'])
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
            return jsonify({'error': result.error}), 404
        return jsonify({'error': result.error}), 400

    return jsonify({
        'invoice': result.invoice.to_dict(),
        'message': 'Invoice voided'
    }), 200


@admin_invoices_bp.route('/<invoice_id>/refund', methods=['POST'])
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
    refund_reference = data.get('refund_reference', 'ADMIN_REFUND')

    invoice_repo = InvoiceRepository(db.session)
    invoice_service = InvoiceService(invoice_repository=invoice_repo)

    result = invoice_service.mark_refunded(invoice_id, refund_reference)

    if not result.success:
        if "not found" in result.error.lower():
            return jsonify({'error': result.error}), 404
        return jsonify({'error': result.error}), 400

    return jsonify({
        'invoice': result.invoice.to_dict(),
        'message': 'Invoice refunded'
    }), 200


@admin_invoices_bp.route('/<invoice_id>/pdf', methods=['GET'])
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
        return jsonify({'error': 'Invoice not found'}), 404

    # For now, return invoice data as JSON (PDF generation would be a separate service)
    return jsonify({
        'invoice': invoice.to_dict(),
        'message': 'PDF generation not implemented'
    }), 200
