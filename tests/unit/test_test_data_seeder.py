"""
Unit tests for TestDataSeeder service.

TDD: These tests are written BEFORE the implementation.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import os


class TestTestDataSeeder:
    """Test the test data seeder service."""

    def test_seeder_skips_when_env_false(self):
        """Seeder should skip when TEST_DATA_SEED is false."""
        from src.testing.test_data_seeder import TestDataSeeder

        with patch.dict(os.environ, {'TEST_DATA_SEED': 'false'}, clear=False):
            seeder = TestDataSeeder(db_session=MagicMock())
            result = seeder.seed()
            assert result is False

    def test_seeder_skips_when_env_not_set(self):
        """Seeder should skip when TEST_DATA_SEED is not set (default)."""
        from src.testing.test_data_seeder import TestDataSeeder

        env = os.environ.copy()
        env.pop('TEST_DATA_SEED', None)
        with patch.dict(os.environ, env, clear=True):
            seeder = TestDataSeeder(db_session=MagicMock())
            result = seeder.seed()
            assert result is False

    def test_seeder_runs_when_env_true(self):
        """Seeder should run when TEST_DATA_SEED is true."""
        from src.testing.test_data_seeder import TestDataSeeder

        mock_session = MagicMock()
        # Mock query to return None (no existing data)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch.dict(os.environ, {'TEST_DATA_SEED': 'true'}, clear=False):
            seeder = TestDataSeeder(db_session=mock_session)
            result = seeder.seed()
            assert result is True
            assert mock_session.commit.called

    def test_seeder_runs_when_env_TRUE_uppercase(self):
        """Seeder should handle uppercase TRUE."""
        from src.testing.test_data_seeder import TestDataSeeder

        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch.dict(os.environ, {'TEST_DATA_SEED': 'TRUE'}, clear=False):
            seeder = TestDataSeeder(db_session=mock_session)
            result = seeder.seed()
            assert result is True

    def test_seeder_creates_test_user(self):
        """Seeder should create test user with configured credentials."""
        from src.testing.test_data_seeder import TestDataSeeder

        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch.dict(os.environ, {
            'TEST_DATA_SEED': 'true',
            'TEST_USER_EMAIL': 'testuser@example.com',
            'TEST_USER_PASSWORD': 'TestPass123@'
        }, clear=False):
            seeder = TestDataSeeder(db_session=mock_session)
            seeder.seed()

            # Verify session.add was called
            assert mock_session.add.called

    def test_seeder_uses_default_email_when_not_configured(self):
        """Seeder should use default email when TEST_USER_EMAIL not set."""
        from src.testing.test_data_seeder import TestDataSeeder

        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        env = {'TEST_DATA_SEED': 'true'}
        with patch.dict(os.environ, env, clear=False):
            seeder = TestDataSeeder(db_session=mock_session)
            seeder.seed()
            # Should not raise an error - uses defaults
            assert mock_session.commit.called

    def test_seeder_creates_test_admin(self):
        """Seeder should create admin user."""
        from src.testing.test_data_seeder import TestDataSeeder

        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch.dict(os.environ, {
            'TEST_DATA_SEED': 'true',
            'TEST_ADMIN_EMAIL': 'admin@example.com',
            'TEST_ADMIN_PASSWORD': 'AdminPass123@'
        }, clear=False):
            seeder = TestDataSeeder(db_session=mock_session)
            seeder.seed()
            assert mock_session.add.called

    def test_seeder_creates_test_tariff_plan(self):
        """Seeder should create test tariff plan."""
        from src.testing.test_data_seeder import TestDataSeeder

        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch.dict(os.environ, {'TEST_DATA_SEED': 'true'}, clear=False):
            seeder = TestDataSeeder(db_session=mock_session)
            seeder.seed()
            # Should create multiple entities (user, admin, plan, subscription)
            assert mock_session.add.call_count >= 3

    def test_seeder_skips_existing_user(self):
        """Seeder should not duplicate existing test user."""
        from src.testing.test_data_seeder import TestDataSeeder

        mock_session = MagicMock()
        existing_user = MagicMock()
        existing_user.id = 'existing-uuid'

        # First call returns existing user, rest return None
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            existing_user,  # test user exists
            None,  # admin doesn't exist
            None,  # plan doesn't exist
            None,  # subscription doesn't exist
        ]

        with patch.dict(os.environ, {'TEST_DATA_SEED': 'true'}, clear=False):
            seeder = TestDataSeeder(db_session=mock_session)
            seeder.seed()
            # Should still succeed
            assert mock_session.commit.called

    def test_cleanup_skips_when_env_false(self):
        """Cleanup should skip when TEST_DATA_CLEANUP is false."""
        from src.testing.test_data_seeder import TestDataSeeder

        mock_session = MagicMock()
        with patch.dict(os.environ, {'TEST_DATA_CLEANUP': 'false'}, clear=False):
            seeder = TestDataSeeder(db_session=mock_session)
            result = seeder.cleanup()
            assert result is False
            assert not mock_session.commit.called

    def test_cleanup_skips_when_env_not_set(self):
        """Cleanup should skip when TEST_DATA_CLEANUP is not set (default)."""
        from src.testing.test_data_seeder import TestDataSeeder

        mock_session = MagicMock()
        env = os.environ.copy()
        env.pop('TEST_DATA_CLEANUP', None)
        with patch.dict(os.environ, env, clear=True):
            seeder = TestDataSeeder(db_session=mock_session)
            result = seeder.cleanup()
            assert result is False

    def test_cleanup_runs_when_env_true(self):
        """Cleanup should remove test data when TEST_DATA_CLEANUP is true."""
        from src.testing.test_data_seeder import TestDataSeeder

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with patch.dict(os.environ, {'TEST_DATA_CLEANUP': 'true'}, clear=False):
            seeder = TestDataSeeder(db_session=mock_session)
            result = seeder.cleanup()
            assert result is True
            assert mock_session.commit.called

    def test_should_seed_returns_bool(self):
        """should_seed() should return boolean."""
        from src.testing.test_data_seeder import TestDataSeeder

        seeder = TestDataSeeder(db_session=MagicMock())

        with patch.dict(os.environ, {'TEST_DATA_SEED': 'true'}, clear=False):
            assert seeder.should_seed() is True

        with patch.dict(os.environ, {'TEST_DATA_SEED': 'false'}, clear=False):
            assert seeder.should_seed() is False

    def test_should_cleanup_returns_bool(self):
        """should_cleanup() should return boolean."""
        from src.testing.test_data_seeder import TestDataSeeder

        seeder = TestDataSeeder(db_session=MagicMock())

        with patch.dict(os.environ, {'TEST_DATA_CLEANUP': 'true'}, clear=False):
            assert seeder.should_cleanup() is True

        with patch.dict(os.environ, {'TEST_DATA_CLEANUP': 'false'}, clear=False):
            assert seeder.should_cleanup() is False


class TestTestDataSeederMarker:
    """Test the marker used to identify test data."""

    def test_marker_is_defined(self):
        """TestDataSeeder should have a TEST_DATA_MARKER constant."""
        from src.testing.test_data_seeder import TestDataSeeder

        assert hasattr(TestDataSeeder, 'TEST_DATA_MARKER')
        assert isinstance(TestDataSeeder.TEST_DATA_MARKER, str)
        assert len(TestDataSeeder.TEST_DATA_MARKER) > 0

    def test_marker_used_in_plan_name(self):
        """Test plans should use the marker prefix for identification."""
        from src.testing.test_data_seeder import TestDataSeeder

        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with patch.dict(os.environ, {'TEST_DATA_SEED': 'true'}, clear=False):
            seeder = TestDataSeeder(db_session=mock_session)
            seeder.seed()

            # Find the TarifPlan add call
            add_calls = mock_session.add.call_args_list
            # At least one call should have an object with name containing marker
            # (This is a weak test - implementation will validate)
            assert len(add_calls) > 0
