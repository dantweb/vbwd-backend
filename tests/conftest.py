"""Pytest configuration and fixtures."""
import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Set test environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'true'


@pytest.fixture
def app():
    """Create application for testing."""
    from src.app import create_app
    from src.config import get_database_url

    # Test configuration with database URI
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": get_database_url(),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "RATELIMIT_ENABLED": True,
        "RATELIMIT_STORAGE_URL": "memory://",  # Use in-memory storage for tests
    }

    app = create_app(test_config)

    # Reset rate limiter state between tests
    from src.extensions import limiter
    limiter.reset()

    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


# Database fixtures (Sprint 1)
# @pytest.fixture
# def db_session(app):
#     """Database session for tests."""
#     from src.extensions import db
#     with app.app_context():
#         db.create_all()
#         yield db.session
#         db.session.rollback()
#         db.drop_all()
