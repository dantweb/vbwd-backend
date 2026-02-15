"""Admin profile routes."""
from flask import Blueprint, jsonify, request, g
from src.middleware.auth import require_auth, require_admin
from src.repositories.user_repository import UserRepository
from src.extensions import db
from src.models.user_details import UserDetails

admin_profile_bp = Blueprint(
    "admin_profile", __name__, url_prefix="/api/v1/admin/profile"
)


@admin_profile_bp.route("", methods=["GET"])
@require_auth
@require_admin
def get_profile():
    """
    Get current admin user's profile.

    Returns:
        200: User profile with details
    """
    user_repo = UserRepository(db.session)
    user = user_repo.find_by_id(g.user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Get user details
    details_dict = user.details.to_dict() if user.details else {}

    return (
        jsonify(
            {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.details.full_name if user.details else "",
                    "role": user.role.value if user.role else "user",
                    "is_active": user.status.value == "ACTIVE" if user.status else True,
                    "details": details_dict,
                }
            }
        ),
        200,
    )


@admin_profile_bp.route("", methods=["PUT"])
@require_auth
@require_admin
def update_profile():
    """
    Update current admin user's profile.

    Body:
        - first_name: str (optional)
        - last_name: str (optional)
        - company: str (optional)
        - tax_number: str (optional)
        - phone: str (optional)
        - address_line_1: str (optional)
        - address_line_2: str (optional)
        - city: str (optional)
        - postal_code: str (optional)
        - country: str (optional)
        - config: dict (optional) - User preferences like language, theme

    Returns:
        200: Updated user profile
        404: User not found
    """
    user_repo = UserRepository(db.session)
    user = user_repo.find_by_id(g.user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}

    # Create user_details if doesn't exist
    if not user.details:
        user_details = UserDetails()
        user_details.user_id = user.id
        db.session.add(user_details)
        db.session.flush()
        user.details = user_details

    # Update allowed fields
    allowed_fields = [
        "first_name",
        "last_name",
        "company",
        "tax_number",
        "phone",
        "address_line_1",
        "address_line_2",
        "city",
        "postal_code",
        "country",
    ]

    for field in allowed_fields:
        if field in data:
            setattr(user.details, field, data[field])

    # Handle config separately (merge with existing)
    if "config" in data and isinstance(data["config"], dict):
        existing_config = user.details.config or {}
        existing_config.update(data["config"])
        user.details.config = existing_config

    db.session.commit()

    # Get updated details
    details_dict = user.details.to_dict() if user.details else {}

    return (
        jsonify(
            {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.details.full_name if user.details else "",
                    "role": user.role.value if user.role else "user",
                    "is_active": user.status.value == "ACTIVE" if user.status else True,
                    "details": details_dict,
                },
                "message": "Profile updated",
            }
        ),
        200,
    )
