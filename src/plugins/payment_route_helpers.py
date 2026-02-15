"""Shared payment route helpers for all payment provider plugins.

Three helper functions that every payment plugin route calls.
Eliminates the need for each provider to duplicate config_store checks,
invoice validation, and event emission.
"""
import logging
from uuid import UUID
from flask import current_app, jsonify

from src.events.payment_events import PaymentCapturedEvent
from src.models.enums import LineItemType
from src.models.subscription import Subscription
from src.models.addon_subscription import AddOnSubscription
from src.extensions import db

logger = logging.getLogger(__name__)


def check_plugin_enabled(plugin_name: str):
    """Check plugin is enabled via config_store and return its config.

    Every payment route calls this first. Reads from shared JSON config_store
    (multi-worker safe -- no in-memory state).

    Returns:
        (config_dict, None) if plugin is enabled
        (None, (json_response, status_code)) if plugin disabled or unavailable
    """
    config_store = getattr(current_app, "config_store", None)
    if not config_store:
        return None, (jsonify({"error": "Plugin system not available"}), 503)

    entry = config_store.get_by_name(plugin_name)
    if not entry or entry.status != "enabled":
        return None, (jsonify({"error": "Plugin not enabled"}), 404)

    config = config_store.get_config(plugin_name)
    return config, None


def validate_invoice_for_payment(invoice_id_str, user_id):
    """Validate invoice exists, is PENDING, and belongs to user.

    Every payment create-session route calls this after parsing request body.
    Uses DI container from current_app for request-scoped repository.

    Returns:
        (invoice, None) if valid
        (None, (json_response, status_code)) if invalid
    """
    try:
        invoice_uuid = (
            UUID(invoice_id_str) if isinstance(invoice_id_str, str) else invoice_id_str
        )
    except (ValueError, TypeError):
        return None, (jsonify({"error": "Invalid invoice_id format"}), 400)

    container = current_app.container
    invoice_repo = container.invoice_repository()
    invoice = invoice_repo.find_by_id(invoice_uuid)

    if not invoice:
        return None, (jsonify({"error": "Invoice not found"}), 404)
    if invoice.status.value != "PENDING":
        return None, (
            jsonify({"error": f"Invoice is {invoice.status.value}, expected PENDING"}),
            400,
        )
    if str(invoice.user_id) != str(user_id):
        return None, (jsonify({"error": "Invoice does not belong to this user"}), 403)

    return invoice, None


def emit_payment_captured(
    invoice_id, payment_reference, amount, currency, provider, transaction_id=""
):
    """Emit PaymentCapturedEvent -- the ONLY action a webhook handler should take.

    Event-driven: the webhook route emits this event and returns 200.
    PaymentCapturedHandler handles all activation (invoice->PAID, subscription->ACTIVE, etc.)
    The payment plugin NEVER acts directly on domain objects.

    Returns:
        EventResult from the handler chain
    """
    logger.info(
        "emit_payment_captured: invoice=%s provider=%s ref=%s amount=%s",
        invoice_id,
        provider,
        payment_reference,
        amount,
    )
    event = PaymentCapturedEvent(
        invoice_id=invoice_id,
        payment_reference=payment_reference,
        amount=amount,
        currency=currency,
        provider=provider,
        transaction_id=transaction_id,
    )
    container = current_app.container
    result = container.event_dispatcher().emit(event)
    if not result.success:
        logger.error("PaymentCapturedEvent handler failed: %s", result.error)
    else:
        logger.info(
            "PaymentCapturedEvent processed successfully for invoice %s", invoice_id
        )
    return result


def determine_session_mode(invoice):
    """Check invoice line items to determine payment mode.

    Returns "subscription" if any line item is recurring, "payment" otherwise.
    Used by all payment provider plugins.
    """
    for item in invoice.line_items:
        if item.item_type == LineItemType.SUBSCRIPTION:
            sub = db.session.get(Subscription, item.item_id)
            if sub and sub.tarif_plan and sub.tarif_plan.is_recurring:
                return "subscription"
        elif item.item_type == LineItemType.ADD_ON:
            addon_sub = db.session.get(AddOnSubscription, item.item_id)
            if addon_sub and addon_sub.addon and addon_sub.addon.is_recurring:
                return "subscription"
    return "payment"
