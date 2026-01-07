"""Admin user management routes."""
import bcrypt
from flask import Blueprint, jsonify, request, g, current_app
from src.middleware.auth import require_auth, require_admin
from src.repositories.user_repository import UserRepository
from src.extensions import db
from src.models.user import User
from src.models.user_details import UserDetails
from src.models.enums import UserStatus, UserRole

admin_users_bp = Blueprint('admin_users', __name__, url_prefix='/api/v1/admin/users')


@admin_users_bp.route('/', methods=['POST'])
@require_auth
@require_admin
def create_user():
    """
    Create new user with optional details.

    Body:
        - email: str (required)
        - password: str (required, min 8 chars)
        - status: str (optional, default 'active')
        - role: str (optional, default 'user')
        - details: object (optional)

    Returns:
        201: Created user
        400: Validation error
        409: Email already exists
    """
    data = request.get_json() or {}

    # Validate required fields
    if not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    if not data.get('password'):
        return jsonify({'error': 'Password is required'}), 400
    if len(data.get('password', '')) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    user_repo = UserRepository(db.session)

    # Check if email already exists
    existing = user_repo.find_by_email(data['email'])
    if existing:
        return jsonify({'error': 'User with this email already exists'}), 409

    # Hash password
    password_bytes = data['password'].encode('utf-8')
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

    # Parse status
    status_str = data.get('status', 'active')
    try:
        status = UserStatus(status_str)
    except ValueError:
        return jsonify({'error': f"Invalid status: {status_str}"}), 400

    # Parse role
    role_str = data.get('role', 'user')
    try:
        role = UserRole(role_str)
    except ValueError:
        return jsonify({'error': f"Invalid role: {role_str}"}), 400

    # Create user
    user = User()
    user.email = data['email']
    user.password_hash = password_hash
    user.status = status
    user.role = role

    created_user = user_repo.save(user)

    # Create user details if provided
    details_data = data.get('details')
    if details_data:
        user_details = UserDetails()
        user_details.user_id = created_user.id
        user_details.first_name = details_data.get('first_name')
        user_details.last_name = details_data.get('last_name')
        user_details.address_line_1 = details_data.get('address_line_1')
        user_details.address_line_2 = details_data.get('address_line_2')
        user_details.city = details_data.get('city')
        user_details.postal_code = details_data.get('postal_code')
        user_details.country = details_data.get('country')
        user_details.phone = details_data.get('phone')
        db.session.add(user_details)
        db.session.commit()
        created_user.details = user_details

    # Dispatch user:created event
    try:
        dispatcher = current_app.container.event_dispatcher()
        dispatcher.emit('user:created', {
            'user_id': str(created_user.id),
            'email': created_user.email,
            'role': created_user.role.value,
        })
    except Exception:
        pass  # Don't fail if event dispatcher not configured

    # Build response
    response = {
        'id': str(created_user.id),
        'email': created_user.email,
        'status': created_user.status.value,
        'role': created_user.role.value,
        'created_at': created_user.created_at.isoformat() if created_user.created_at else None,
    }
    if created_user.details:
        response['details'] = created_user.details.to_dict()

    return jsonify(response), 201


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
        - status: str (optional, 'active', 'suspended', etc.)
        - is_active: bool (optional, alternative to status)
        - role: str (optional)
        - name: str (optional, full name to split into first/last)

    Returns:
        200: Updated user
        404: User not found
    """
    user_repo = UserRepository(db.session)
    user = user_repo.find_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}

    # Handle is_active -> status conversion (frontend sends is_active)
    if 'is_active' in data:
        user.status = UserStatus.ACTIVE if data['is_active'] else UserStatus.SUSPENDED

    # Handle legacy status field
    if 'status' in data:
        try:
            user.status = UserStatus(data['status'])
        except ValueError:
            return jsonify({'error': f"Invalid status: {data['status']}"}), 400

    if 'role' in data:
        try:
            user.role = UserRole(data['role'])
        except ValueError:
            return jsonify({'error': f"Invalid role: {data['role']}"}), 400

    # Handle name -> UserDetails (frontend sends combined name)
    if 'name' in data and data['name']:
        parts = data['name'].strip().split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

        if user.details:
            user.details.first_name = first_name
            user.details.last_name = last_name
        else:
            user_details = UserDetails()
            user_details.user_id = user.id
            user_details.first_name = first_name
            user_details.last_name = last_name
            db.session.add(user_details)

    saved_user = user_repo.save(user)

    return jsonify({
        'user': saved_user.to_dict()
    }), 200


@admin_users_bp.route('/<user_id>/roles', methods=['PUT'])
@require_auth
@require_admin
def update_user_roles(user_id):
    """
    Update user roles.

    Args:
        user_id: UUID of the user

    Body:
        - roles: list of strings (required)

    Returns:
        200: Updated user
        400: Validation error
        404: User not found
    """
    user_repo = UserRepository(db.session)
    user = user_repo.find_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or {}
    roles = data.get('roles', [])

    if not roles:
        return jsonify({'error': 'At least one role is required'}), 400

    # For now, use the first role (single-role model)
    # TODO: Implement multi-role support in User model
    try:
        user.role = UserRole(roles[0])
    except ValueError:
        return jsonify({'error': f"Invalid role: {roles[0]}"}), 400

    saved_user = user_repo.save(user)

    return jsonify({
        'user': saved_user.to_dict(),
        'message': 'Roles updated'
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
