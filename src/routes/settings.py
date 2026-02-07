"""Public settings routes."""
from flask import Blueprint, jsonify, request
from src.repositories.payment_method_repository import PaymentMethodRepository
from src.repositories.country_repository import CountryRepository
from src.extensions import db

settings_bp = Blueprint("settings", __name__, url_prefix="/api/v1/settings")


@settings_bp.route("/payment-methods", methods=["GET"])
def get_payment_methods():
    """
    Get available payment methods for checkout.

    This is a public endpoint (no auth required) that returns only active
    payment methods without sensitive configuration data.

    Query params:
        - locale: str (optional) - Locale for translations (e.g., 'de', 'en')
        - currency: str (optional) - Filter by currency
        - country: str (optional) - Filter by country

    Returns:
        200: { "methods": [...] }
    """
    repo = PaymentMethodRepository(db.session)

    # Get optional filters
    locale = request.args.get("locale")
    currency = request.args.get("currency")
    country = request.args.get("country")

    # Get available methods (already filtered by is_active)
    if currency or country:
        methods = repo.find_available(
            currency_code=currency,
            country_code=country,
        )
    else:
        methods = repo.find_active()

    # Convert to public dict (excludes sensitive config, applies translation)
    return jsonify({"methods": [m.to_public_dict(locale=locale) for m in methods]}), 200


@settings_bp.route("/payment-methods/<code>", methods=["GET"])
def get_payment_method_by_code(code):
    """
    Get a specific payment method by code.

    Query params:
        - locale: str (optional) - Locale for translations

    Returns:
        200: { "method": {...} }
        404: Not found
    """
    repo = PaymentMethodRepository(db.session)
    method = repo.find_by_code(code)

    if not method or not method.is_active:
        return jsonify({"error": "Payment method not found"}), 404

    locale = request.args.get("locale")

    return jsonify({"method": method.to_public_dict(locale=locale)}), 200


@settings_bp.route("/terms", methods=["GET"])
def get_terms():
    """
    Get terms and conditions.

    Returns:
        200: { "title": "...", "content": "..." }
    """
    terms_content = """
## Terms and Conditions

### 1. Acceptance of Terms
By accessing and using this service, you accept and agree to be bound by these Terms and Conditions.

### 2. Subscription Services
- Subscriptions are billed according to the selected billing period
- You may cancel your subscription at any time
- Refunds are handled according to our refund policy

### 3. Payment
- Payment is due upon checkout completion
- We accept the payment methods listed during checkout
- All prices include applicable taxes unless stated otherwise

### 4. Privacy
Your use of our services is also governed by our Privacy Policy.

### 5. Limitation of Liability
Our liability is limited to the amount paid for the service.

### 6. Changes to Terms
We reserve the right to modify these terms at any time.

Last updated: 2026-01-01
"""

    return (
        jsonify({"title": "Terms and Conditions", "content": terms_content.strip()}),
        200,
    )


@settings_bp.route("/countries", methods=["GET"])
def get_countries():
    """
    Get available countries for billing address selection.

    This is a public endpoint (no auth required) that returns only enabled
    countries ordered by position.

    Returns:
        200: { "countries": [{"code": "DE", "name": "Germany"}, ...] }
    """
    repo = CountryRepository(db.session)
    countries = repo.find_enabled()

    return jsonify({"countries": [c.to_public_dict() for c in countries]}), 200
