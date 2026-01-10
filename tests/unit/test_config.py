"""Tests for application configuration."""
import os
import pytest
from unittest.mock import patch


class TestProductionConfig:
    """Tests for ProductionConfig security validations."""

    def test_production_config_requires_flask_secret_key(self):
        """ProductionConfig raises error if FLASK_SECRET_KEY not set."""
        with patch.dict(
            os.environ,
            {"FLASK_SECRET_KEY": "", "JWT_SECRET_KEY": "valid-jwt-secret"},
            clear=False,
        ):
            # Remove the key entirely
            os.environ.pop("FLASK_SECRET_KEY", None)

            from src.config import ProductionConfig

            with pytest.raises(ValueError, match="FLASK_SECRET_KEY must be set"):
                ProductionConfig()

    def test_production_config_requires_jwt_secret_key(self):
        """ProductionConfig raises error if JWT_SECRET_KEY not set."""
        with patch.dict(
            os.environ,
            {"FLASK_SECRET_KEY": "valid-flask-secret", "JWT_SECRET_KEY": ""},
            clear=False,
        ):
            os.environ.pop("JWT_SECRET_KEY", None)

            from src.config import ProductionConfig

            with pytest.raises(ValueError, match="JWT_SECRET_KEY must be set"):
                ProductionConfig()

    def test_production_config_rejects_default_flask_secret(self):
        """ProductionConfig rejects default dev SECRET_KEY value."""
        with patch.dict(
            os.environ,
            {
                "FLASK_SECRET_KEY": "dev-secret-key-change-in-production",
                "JWT_SECRET_KEY": "valid-jwt-secret",
            },
            clear=False,
        ):
            from src.config import ProductionConfig

            with pytest.raises(ValueError, match="insecure default"):
                ProductionConfig()

    def test_production_config_rejects_default_jwt_secret(self):
        """ProductionConfig rejects JWT_SECRET_KEY matching dev default."""
        with patch.dict(
            os.environ,
            {
                "FLASK_SECRET_KEY": "valid-flask-secret",
                "JWT_SECRET_KEY": "dev-secret-key-change-in-production",
            },
            clear=False,
        ):
            from src.config import ProductionConfig

            with pytest.raises(ValueError, match="insecure default"):
                ProductionConfig()

    def test_production_config_accepts_valid_secrets(self):
        """ProductionConfig accepts properly set secrets."""
        with patch.dict(
            os.environ,
            {
                "FLASK_SECRET_KEY": "a-secure-production-secret-key-here",
                "JWT_SECRET_KEY": "another-secure-jwt-secret-key",
            },
            clear=False,
        ):
            from src.config import ProductionConfig

            config = ProductionConfig()

            assert config.SECRET_KEY == "a-secure-production-secret-key-here"
            assert config.JWT_SECRET_KEY == "another-secure-jwt-secret-key"


class TestConfigConstants:
    """Tests for configuration constants."""

    def test_jwt_expiration_hours_default(self):
        """JWT_EXPIRATION_HOURS has sensible default."""
        from src.config import Config

        # Should have JWT_EXPIRATION_HOURS attribute
        assert hasattr(Config, "JWT_EXPIRATION_HOURS")
        assert Config.JWT_EXPIRATION_HOURS > 0
        assert Config.JWT_EXPIRATION_HOURS <= 168  # Max 1 week

    def test_jwt_expiration_hours_from_env(self):
        """JWT_EXPIRATION_HOURS can be set via environment."""
        with patch.dict(os.environ, {"JWT_EXPIRATION_HOURS": "48"}):
            # Need to reload config to pick up env var
            import importlib
            import src.config

            importlib.reload(src.config)

            assert src.config.Config.JWT_EXPIRATION_HOURS == 48


class TestDevelopmentConfig:
    """Tests for DevelopmentConfig."""

    def test_development_config_allows_defaults(self):
        """DevelopmentConfig allows default secrets for convenience."""
        from src.config import DevelopmentConfig

        config = DevelopmentConfig()

        # Should not raise
        assert config.SECRET_KEY is not None
        assert config.DEBUG is True


class TestTestingConfig:
    """Tests for TestingConfig."""

    def test_testing_config_uses_sqlite(self):
        """TestingConfig uses in-memory SQLite."""
        from src.config import TestingConfig

        config = TestingConfig()

        assert "sqlite" in config.SQLALCHEMY_DATABASE_URI
        assert config.TESTING is True
