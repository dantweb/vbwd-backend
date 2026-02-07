"""Public add-on routes (for user checkout)."""
from flask import Blueprint, jsonify
from src.repositories.addon_repository import AddOnRepository
from src.extensions import db

addons_bp = Blueprint("addons", __name__, url_prefix="/api/v1/addons")


@addons_bp.route("/", methods=["GET"])
def list_active_addons():
    """
    List all active add-ons (public endpoint).

    This endpoint is used for the user checkout flow to display
    available add-ons that can be added to the order.

    Returns:
        200: List of active add-ons
    """
    addon_repo = AddOnRepository(db.session)
    addons = addon_repo.find_active()

    return jsonify({"addons": [addon.to_dict() for addon in addons]}), 200
