"""Flask extensions and database setup."""
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from src.config import DATABASE_CONFIG, get_redis_url

# SQLAlchemy instance
db = SQLAlchemy()

# Rate limiter - uses Redis for distributed rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=get_redis_url(),
    strategy="fixed-window",  # or "moving-window" for stricter limiting
)


def create_db_engine():
    """
    Create database engine with appropriate settings.

    SQLite doesn't support pool_size, max_overflow, etc.
    PostgreSQL uses full distributed architecture settings.
    """
    db_url = DATABASE_CONFIG["url"]

    # SQLite doesn't support connection pooling options
    if db_url.startswith("sqlite"):
        return create_engine(db_url, echo=False)

    # PostgreSQL with full distributed architecture support
    return create_engine(
        db_url,
        isolation_level=DATABASE_CONFIG["isolation_level"],
        pool_size=DATABASE_CONFIG["pool_size"],
        max_overflow=DATABASE_CONFIG["max_overflow"],
        pool_pre_ping=DATABASE_CONFIG["pool_pre_ping"],
        pool_recycle=DATABASE_CONFIG["pool_recycle"],
        echo=False,
    )


# Create engine
engine = create_db_engine()

# Session factory for direct usage
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)
