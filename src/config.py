"""Application configuration."""
import os
from typing import Optional


def get_database_url() -> str:
    """Get PostgreSQL connection URL."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://vbwd:vbwd@postgres:5432/vbwd"
    )


def get_redis_url() -> str:
    """Get Redis connection URL."""
    return os.getenv("REDIS_URL", "redis://redis:6379/0")


# Database engine configuration for distributed systems (Sprint 1)
DATABASE_CONFIG = {
    "url": get_database_url(),
    "isolation_level": "READ_COMMITTED",  # PostgreSQL default (explicit)
    "pool_size": 20,  # Per Flask instance
    "max_overflow": 40,  # Additional connections under load
    "pool_pre_ping": True,  # Verify connections before use
    "pool_recycle": 3600,  # Recycle connections after 1 hour
}


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

    # Database
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": DATABASE_CONFIG["pool_size"],
        "max_overflow": DATABASE_CONFIG["max_overflow"],
        "pool_pre_ping": DATABASE_CONFIG["pool_pre_ping"],
        "pool_recycle": DATABASE_CONFIG["pool_recycle"],
    }

    # Redis
    REDIS_URL = get_redis_url()

    # Security
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour

    # Celery
    CELERY_BROKER_URL = get_redis_url()
    CELERY_RESULT_BACKEND = get_redis_url()


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # In-memory for tests

    # Use separate Redis DB for tests
    REDIS_URL = "redis://redis:6379/1"
    CELERY_BROKER_URL = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND = "redis://redis:6379/1"


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False

    def __init__(self):
        """Initialize production config and validate required env vars."""
        super().__init__()

        # In production, these MUST be set via environment variables
        self.SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
        self.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

        if not self.SECRET_KEY:
            raise ValueError("FLASK_SECRET_KEY must be set in production")


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(env: Optional[str] = None) -> Config:
    """
    Get configuration based on environment.

    Args:
        env: Environment name (development, testing, production)

    Returns:
        Configuration class
    """
    if env is None:
        env = os.getenv("FLASK_ENV", "development")

    return config.get(env, config["default"])
