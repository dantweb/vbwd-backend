"""Authentication middleware."""
from functools import wraps
from flask import request, jsonify, g
from src.services.auth_service import AuthService
from src.repositories.user_repository import UserRepository
from src.extensions import db
from src.models.enums import UserRole


def require_auth(f):
    """Decorator to require authentication for a route.

    Validates JWT token from Authorization header and loads user into g.user_id.

    Usage:
        @auth_bp.route('/protected')
        @require_auth
        def protected_route():
            user_id = g.user_id
            ...

    Returns:
        401: If token is missing or invalid
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header is required"}), 401

        # Extract token (format: "Bearer <token>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header format"}), 401

        token = parts[1]

        # Verify token
        user_repo = UserRepository(db.session)
        auth_service = AuthService(user_repository=user_repo)

        user_id = auth_service.verify_token(token)
        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Verify user exists and is active
        user = user_repo.find_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 401

        if user.status.value != "active":
            return jsonify({"error": "User account is not active"}), 401

        # Store user_id in Flask's g object for use in route
        g.user_id = user_id
        g.user = user

        return f(*args, **kwargs)

    return decorated_function


def require_admin(f):
    """Decorator to require admin role for a route.

    Must be used with @require_auth decorator.

    Usage:
        @admin_bp.route('/admin-only')
        @require_auth
        @require_admin
        def admin_route():
            ...

    Returns:
        403: If user is not an admin
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user was loaded by @require_auth
        if not hasattr(g, "user"):
            return jsonify({"error": "Authentication required"}), 401

        # Check if user is admin
        if g.user.role != UserRole.ADMIN:
            return jsonify({"error": "Admin access required"}), 403

        return f(*args, **kwargs)

    return decorated_function


def optional_auth(f):
    """Decorator to optionally authenticate a route.

    If token is provided and valid, loads user into g.user_id.
    If token is missing or invalid, continues without authentication.

    Usage:
        @api_bp.route('/public-or-private')
        @optional_auth
        def flexible_route():
            if hasattr(g, 'user_id'):
                # User is authenticated
                ...
            else:
                # User is not authenticated
                ...

    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # No token, continue without auth
            return f(*args, **kwargs)

        # Extract token (format: "Bearer <token>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            # Invalid format, continue without auth
            return f(*args, **kwargs)

        token = parts[1]

        # Verify token
        user_repo = UserRepository(db.session)
        auth_service = AuthService(user_repository=user_repo)

        user_id = auth_service.verify_token(token)
        if user_id:
            # Valid token, load user
            user = user_repo.find_by_id(user_id)
            if user and user.status.value == "active":
                g.user_id = user_id
                g.user = user

        # Continue with or without auth
        return f(*args, **kwargs)

    return decorated_function
