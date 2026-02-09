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

    return jsonify({"bundles": [bundle.to_dict() for bundle in bundles]}), 200


@token_bundles_bp.route("/<bundle_id>", methods=["GET"])
def get_token_bundle(bundle_id):
    """
    Get token bundle details by ID (public catalog endpoint).

    Args:
        bundle_id: UUID of the token bundle

    Returns:
        200: Token bundle details
        404: Token bundle not found
    """
    try:
        bundle_repo = TokenBundleRepository(db.session)
        bundle = bundle_repo.find_by_id(bundle_id)
    except Exception:
        return jsonify({"error": "Token bundle not found"}), 404

    if not bundle:
        return jsonify({"error": "Token bundle not found"}), 404

    return jsonify({"bundle": bundle.to_dict()}), 200
