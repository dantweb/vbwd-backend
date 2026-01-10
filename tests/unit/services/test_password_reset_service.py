"""Tests for PasswordResetService - TDD First."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4


class TestPasswordResetService:
    """Test suite for PasswordResetService."""

    @pytest.fixture
    def mock_user_repo(self):
        """Create mock user repository."""
        return Mock()

    @pytest.fixture
    def mock_reset_repo(self):
        """Create mock password reset repository."""
        return Mock()

    @pytest.fixture
    def service(self, mock_user_repo, mock_reset_repo):
        """Create PasswordResetService with mocked dependencies."""
        from src.services.password_reset_service import PasswordResetService

        return PasswordResetService(
            user_repository=mock_user_repo, reset_repository=mock_reset_repo
        )

    # --- Tests for create_reset_token ---

    def test_create_reset_token_for_valid_email(
        self, service, mock_user_repo, mock_reset_repo
    ):
        """Token created and stored for valid email."""
        # Arrange
        user_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user_repo.find_by_email.return_value = mock_user

        # Act
        result = service.create_reset_token("test@example.com")

        # Assert
        assert result.success is True
        assert result.user_id == str(user_id)
        assert result.email == "test@example.com"
        assert result.token is not None
        assert len(result.token) > 20  # Token should be reasonably long
        assert result.expires_at is not None
        mock_reset_repo.invalidate_tokens_for_user.assert_called_once_with(user_id)
        mock_reset_repo.create_token.assert_called_once()

    def test_create_reset_token_for_unknown_email_returns_success(
        self, service, mock_user_repo
    ):
        """No event emitted for unknown email (security - don't reveal existence)."""
        # Arrange
        mock_user_repo.find_by_email.return_value = None

        # Act
        result = service.create_reset_token("unknown@example.com")

        # Assert - should still return success to not reveal if email exists
        assert result.success is True
        assert result.token is None  # But no token generated
        assert result.user_id is None

    def test_create_reset_token_invalidates_existing_tokens(
        self, service, mock_user_repo, mock_reset_repo
    ):
        """Existing tokens invalidated before creating new one."""
        # Arrange
        user_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user_repo.find_by_email.return_value = mock_user

        # Act
        service.create_reset_token("test@example.com")

        # Assert
        mock_reset_repo.invalidate_tokens_for_user.assert_called_once_with(user_id)

    def test_create_reset_token_sets_expiry_one_hour(
        self, service, mock_user_repo, mock_reset_repo
    ):
        """Token should expire after 1 hour."""
        # Arrange
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user_repo.find_by_email.return_value = mock_user

        # Act
        before = datetime.utcnow()
        result = service.create_reset_token("test@example.com")
        after = datetime.utcnow()

        # Assert - expiry should be approximately 1 hour from now
        assert result.expires_at is not None
        expected_min = before + timedelta(hours=1) - timedelta(seconds=1)
        expected_max = after + timedelta(hours=1) + timedelta(seconds=1)
        assert expected_min <= result.expires_at <= expected_max

    # --- Tests for reset_password ---

    def test_reset_password_with_valid_token(
        self, service, mock_user_repo, mock_reset_repo
    ):
        """Password reset succeeds with valid token."""
        # Arrange
        user_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"

        mock_token = Mock()
        mock_token.user_id = user_id
        mock_token.expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_token.used_at = None

        mock_reset_repo.find_by_token.return_value = mock_token
        mock_user_repo.find_by_id.return_value = mock_user

        # Act
        result = service.reset_password("valid_token", "NewPassword123!")

        # Assert
        assert result.success is True
        assert result.user_id == str(user_id)
        assert result.email == "test@example.com"
        mock_reset_repo.mark_used.assert_called_once()

    def test_reset_password_with_invalid_token(self, service, mock_reset_repo):
        """Password reset fails with invalid token."""
        # Arrange
        mock_reset_repo.find_by_token.return_value = None

        # Act
        result = service.reset_password("invalid_token", "NewPassword123!")

        # Assert
        assert result.success is False
        assert result.error == "Invalid token"
        assert result.failure_reason == "invalid"

    def test_reset_password_with_expired_token(self, service, mock_reset_repo):
        """Password reset fails with expired token."""
        # Arrange
        mock_token = Mock()
        mock_token.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
        mock_token.used_at = None
        mock_reset_repo.find_by_token.return_value = mock_token

        # Act
        result = service.reset_password("expired_token", "NewPassword123!")

        # Assert
        assert result.success is False
        assert result.error == "Token expired"
        assert result.failure_reason == "expired"

    def test_reset_password_with_already_used_token(self, service, mock_reset_repo):
        """Password reset fails with already used token."""
        # Arrange
        mock_token = Mock()
        mock_token.expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_token.used_at = datetime.utcnow() - timedelta(minutes=30)  # Already used
        mock_reset_repo.find_by_token.return_value = mock_token

        # Act
        result = service.reset_password("used_token", "NewPassword123!")

        # Assert
        assert result.success is False
        assert result.error == "Token already used"
        assert result.failure_reason == "already_used"

    def test_reset_password_updates_user_password(
        self, service, mock_user_repo, mock_reset_repo
    ):
        """Password is actually updated in the database."""
        # Arrange
        user_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"

        mock_token = Mock()
        mock_token.user_id = user_id
        mock_token.expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_token.used_at = None

        mock_reset_repo.find_by_token.return_value = mock_token
        mock_user_repo.find_by_id.return_value = mock_user

        # Act
        service.reset_password("valid_token", "NewPassword123!")

        # Assert
        mock_user_repo.update.assert_called_once()

    def test_reset_password_marks_token_as_used(
        self, service, mock_user_repo, mock_reset_repo
    ):
        """Token is marked as used after successful reset."""
        # Arrange
        user_id = uuid4()
        token_id = uuid4()
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"

        mock_token = Mock()
        mock_token.id = token_id
        mock_token.user_id = user_id
        mock_token.expires_at = datetime.utcnow() + timedelta(hours=1)
        mock_token.used_at = None

        mock_reset_repo.find_by_token.return_value = mock_token
        mock_user_repo.find_by_id.return_value = mock_user

        # Act
        service.reset_password("valid_token", "NewPassword123!")

        # Assert
        mock_reset_repo.mark_used.assert_called_once_with(token_id)
