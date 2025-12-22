"""User subscription routes."""
from flask import Blueprint, jsonify, g
from src.extensions import db
from src.middleware.auth import require_auth
from src.repositories.subscription_repository import SubscriptionRepository
from src.repositories.tarif_plan_repository import TarifPlanRepository
from src.services.subscription_service import SubscriptionService

subscriptions_bp = Blueprint("subscriptions", __name__)


@subscriptions_bp.route("", methods=["GET"])
@require_auth
def list_subscriptions():
    """
    List user's subscriptions.

    GET /api/v1/user/subscriptions
    Authorization: Bearer <token>

    Returns:
        200: List of all user subscriptions
    """
    # Initialize services
    subscription_repo = SubscriptionRepository(db.session)
    subscription_service = SubscriptionService(subscription_repo=subscription_repo)

    # Get user subscriptions
    subscriptions = subscription_service.get_user_subscriptions(g.user_id)

    return jsonify({
        "subscriptions": [s.to_dict() for s in subscriptions],
    }), 200


@subscriptions_bp.route("/active", methods=["GET"])
@require_auth
def get_active_subscription():
    """
    Get user's active subscription.

    GET /api/v1/user/subscriptions/active
    Authorization: Bearer <token>

    Returns:
        200: Active subscription or None
    """
    # Initialize services
    subscription_repo = SubscriptionRepository(db.session)
    subscription_service = SubscriptionService(subscription_repo=subscription_repo)

    # Get active subscription
    subscription = subscription_service.get_active_subscription(g.user_id)

    if not subscription:
        return jsonify({"subscription": None}), 200

    return jsonify({
        "subscription": subscription.to_dict(),
    }), 200


@subscriptions_bp.route("/<subscription_id>/cancel", methods=["POST"])
@require_auth
def cancel_subscription(subscription_id: str):
    """
    Cancel user's subscription.

    POST /api/v1/user/subscriptions/<uuid>/cancel
    Authorization: Bearer <token>

    Path params:
        subscription_id: Subscription UUID

    Returns:
        200: Cancelled subscription
        404: Subscription not found or not owned by user
    """
    from uuid import UUID

    # Validate UUID format
    try:
        subscription_uuid = UUID(subscription_id)
    except ValueError:
        return jsonify({"error": "Invalid subscription ID format"}), 400

    # Initialize services
    subscription_repo = SubscriptionRepository(db.session)
    subscription_service = SubscriptionService(subscription_repo=subscription_repo)

    # Verify ownership
    subscription = subscription_repo.find_by_id(subscription_uuid)
    if not subscription or subscription.user_id != g.user_id:
        return jsonify({"error": "Subscription not found"}), 404

    # Cancel subscription
    subscription = subscription_service.cancel_subscription(subscription_uuid)

    return jsonify({
        "subscription": subscription.to_dict(),
        "message": "Subscription cancelled. Access continues until expiration.",
    }), 200
