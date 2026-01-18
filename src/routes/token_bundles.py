"""Public token bundle routes (for user checkout)."""
from flask import Blueprint, jsonify
from src.repositories.token_bundle_repository import TokenBundleRepository
from src.extensions import db

token_bundles_bp = Blueprint(
    "token_bundles", __name__, url_prefix="/api/v1/token-bundles"
)


@token_bundles_bp.route("/", methods=["GET"])
def list_active_bundles():
    """
    List all active token bundles (public endpoint).

    This endpoint is used for the user checkout flow to display
    available token bundles that can be added to the order.

    Returns:
        200: List of active token bundles
    """
    bundle_repo = TokenBundleRepository(db.session)
    bundles = bundle_repo.find_active()

    return jsonify({
        "bundles": [bundle.to_dict() for bundle in bundles]
    }), 200
