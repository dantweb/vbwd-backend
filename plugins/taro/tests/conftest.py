"""Test fixtures for Taro plugin tests."""
import pytest
import os
import sys

# Add src and plugins to path for proper imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

os.environ["FLASK_ENV"] = "testing"
os.environ["TESTING"] = "true"


@pytest.fixture
def app():
    """Create application for testing."""
    from src.app import create_app
    from src.config import get_database_url

    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": get_database_url(),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "RATELIMIT_ENABLED": True,
        "RATELIMIT_STORAGE_URL": "memory://",
    }

    app = create_app(test_config)

    from src.extensions import limiter
    limiter.reset()

    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Provide database for testing."""
    from src.extensions import db

    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()
