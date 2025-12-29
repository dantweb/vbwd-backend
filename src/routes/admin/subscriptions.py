"""Admin subscription management routes."""
from flask import Blueprint, jsonify, request
from datetime import timedelta
from src.middleware.auth import require_auth, require_admin
from src.repositories.subscription_repository import SubscriptionRepository
from src.services.subscription_service import SubscriptionService
from src.extensions import db
from src.models.enums import SubscriptionStatus

admin_subs_bp = Blueprint('admin_subscriptions', __name__, url_prefix='/api/v1/admin/subscriptions')


@admin_subs_bp.route('/', methods=['GET'])
@require_auth
@require_admin
def list_subscriptions():
    """
    List all subscriptions with pagination and filters.

    Query params:
        - limit: int (default 20, max 100)
        - offset: int (default 0)
        - status: str (active, pending, cancelled, expired)
        - user_id: str (filter by user)
        - plan_id: str (filter by plan)

    Returns:
        200: List of subscriptions with pagination info
    """
    limit = min(int(request.args.get('limit', 20)), 100)
    offset = int(request.args.get('offset', 0))
    status = request.args.get('status')
    user_id = request.args.get('user_id')
    plan_id = request.args.get('plan_id')

    sub_repo = SubscriptionRepository(db.session)

    subscriptions, total = sub_repo.find_all_paginated(
        limit=limit,
        offset=offset,
        status=status,
        user_id=user_id,
        plan_id=plan_id
    )

    return jsonify({
        'subscriptions': [sub.to_dict() for sub in subscriptions],
        'total': total,
        'limit': limit,
        'offset': offset
    }), 200


@admin_subs_bp.route('/<subscription_id>', methods=['GET'])
@require_auth
@require_admin
def get_subscription(subscription_id):
    """
    Get subscription detail.

    Args:
        subscription_id: UUID of the subscription

    Returns:
        200: Subscription details
        404: Subscription not found
    """
    sub_repo = SubscriptionRepository(db.session)
    subscription = sub_repo.find_by_id(subscription_id)

    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404

    return jsonify({
        'subscription': subscription.to_dict()
    }), 200


@admin_subs_bp.route('/<subscription_id>/extend', methods=['POST'])
@require_auth
@require_admin
def extend_subscription(subscription_id):
    """
    Extend subscription expiration.

    Args:
        subscription_id: UUID of the subscription

    Body:
        - days: int (number of days to extend)

    Returns:
        200: Updated subscription
        404: Subscription not found
    """
    sub_repo = SubscriptionRepository(db.session)
    subscription = sub_repo.find_by_id(subscription_id)

    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404

    data = request.get_json() or {}
    days = data.get('days', 30)

    if subscription.expires_at:
        subscription.expires_at = subscription.expires_at + timedelta(days=days)

    saved_sub = sub_repo.save(subscription)

    return jsonify({
        'subscription': saved_sub.to_dict(),
        'message': f'Subscription extended by {days} days'
    }), 200


@admin_subs_bp.route('/<subscription_id>/cancel', methods=['POST'])
@require_auth
@require_admin
def cancel_subscription(subscription_id):
    """
    Cancel a subscription.

    Args:
        subscription_id: UUID of the subscription

    Returns:
        200: Subscription cancelled
        404: Subscription not found
    """
    sub_repo = SubscriptionRepository(db.session)
    sub_service = SubscriptionService(subscription_repository=sub_repo)

    result = sub_service.cancel_subscription(subscription_id)

    if not result.success:
        if "not found" in result.error.lower():
            return jsonify({'error': result.error}), 404
        return jsonify({'error': result.error}), 400

    return jsonify({
        'subscription': result.subscription.to_dict(),
        'message': 'Subscription cancelled'
    }), 200


@admin_subs_bp.route('/<subscription_id>/activate', methods=['POST'])
@require_auth
@require_admin
def activate_subscription(subscription_id):
    """
    Force activate a subscription.

    Args:
        subscription_id: UUID of the subscription

    Returns:
        200: Subscription activated
        404: Subscription not found
    """
    sub_repo = SubscriptionRepository(db.session)
    sub_service = SubscriptionService(subscription_repository=sub_repo)

    result = sub_service.activate_subscription(subscription_id)

    if not result.success:
        if "not found" in result.error.lower():
            return jsonify({'error': result.error}), 404
        return jsonify({'error': result.error}), 400

    return jsonify({
        'subscription': result.subscription.to_dict(),
        'message': 'Subscription activated'
    }), 200


@admin_subs_bp.route('/<subscription_id>/refund', methods=['POST'])
@require_auth
@require_admin
def refund_subscription(subscription_id):
    """
    Process refund for a subscription.

    Args:
        subscription_id: UUID of the subscription

    Body:
        - amount: decimal (optional, defaults to full amount)
        - reason: str (optional)

    Returns:
        200: Refund processed
        404: Subscription not found
    """
    sub_repo = SubscriptionRepository(db.session)
    subscription = sub_repo.find_by_id(subscription_id)

    if not subscription:
        return jsonify({'error': 'Subscription not found'}), 404

    data = request.get_json() or {}
    reason = data.get('reason', 'Admin refund')

    # Cancel the subscription as part of refund
    subscription.status = SubscriptionStatus.CANCELLED
    saved_sub = sub_repo.save(subscription)

    return jsonify({
        'subscription': saved_sub.to_dict(),
        'message': f'Refund processed: {reason}'
    }), 200
