"""Admin user management routes."""
from flask import Blueprint, jsonify, request, g
from src.middleware.auth import require_auth, require_admin
from src.repositories.user_repository import UserRepository
from src.extensions import db
from src.models.enums import UserStatus

admin_users_bp = Blueprint('admin_users', __name__, url_prefix='/api/v1/admin/users')


@admin_users_bp.route('/', methods=['GET'])
@require_auth
@require_admin
def list_users():
    """
    List all users with pagination and filters.

    Query params:
        - limit: int (default 20, max 100)
        - offset: int (default 0)
        - status: str (active, pending, suspended, deleted)
        - search: str (email search)

    Returns:
        200: List of users with pagination info
        401: Unauthorized
        403: Forbidden (non-admin)
    """
    limit = min(int(request.args.get('limit', 20)), 100)
    offset = int(request.args.get('offset', 0))
    status = request.args.get('status')
    search = request.args.get('search')

    user_repo = UserRepository(db.session)

    users, total = user_repo.find_all_paginated(
        limit=limit,
        offset=offset,
        status=status,
        search=search
    )

    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': total,
        'limit': limit,
        'offset': offset
    }), 200


@admin_users_bp.route('/<user_id>', methods=['GET'])
@require_auth
@require_admin
def get_user(user_id):
    """
    Get user detail.

    Args:
        user_id: UUID of the user

    Returns:
        200: User details
        404: User not found
    """
    user_repo = UserRepository(db.session)
    user = user_repo.find_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'user': user.to_dict()
    }), 200


@admin_users_bp.route('/<user_id>', methods=['PUT'])
@require_auth
@require_admin
def update_user(user_id):
    """
    Update user details.

    Args:
        user_id: UUID of the user

    Body:
        - status: str (optional)
        - role: str (optional)

    Returns:
        200: Updated user
        404: User not found
    """
    user_repo = UserRepository(db.session)
    user = user_repo.find_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}

    if 'status' in data:
        try:
            user.status = UserStatus(data['status'])
        except ValueError:
            return jsonify({'error': f"Invalid status: {data['status']}"}), 400

    if 'role' in data:
        from src.models.enums import UserRole
        try:
            user.role = UserRole(data['role'])
        except ValueError:
            return jsonify({'error': f"Invalid role: {data['role']}"}), 400

    saved_user = user_repo.save(user)

    return jsonify({
        'user': saved_user.to_dict()
    }), 200


@admin_users_bp.route('/<user_id>/suspend', methods=['POST'])
@require_auth
@require_admin
def suspend_user(user_id):
    """
    Suspend a user.

    Args:
        user_id: UUID of the user

    Returns:
        200: User suspended
        404: User not found
    """
    user_repo = UserRepository(db.session)
    user = user_repo.find_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.status = UserStatus.SUSPENDED
    saved_user = user_repo.save(user)

    return jsonify({
        'user': saved_user.to_dict(),
        'message': 'User suspended successfully'
    }), 200


@admin_users_bp.route('/<user_id>/activate', methods=['POST'])
@require_auth
@require_admin
def activate_user(user_id):
    """
    Activate a suspended user.

    Args:
        user_id: UUID of the user

    Returns:
        200: User activated
        404: User not found
    """
    user_repo = UserRepository(db.session)
    user = user_repo.find_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.status = UserStatus.ACTIVE
    saved_user = user_repo.save(user)

    return jsonify({
        'user': saved_user.to_dict(),
        'message': 'User activated successfully'
    }), 200
