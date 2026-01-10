"""Startup environment validation utilities."""
import os
import sys
import logging
from typing import List

logger = logging.getLogger(__name__)

# Required in all environments
REQUIRED_ENV_VARS = [
    "DATABASE_URL",
    "REDIS_URL",
]

# Required only in production
REQUIRED_IN_PRODUCTION = [
    "FLASK_SECRET_KEY",
    "JWT_SECRET_KEY",
]

# Insecure default values that must not be used in production
INSECURE_DEFAULTS = [
    "dev-secret-key",
    "dev-secret-key-change-in-production",
    "dev-jwt-secret-change-in-production",
    "change-me-in-production",
]


def get_missing_vars() -> List[str]:
    """
    Get list of missing required environment variables.

    Returns:
        List of missing variable names.
    """
    missing = []

    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            missing.append(var)

    return missing


def validate_environment() -> bool:
    """
    Validate required environment variables are set.

    In production mode:
    - Exits with code 1 if required secrets are missing
    - Exits with code 1 if insecure default values are used

    In development mode:
    - Logs warnings for missing variables but continues

    Returns:
        True if all required variables are present and valid.
    """
    is_production = os.environ.get("FLASK_ENV") == "production"
    missing = get_missing_vars()
    security_issues = []

    # Check production-specific requirements
    if is_production:
        for var in REQUIRED_IN_PRODUCTION:
            value = os.environ.get(var)
            if not value:
                missing.append(var)
            elif any(insecure in value.lower() for insecure in INSECURE_DEFAULTS):
                security_issues.append(f"{var} (using insecure default)")

    # Handle missing variables
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        if is_production:
            logger.critical(
                "Cannot start in production with missing required variables"
            )
            sys.exit(1)
        else:
            logger.warning("Continuing in development mode with missing variables")

    # Handle security issues
    if security_issues:
        logger.error(f"Security issues detected: {security_issues}")
        if is_production:
            logger.critical("Cannot start in production with insecure configuration")
            sys.exit(1)

    # Return True if all basic required vars are present
    return len(get_missing_vars()) == 0
