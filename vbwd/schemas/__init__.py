"""Marshmallow schemas for request/response validation."""
from vbwd.schemas.auth_schemas import (
    RegisterRequestSchema,
    LoginRequestSchema,
    AuthResponseSchema,
)
from vbwd.schemas.user_schemas import (
    UserSchema,
    UserDetailsSchema,
    UserDetailsUpdateSchema,
    UserProfileSchema,
)

__all__ = [
    "RegisterRequestSchema",
    "LoginRequestSchema",
    "AuthResponseSchema",
    "UserSchema",
    "UserDetailsSchema",
    "UserDetailsUpdateSchema",
    "UserProfileSchema",
]
