"""Admin tariff plan management routes."""
from flask import Blueprint, jsonify, request
from decimal import Decimal
from src.middleware.auth import require_auth, require_admin
from src.repositories.tarif_plan_repository import TarifPlanRepository
from src.repositories.subscription_repository import SubscriptionRepository
from src.extensions import db
from src.models import TarifPlan

admin_plans_bp = Blueprint('admin_plans', __name__, url_prefix='/api/v1/admin/tarif-plans')


@admin_plans_bp.route('/', methods=['GET'])
@require_auth
@require_admin
def list_plans():
    """
    List all tariff plans including inactive ones.

    Query params:
        - include_inactive: bool (default true for admin)

    Returns:
        200: List of all plans
    """
    plan_repo = TarifPlanRepository(db.session)

    # Admin sees all plans, including inactive
    plans = plan_repo.find_all()

    return jsonify({
        'plans': [plan.to_dict() for plan in plans]
    }), 200


@admin_plans_bp.route('/', methods=['POST'])
@require_auth
@require_admin
def create_plan():
    """
    Create a new tariff plan.

    Body:
        - name: str (required)
        - description: str (optional)
        - price: decimal (required)
        - currency: str (default: EUR)
        - billing_period: str (monthly, yearly)
        - features: dict (optional)
        - is_active: bool (default: true)

    Returns:
        201: Created plan
        400: Validation error
    """
    data = request.get_json() or {}

    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    if 'price' not in data:
        return jsonify({'error': 'Price is required'}), 400

    try:
        plan = TarifPlan(
            name=data['name'],
            description=data.get('description', ''),
            price=Decimal(str(data['price'])),
            currency=data.get('currency', 'EUR'),
            billing_period=data.get('billing_period', 'monthly'),
            features=data.get('features', {}),
            is_active=data.get('is_active', True)
        )

        plan_repo = TarifPlanRepository(db.session)
        saved_plan = plan_repo.save(plan)

        return jsonify({
            'plan': saved_plan.to_dict(),
            'message': 'Plan created successfully'
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@admin_plans_bp.route('/<plan_id>', methods=['GET'])
@require_auth
@require_admin
def get_plan(plan_id):
    """
    Get plan detail.

    Args:
        plan_id: UUID of the plan

    Returns:
        200: Plan details
        404: Plan not found
    """
    plan_repo = TarifPlanRepository(db.session)
    plan = plan_repo.find_by_id(plan_id)

    if not plan:
        return jsonify({'error': 'Plan not found'}), 404

    return jsonify({
        'plan': plan.to_dict()
    }), 200


@admin_plans_bp.route('/<plan_id>', methods=['PUT'])
@require_auth
@require_admin
def update_plan(plan_id):
    """
    Update tariff plan details.

    Args:
        plan_id: UUID of the plan

    Body:
        - name: str (optional)
        - description: str (optional)
        - price: decimal (optional)
        - currency: str (optional)
        - billing_period: str (optional)
        - features: dict (optional)
        - is_active: bool (optional)

    Returns:
        200: Updated plan
        404: Plan not found
    """
    plan_repo = TarifPlanRepository(db.session)
    plan = plan_repo.find_by_id(plan_id)

    if not plan:
        return jsonify({'error': 'Plan not found'}), 404

    data = request.get_json() or {}

    if 'name' in data:
        plan.name = data['name']
    if 'description' in data:
        plan.description = data['description']
    if 'price' in data:
        plan.price = Decimal(str(data['price']))
    if 'currency' in data:
        plan.currency = data['currency']
    if 'billing_period' in data:
        plan.billing_period = data['billing_period']
    if 'features' in data:
        plan.features = data['features']
    if 'is_active' in data:
        plan.is_active = data['is_active']

    saved_plan = plan_repo.save(plan)

    return jsonify({
        'plan': saved_plan.to_dict()
    }), 200


@admin_plans_bp.route('/<plan_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_plan(plan_id):
    """
    Delete a tariff plan.

    Args:
        plan_id: UUID of the plan

    Returns:
        200: Plan deleted
        404: Plan not found
        400: Cannot delete plan with active subscriptions
    """
    plan_repo = TarifPlanRepository(db.session)
    sub_repo = SubscriptionRepository(db.session)

    plan = plan_repo.find_by_id(plan_id)
    if not plan:
        return jsonify({'error': 'Plan not found'}), 404

    # Check for active subscriptions
    subs, total = sub_repo.find_all_paginated(plan_id=plan_id, limit=1)
    if total > 0:
        return jsonify({
            'error': 'Cannot delete plan with existing subscriptions. Deactivate instead.'
        }), 400

    plan_repo.delete(plan_id)

    return jsonify({
        'message': 'Plan deleted successfully'
    }), 200


@admin_plans_bp.route('/<plan_id>/deactivate', methods=['POST'])
@require_auth
@require_admin
def deactivate_plan(plan_id):
    """
    Deactivate a tariff plan.

    Args:
        plan_id: UUID of the plan

    Returns:
        200: Plan deactivated
        404: Plan not found
    """
    plan_repo = TarifPlanRepository(db.session)
    plan = plan_repo.find_by_id(plan_id)

    if not plan:
        return jsonify({'error': 'Plan not found'}), 404

    plan.is_active = False
    saved_plan = plan_repo.save(plan)

    return jsonify({
        'plan': saved_plan.to_dict(),
        'message': 'Plan deactivated'
    }), 200


@admin_plans_bp.route('/<plan_id>/activate', methods=['POST'])
@require_auth
@require_admin
def activate_plan(plan_id):
    """
    Activate a tariff plan.

    Args:
        plan_id: UUID of the plan

    Returns:
        200: Plan activated
        404: Plan not found
    """
    plan_repo = TarifPlanRepository(db.session)
    plan = plan_repo.find_by_id(plan_id)

    if not plan:
        return jsonify({'error': 'Plan not found'}), 404

    plan.is_active = True
    saved_plan = plan_repo.save(plan)

    return jsonify({
        'plan': saved_plan.to_dict(),
        'message': 'Plan activated'
    }), 200
