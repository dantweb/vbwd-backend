"""Authentication routes."""
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from src.schemas.auth_schemas import (
    RegisterRequestSchema,
    LoginRequestSchema,
    AuthResponseSchema
)
from src.services.auth_service import AuthService
from src.repositories.user_repository import UserRepository
from src.extensions import db

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Initialize schemas
register_schema = RegisterRequestSchema()
login_schema = LoginRequestSchema()
auth_response_schema = AuthResponseSchema()


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user.

    ---
    Request body:
        {
            "email": "user@example.com",
            "password": "SecurePassword123!"
        }

    Returns:
        200: {
            "success": true,
            "token": "jwt_token_here",
            "user_id": "uuid-here"
        }
        400: {
            "success": false,
            "error": "Error message"
        }
    """
    try:
        # Validate request data
        data = register_schema.load(request.json)
    except ValidationError as err:
        return jsonify({
            'success': False,
            'error': str(err.messages)
        }), 400

    # Initialize service
    user_repo = UserRepository(db.session)
    auth_service = AuthService(user_repository=user_repo)

    # Register user
    result = auth_service.register(
        email=data['email'],
        password=data['password']
    )

    # Return response
    if result.success:
        return jsonify(auth_response_schema.dump(result)), 200
    else:
        return jsonify(auth_response_schema.dump(result)), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user.

    ---
    Request body:
        {
            "email": "user@example.com",
            "password": "SecurePassword123!"
        }

    Returns:
        200: {
            "success": true,
            "token": "jwt_token_here",
            "user_id": "uuid-here"
        }
        400: {
            "success": false,
            "error": "Error message"
        }
    """
    try:
        # Validate request data
        data = login_schema.load(request.json)
    except ValidationError as err:
        return jsonify({
            'success': False,
            'error': str(err.messages)
        }), 400

    # Initialize service
    user_repo = UserRepository(db.session)
    auth_service = AuthService(user_repository=user_repo)

    # Login user
    result = auth_service.login(
        email=data['email'],
        password=data['password']
    )

    # Return response
    if result.success:
        return jsonify(auth_response_schema.dump(result)), 200
    else:
        return jsonify(auth_response_schema.dump(result)), 401
