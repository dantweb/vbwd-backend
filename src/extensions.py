"""Flask extensions and database setup."""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from src.config import DATABASE_CONFIG

# SQLAlchemy instance
db = SQLAlchemy()

# Create engine with distributed architecture support
engine = create_engine(
    DATABASE_CONFIG["url"],
    isolation_level=DATABASE_CONFIG["isolation_level"],  # READ COMMITTED
    pool_size=DATABASE_CONFIG["pool_size"],  # 20 per instance
    max_overflow=DATABASE_CONFIG["max_overflow"],  # 40 additional
    pool_pre_ping=DATABASE_CONFIG["pool_pre_ping"],  # Health check
    pool_recycle=DATABASE_CONFIG["pool_recycle"],  # 1 hour recycle
    echo=False,  # Set True for SQL logging
)

# Session factory for direct usage
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)
