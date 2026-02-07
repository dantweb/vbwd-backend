"""User subscription routes."""
from flask import Blueprint, jsonify, g, request
from uuid import UUID
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

    return (
        jsonify(
            {
                "subscriptions": [s.to_dict() for s in subscriptions],
            }
        ),
        200,
    )


@subscriptions_bp.route("/active", methods=["GET"])
@require_auth
def get_active_subscription():
    """
    Get user's active subscription with plan details.

    GET /api/v1/user/subscriptions/active
    Authorization: Bearer <token>

    Returns:
        200: Active subscription with plan details or None
    """
    # Initialize services
    subscription_repo = SubscriptionRepository(db.session)
    tarif_plan_repo = TarifPlanRepository(db.session)
    subscription_service = SubscriptionService(subscription_repo=subscription_repo)

    # Get active subscription
    subscription = subscription_service.get_active_subscription(g.user_id)

    if not subscription:
        return jsonify({"subscription": None}), 200

    # Build response with plan details
    subscription_data = subscription.to_dict()

    # Add plan details if available
    if subscription.tarif_plan_id:
        plan = tarif_plan_repo.find_by_id(subscription.tarif_plan_id)
        if plan:
            subscription_data["plan"] = {
                "id": str(plan.id),
                "name": plan.name,
                "slug": plan.slug,
                "price": float(plan.price) if plan.price else 0,
                "billing_period": plan.billing_period.value
                if plan.billing_period
                else "monthly",
            }

    # Add pending plan details if available
    if subscription.pending_plan_id:
        pending_plan = tarif_plan_repo.find_by_id(subscription.pending_plan_id)
        if pending_plan:
            subscription_data["pending_plan"] = {
                "id": str(pending_plan.id),
                "name": pending_plan.name,
                "slug": pending_plan.slug,
            }

    return (
        jsonify(
            {
                "subscription": subscription_data,
            }
        ),
        200,
    )


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
    result = subscription_service.cancel_subscription(subscription_uuid)

    if not result.success:
        return jsonify({"error": result.error}), 400

    return (
        jsonify(
            {
                "subscription": result.subscription.to_dict(),
                "message": "Subscription cancelled. Access continues until expiration.",
            }
        ),
        200,
    )


@subscriptions_bp.route("/<subscription_id>/pause", methods=["POST"])
@require_auth
def pause_subscription(subscription_id: str):
    """
    Pause user's subscription.

    POST /api/v1/user/subscriptions/<uuid>/pause
    Authorization: Bearer <token>

    Returns:
        200: Paused subscription
        400: Cannot pause subscription
        404: Subscription not found
    """
    try:
        subscription_uuid = UUID(subscription_id)
    except ValueError:
        return jsonify({"error": "Invalid subscription ID format"}), 400

    subscription_repo = SubscriptionRepository(db.session)
    subscription_service = SubscriptionService(subscription_repo=subscription_repo)

    # Verify ownership
    subscription = subscription_repo.find_by_id(subscription_uuid)
    if not subscription or subscription.user_id != g.user_id:
        return jsonify({"error": "Subscription not found"}), 404

    result = subscription_service.pause_subscription(subscription_uuid)

    if not result.success:
        return jsonify({"error": result.error}), 400

    return (
        jsonify(
            {
                "subscription": result.subscription.to_dict(),
                "message": "Subscription paused.",
            }
        ),
        200,
    )


@subscriptions_bp.route("/<subscription_id>/resume", methods=["POST"])
@require_auth
def resume_subscription(subscription_id: str):
    """
    Resume user's paused subscription.

    POST /api/v1/user/subscriptions/<uuid>/resume
    Authorization: Bearer <token>

    Returns:
        200: Resumed subscription
        400: Cannot resume subscription
        404: Subscription not found
    """
    try:
        subscription_uuid = UUID(subscription_id)
    except ValueError:
        return jsonify({"error": "Invalid subscription ID format"}), 400

    subscription_repo = SubscriptionRepository(db.session)
    subscription_service = SubscriptionService(subscription_repo=subscription_repo)

    # Verify ownership
    subscription = subscription_repo.find_by_id(subscription_uuid)
    if not subscription or subscription.user_id != g.user_id:
        return jsonify({"error": "Subscription not found"}), 404

    result = subscription_service.resume_subscription(subscription_uuid)

    if not result.success:
        return jsonify({"error": result.error}), 400

    return (
        jsonify(
            {
                "subscription": result.subscription.to_dict(),
                "message": "Subscription resumed. Expiration extended by pause duration.",
            }
        ),
        200,
    )


@subscriptions_bp.route("/<subscription_id>/upgrade", methods=["POST"])
@require_auth
def upgrade_subscription(subscription_id: str):
    """
    Upgrade subscription to higher tier plan.

    POST /api/v1/user/subscriptions/<uuid>/upgrade
    Authorization: Bearer <token>
    Body: { "plan_id": "..." }

    Returns:
        200: Upgraded subscription
        400: Cannot upgrade
        404: Subscription not found
    """
    try:
        subscription_uuid = UUID(subscription_id)
    except ValueError:
        return jsonify({"error": "Invalid subscription ID format"}), 400

    data = request.get_json() or {}
    plan_id = data.get("plan_id")

    if not plan_id:
        return jsonify({"error": "plan_id is required"}), 400

    try:
        plan_uuid = UUID(plan_id)
    except ValueError:
        return jsonify({"error": "Invalid plan ID format"}), 400

    subscription_repo = SubscriptionRepository(db.session)
    tarif_plan_repo = TarifPlanRepository(db.session)
    subscription_service = SubscriptionService(
        subscription_repo=subscription_repo, tarif_plan_repo=tarif_plan_repo
    )

    # Verify ownership
    subscription = subscription_repo.find_by_id(subscription_uuid)
    if not subscription or subscription.user_id != g.user_id:
        return jsonify({"error": "Subscription not found"}), 404

    result = subscription_service.upgrade_subscription(subscription_uuid, plan_uuid)

    if not result.success:
        return jsonify({"error": result.error}), 400

    return (
        jsonify(
            {
                "subscription": result.subscription.to_dict(),
                "message": "Subscription upgraded successfully.",
            }
        ),
        200,
    )


@subscriptions_bp.route("/<subscription_id>/downgrade", methods=["POST"])
@require_auth
def downgrade_subscription(subscription_id: str):
    """
    Downgrade subscription to lower tier plan at next renewal.

    POST /api/v1/user/subscriptions/<uuid>/downgrade
    Authorization: Bearer <token>
    Body: { "plan_id": "..." }

    Returns:
        200: Subscription with pending downgrade
        400: Cannot downgrade
        404: Subscription not found
    """
    try:
        subscription_uuid = UUID(subscription_id)
    except ValueError:
        return jsonify({"error": "Invalid subscription ID format"}), 400

    data = request.get_json() or {}
    plan_id = data.get("plan_id")

    if not plan_id:
        return jsonify({"error": "plan_id is required"}), 400

    try:
        plan_uuid = UUID(plan_id)
    except ValueError:
        return jsonify({"error": "Invalid plan ID format"}), 400

    subscription_repo = SubscriptionRepository(db.session)
    tarif_plan_repo = TarifPlanRepository(db.session)
    subscription_service = SubscriptionService(
        subscription_repo=subscription_repo, tarif_plan_repo=tarif_plan_repo
    )

    # Verify ownership
    subscription = subscription_repo.find_by_id(subscription_uuid)
    if not subscription or subscription.user_id != g.user_id:
        return jsonify({"error": "Subscription not found"}), 404

    result = subscription_service.downgrade_subscription(subscription_uuid, plan_uuid)

    if not result.success:
        return jsonify({"error": result.error}), 400

    return (
        jsonify(
            {
                "subscription": result.subscription.to_dict(),
                "message": "Downgrade scheduled for next renewal.",
            }
        ),
        200,
    )


@subscriptions_bp.route("/<subscription_id>/proration", methods=["GET"])
@require_auth
def get_proration(subscription_id: str):
    """
    Get proration calculation for plan change.

    GET /api/v1/user/subscriptions/<uuid>/proration?new_plan_id=...
    Authorization: Bearer <token>

    Returns:
        200: Proration calculation
        400: Invalid request
        404: Subscription not found
    """
    try:
        subscription_uuid = UUID(subscription_id)
    except ValueError:
        return jsonify({"error": "Invalid subscription ID format"}), 400

    new_plan_id = request.args.get("new_plan_id")
    if not new_plan_id:
        return jsonify({"error": "new_plan_id query parameter is required"}), 400

    try:
        new_plan_uuid = UUID(new_plan_id)
    except ValueError:
        return jsonify({"error": "Invalid plan ID format"}), 400

    subscription_repo = SubscriptionRepository(db.session)
    tarif_plan_repo = TarifPlanRepository(db.session)
    subscription_service = SubscriptionService(
        subscription_repo=subscription_repo, tarif_plan_repo=tarif_plan_repo
    )

    # Verify ownership
    subscription = subscription_repo.find_by_id(subscription_uuid)
    if not subscription or subscription.user_id != g.user_id:
        return jsonify({"error": "Subscription not found"}), 404

    proration = subscription_service.calculate_proration(
        subscription_uuid, new_plan_uuid
    )

    if not proration:
        return jsonify({"error": "Unable to calculate proration"}), 400

    return (
        jsonify(
            {
                "proration": {
                    "credit": str(proration.credit),
                    "amount_due": str(proration.amount_due),
                    "days_remaining": proration.days_remaining,
                }
            }
        ),
        200,
    )
