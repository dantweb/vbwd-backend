"""Tariff plan routes."""
from flask import Blueprint, request, jsonify
from src.extensions import db
from src.repositories.tarif_plan_repository import TarifPlanRepository
from src.repositories.currency_repository import CurrencyRepository
from src.repositories.tax_repository import TaxRepository
from src.services.tarif_plan_service import TarifPlanService
from src.services.currency_service import CurrencyService
from src.services.tax_service import TaxService

tarif_plans_bp = Blueprint("tarif_plans", __name__)


@tarif_plans_bp.route("", methods=["GET"])
def list_plans():
    """
    List active tariff plans.

    GET /api/v1/tarif-plans?currency=USD&country=DE

    Query params:
        currency: Currency code for pricing (default: EUR)
        country: Country code for tax calculation (optional)

    Returns:
        200: List of plans with pricing in specified currency
    """
    currency_code = request.args.get("currency", "EUR").upper()
    country_code = request.args.get("country", "").upper() or None

    # Initialize services
    plan_repo = TarifPlanRepository(db.session)
    currency_repo = CurrencyRepository(db.session)
    tax_repo = TaxRepository(db.session)

    currency_service = CurrencyService(currency_repo=currency_repo)
    tax_service = TaxService(tax_repo=tax_repo)
    tarif_plan_service = TarifPlanService(
        tarif_plan_repo=plan_repo,
        currency_service=currency_service,
        tax_service=tax_service,
    )

    # Get active plans
    plans = tarif_plan_service.get_active_plans()

    # Add pricing info to each plan
    result = []
    for plan in plans:
        try:
            plan_data = tarif_plan_service.get_plan_with_pricing(
                plan,
                currency_code=currency_code,
                country_code=country_code,
            )
            result.append(plan_data)
        except ValueError as e:
            # Currency not found - use default
            plan_data = {
                "id": str(plan.id),
                "name": plan.name,
                "slug": plan.slug,
                "description": plan.description,
                "price": plan.price_float,
                "billing_period": plan.billing_period.value,
                "is_active": plan.is_active,
                "error": str(e),
            }
            result.append(plan_data)

    return jsonify({
        "plans": result,
        "currency": currency_code,
        "country": country_code,
    }), 200


@tarif_plans_bp.route("/<slug>", methods=["GET"])
def get_plan(slug: str):
    """
    Get single tariff plan by slug.

    GET /api/v1/tarif-plans/pro?currency=USD&country=DE

    Path params:
        slug: Plan URL slug

    Query params:
        currency: Currency code for pricing (default: EUR)
        country: Country code for tax calculation (optional)

    Returns:
        200: Plan details with pricing
        404: Plan not found
    """
    currency_code = request.args.get("currency", "EUR").upper()
    country_code = request.args.get("country", "").upper() or None

    # Initialize services
    plan_repo = TarifPlanRepository(db.session)
    currency_repo = CurrencyRepository(db.session)
    tax_repo = TaxRepository(db.session)

    currency_service = CurrencyService(currency_repo=currency_repo)
    tax_service = TaxService(tax_repo=tax_repo)
    tarif_plan_service = TarifPlanService(
        tarif_plan_repo=plan_repo,
        currency_service=currency_service,
        tax_service=tax_service,
    )

    # Get plan
    plan = tarif_plan_service.get_plan_by_slug(slug)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404

    # Add pricing info
    try:
        plan_data = tarif_plan_service.get_plan_with_pricing(
            plan,
            currency_code=currency_code,
            country_code=country_code,
        )
        return jsonify(plan_data), 200
    except ValueError as e:
        return jsonify({
            "error": str(e),
            "plan": {
                "id": str(plan.id),
                "name": plan.name,
                "slug": plan.slug,
                "price": plan.price_float,
            }
        }), 400
