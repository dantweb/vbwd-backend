"""User management routes."""
from flask import Blueprint, request, jsonify, g
from marshmallow import ValidationError
from src.middleware.auth import require_auth
from src.schemas.user_schemas import (
    UserSchema,
    UserDetailsSchema,
    UserDetailsUpdateSchema,
    UserProfileSchema,
)
from src.services.user_service import UserService
from src.services.auth_service import AuthService
from src.repositories.user_repository import UserRepository
from src.repositories.user_details_repository import UserDetailsRepository
from src.extensions import db

# Create blueprint
user_bp = Blueprint("user", __name__, url_prefix="/api/v1/user")

# Initialize schemas
user_schema = UserSchema()
user_details_schema = UserDetailsSchema()
user_details_update_schema = UserDetailsUpdateSchema()
user_profile_schema = UserProfileSchema()


@user_bp.route("/profile", methods=["GET"])
@require_auth
def get_profile():
    """Get current user's profile (user + details).

    Requires: Bearer token in Authorization header

    Returns:
        200: {
            "user": {
                "id": "uuid-here",
                "email": "user@example.com",
                "status": "active",
                "role": "user",
                ...
            },
            "details": {
                "id": "uuid-here",
                "user_id": "uuid-here",
                "first_name": "John",
                "last_name": "Doe",
                ...
            }
        }
        404: If user not found
    """
    user_id = g.user_id

    # Initialize services
    user_repo = UserRepository(db.session)
    user_details_repo = UserDetailsRepository(db.session)
    user_service = UserService(
        user_repository=user_repo, user_details_repository=user_details_repo
    )

    # Get user and details
    user = user_service.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    details = user_service.get_user_details(user_id)

    # Return profile
    return jsonify(user_profile_schema.dump({"user": user, "details": details})), 200


@user_bp.route("/details", methods=["GET"])
@require_auth
def get_details():
    """Get current user's details.

    Requires: Bearer token in Authorization header

    Returns:
        200: UserDetails object
        404: If details not found
    """
    user_id = g.user_id

    # Initialize services
    user_repo = UserRepository(db.session)
    user_details_repo = UserDetailsRepository(db.session)
    user_service = UserService(
        user_repository=user_repo, user_details_repository=user_details_repo
    )

    # Get details
    details = user_service.get_user_details(user_id)
    if not details:
        return jsonify({"error": "User details not found"}), 404

    return jsonify(user_details_schema.dump(details)), 200


@user_bp.route("/details", methods=["PUT"])
@require_auth
def update_details():
    """Update current user's details.

    Requires: Bearer token in Authorization header

    Request body:
        {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "address_line_1": "123 Main St",
            "address_line_2": "Apt 4B",
            "city": "New York",
            "postal_code": "10001",
            "country": "US"
        }

    Returns:
        200: Updated UserDetails object
        400: If validation fails
    """
    user_id = g.user_id

    try:
        # Validate request data
        data = user_details_update_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    # Initialize services
    user_repo = UserRepository(db.session)
    user_details_repo = UserDetailsRepository(db.session)
    user_service = UserService(
        user_repository=user_repo, user_details_repository=user_details_repo
    )

    # Update details
    details = user_service.update_user_details(user_id, data)

    return jsonify(user_details_schema.dump(details)), 200


@user_bp.route("/change-password", methods=["POST"])
@require_auth
def change_password():
    """Change current user's password.

    Requires: Bearer token in Authorization header

    Request body:
        {
            "currentPassword": "OldPassword123!",
            "newPassword": "NewPassword123!"
        }

    Returns:
        200: {"success": true}
        400: If validation fails or current password is wrong
    """
    user_id = g.user_id
    data = request.get_json() or {}

    current_password = data.get("currentPassword")
    new_password = data.get("newPassword")

    if not current_password or not new_password:
        return jsonify({"error": "Current password and new password are required"}), 400

    # Initialize services
    user_repo = UserRepository(db.session)
    auth_service = AuthService(user_repository=user_repo)

    # Get user
    user = user_repo.find_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Verify current password
    if not auth_service.verify_password(current_password, user.password_hash):
        return jsonify({"error": "Current password is incorrect"}), 400

    # Update password
    user.password_hash = auth_service.hash_password(new_password)
    user_repo.save(user)

    return jsonify({"success": True}), 200
