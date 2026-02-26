"""Tests for startup environment validation."""
import os
import pytest


class TestValidateEnvironment:
    """Tests for validate_environment function."""

    @pytest.fixture(autouse=True)
    def reset_env(self):
        """Reset environment before each test."""
        # Store original env
        original = os.environ.copy()
        yield
        # Restore original env
        os.environ.clear()
        os.environ.update(original)

    def test_validates_required_vars_present(self):
        """Returns True when all required vars are present."""
        from src.utils.startup_check import validate_environment

        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["FLASK_ENV"] = "development"

        result = validate_environment()

        assert result is True

    def test_returns_false_when_database_url_missing(self):
        """Returns False when DATABASE_URL is missing."""
        from src.utils.startup_check import validate_environment

        os.environ.pop("DATABASE_URL", None)
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["FLASK_ENV"] = "development"

        result = validate_environment()

        assert result is False

    def test_returns_false_when_redis_url_missing(self):
        """Returns False when REDIS_URL is missing."""
        from src.utils.startup_check import validate_environment

        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
        os.environ.pop("REDIS_URL", None)
        os.environ["FLASK_ENV"] = "development"

        result = validate_environment()

        assert result is False

    def test_production_requires_secret_key(self):
        """Production mode requires SECRET_KEY."""
        from src.utils.startup_check import validate_environment

        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["FLASK_ENV"] = "production"
        os.environ.pop("FLASK_SECRET_KEY", None)
        os.environ["JWT_SECRET_KEY"] = "real-secret-key-for-jwt"

        with pytest.raises(SystemExit):
            validate_environment()

    def test_production_requires_jwt_secret_key(self):
        """Production mode requires JWT_SECRET_KEY."""
        from src.utils.startup_check import validate_environment

        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["FLASK_ENV"] = "production"
        os.environ["FLASK_SECRET_KEY"] = "real-secret-key-for-flask"
        os.environ.pop("JWT_SECRET_KEY", None)

        with pytest.raises(SystemExit):
            validate_environment()

    def test_production_rejects_default_secret_key(self):
        """Production mode rejects insecure default SECRET_KEY."""
        from src.utils.startup_check import validate_environment

        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["FLASK_ENV"] = "production"
        os.environ["FLASK_SECRET_KEY"] = "dev-secret-key-change-in-production"
        os.environ["JWT_SECRET_KEY"] = "real-secret-key-for-jwt"

        with pytest.raises(SystemExit):
            validate_environment()

    def test_production_rejects_default_jwt_secret(self):
        """Production mode rejects insecure default JWT_SECRET_KEY."""
        from src.utils.startup_check import validate_environment

        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["FLASK_ENV"] = "production"
        os.environ["FLASK_SECRET_KEY"] = "real-secret-key-for-flask"
        os.environ["JWT_SECRET_KEY"] = "dev-jwt-secret-change-in-production"

        with pytest.raises(SystemExit):
            validate_environment()

    def test_production_accepts_secure_secrets(self):
        """Production mode accepts secure secrets."""
        from src.utils.startup_check import validate_environment

        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["FLASK_ENV"] = "production"
        os.environ["FLASK_SECRET_KEY"] = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
        os.environ["JWT_SECRET_KEY"] = "x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6"

        result = validate_environment()

        assert result is True

    def test_development_allows_missing_secrets(self):
        """Development mode continues with missing secrets."""
        from src.utils.startup_check import validate_environment

        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"
        os.environ["FLASK_ENV"] = "development"
        os.environ.pop("FLASK_SECRET_KEY", None)
        os.environ.pop("JWT_SECRET_KEY", None)

        # Should not raise in development
        result = validate_environment()

        assert result is True  # Required vars present


class TestGetMissingVars:
    """Tests for get_missing_vars helper function."""

    @pytest.fixture(autouse=True)
    def reset_env(self):
        """Reset environment before each test."""
        original = os.environ.copy()
        yield
        os.environ.clear()
        os.environ.update(original)

    def test_returns_empty_list_when_all_present(self):
        """Returns empty list when all vars are present."""
        from src.utils.startup_check import get_missing_vars

        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
        os.environ["REDIS_URL"] = "redis://localhost:6379/0"

        result = get_missing_vars()

        assert result == []

    def test_returns_list_of_missing_vars(self):
        """Returns list of missing variable names."""
        from src.utils.startup_check import get_missing_vars

        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test"
        os.environ.pop("REDIS_URL", None)

        result = get_missing_vars()

        assert "REDIS_URL" in result
