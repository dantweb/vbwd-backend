"""Integration test configuration and fixtures."""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session", autouse=True)
def seed_test_data_before_integration_tests():
    """
    Seed test data before integration tests run.

    This fixture runs once per test session and ensures that test users
    exist in the database with correct enum values.
    """
    # Only seed if TEST_DATA_SEED is not explicitly disabled
    if os.getenv("TEST_DATA_SEED", "true").lower() == "false":
        return

    # Get database URL from environment
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://vbwd:vbwd@localhost:5432/vbwd"
    )

    try:
        # Create database connection
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(bind=engine)
        db_session = SessionLocal()

        # Import seeder
        from src.testing.test_data_seeder import TestDataSeeder

        # Seed test data
        seeder = TestDataSeeder(db_session)
        seeded = seeder.seed()

        if seeded:
            print("\n✓ Test data seeded successfully")

        db_session.close()
    except Exception as e:
        print(f"\n⚠ Warning: Could not seed test data: {e}")
        # Don't fail tests if seeding fails, they'll just skip if test users don't exist
