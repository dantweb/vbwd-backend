"""Public add-on routes (for user checkout)."""
from flask import Blueprint, jsonify, g
from src.middleware.auth import optional_auth
from src.repositories.addon_repository import AddOnRepository
from src.extensions import db
from src.models import Subscription
from src.models.enums import SubscriptionStatus

addons_bp = Blueprint("addons", __name__, url_prefix="/api/v1/addons")


@addons_bp.route("/", methods=["GET"])
@optional_auth
def list_active_addons():
    """
    List active add-ons available to the current user.

    - Authenticated user with active subscription:
        → independent add-ons + add-ons bound to user's plan
    - Authenticated user without subscription / unauthenticated:
        → independent add-ons only

    Returns:
        200: List of available add-ons
    """
    addon_repo = AddOnRepository(db.session)

    plan_id = None
    if hasattr(g, "user_id"):
        # Find user's active subscription to get their plan
        subscription = (
            db.session.query(Subscription)
            .filter(
                Subscription.user_id == g.user_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
            .first()
        )
        if subscription:
            plan_id = subscription.tarif_plan_id

    addons = addon_repo.find_available_for_plan(plan_id)

    return jsonify({"addons": [addon.to_dict() for addon in addons]}), 200
