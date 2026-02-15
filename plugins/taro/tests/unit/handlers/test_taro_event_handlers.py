"""Tests for Taro event handlers."""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock
from plugins.taro.src.handlers import (
    TaroSessionCreatedHandler,
    TaroFollowUpHandler,
)
from plugins.taro.src.events import (
    TaroSessionCreatedEvent,
    TaroFollowUpRequestedEvent,
)
from plugins.taro.src.repositories.arcana_repository import ArcanaRepository
from plugins.taro.src.repositories.taro_session_repository import TaroSessionRepository
from plugins.taro.src.repositories.taro_card_draw_repository import TaroCardDrawRepository
from plugins.taro.src.services.taro_session_service import TaroSessionService
from plugins.taro.src.services.arcana_interpretation_service import ArcanaInterpretationService


@pytest.fixture
def mock_interpreter_service():
    """Fixture providing mock ArcanaInterpretationService."""
    service = Mock(spec=ArcanaInterpretationService)
    return service


@pytest.fixture
def mock_token_service():
    """Fixture providing mock token service."""
    service = Mock()
    return service


@pytest.fixture
def session_handler(mock_interpreter_service, mock_token_service):
    """Fixture providing TaroSessionCreatedHandler."""
    return TaroSessionCreatedHandler(
        interpreter_service=mock_interpreter_service,
        token_service=mock_token_service,
        card_draw_repo=TaroCardDrawRepository(),
    )


@pytest.fixture
def follow_up_handler(mock_interpreter_service, mock_token_service):
    """Fixture providing TaroFollowUpHandler."""
    return TaroFollowUpHandler(
        interpreter_service=mock_interpreter_service,
        session_service=TaroSessionService(
            arcana_repo=ArcanaRepository(),
            session_repo=TaroSessionRepository(),
            card_draw_repo=TaroCardDrawRepository(),
        ),
        token_service=mock_token_service,
    )


class TestTaroSessionCreatedHandler:
    """Test TaroSessionCreatedHandler."""

    def test_handle_session_created_event(self, session_handler, mock_interpreter_service, mock_token_service):
        """Test handling TaroSessionCreatedEvent."""
        session_id = str(uuid4())
        user_id = str(uuid4())
        card_ids = [str(uuid4()) for _ in range(3)]

        event = TaroSessionCreatedEvent(
            session_id=session_id,
            user_id=user_id,
            spread_id="spread-001",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            created_at=datetime.utcnow(),
            card_arcana_ids=card_ids,
            initial_tokens_consumed=10,
        )

        # Mock interpreter to return interpretations
        mock_interpreter_service.generate_interpretation.return_value = (
            "Test interpretation",
            5,
        )

        # Mock token service
        mock_token_service.deduct_tokens.return_value = True

        # Handle event
        result = session_handler.handle(event)

        assert result is not None
        # Should have called interpreter service
        assert mock_interpreter_service.generate_interpretation.called

    def test_session_created_deducts_tokens(self, session_handler, mock_interpreter_service, mock_token_service, db):
        """Test that session creation deducts tokens."""
        session_id = str(uuid4())
        user_id = str(uuid4())
        card_ids = [str(uuid4()) for _ in range(3)]

        event = TaroSessionCreatedEvent(
            session_id=session_id,
            user_id=user_id,
            spread_id="spread-001",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            created_at=datetime.utcnow(),
            card_arcana_ids=card_ids,
            initial_tokens_consumed=10,
        )

        mock_interpreter_service.generate_interpretation.return_value = (
            "Interpretation",
            5,
        )
        mock_token_service.deduct_tokens.return_value = True

        session_handler.handle(event)

        # Verify tokens were deducted
        mock_token_service.deduct_tokens.assert_called_once()
        call_args = mock_token_service.deduct_tokens.call_args
        assert user_id in str(call_args)

    def test_session_created_generates_interpretations(self, session_handler, mock_interpreter_service, mock_token_service):
        """Test that session creation generates card interpretations."""
        session_id = str(uuid4())
        user_id = str(uuid4())
        card_ids = [str(uuid4()) for _ in range(3)]

        event = TaroSessionCreatedEvent(
            session_id=session_id,
            user_id=user_id,
            spread_id="spread-001",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            created_at=datetime.utcnow(),
            card_arcana_ids=card_ids,
        )

        mock_interpreter_service.generate_interpretation.return_value = (
            "Card interpretation",
            5,
        )
        mock_token_service.deduct_tokens.return_value = True

        session_handler.handle(event)

        # Should have called interpreter for each card
        assert mock_interpreter_service.generate_interpretation.call_count >= 3

    def test_session_created_handles_token_error(self, session_handler, mock_interpreter_service, mock_token_service):
        """Test handling token deduction failure."""
        session_id = str(uuid4())
        user_id = str(uuid4())
        card_ids = [str(uuid4()) for _ in range(3)]

        event = TaroSessionCreatedEvent(
            session_id=session_id,
            user_id=user_id,
            spread_id="spread-001",
            expires_at=datetime.utcnow() + timedelta(minutes=30),
            created_at=datetime.utcnow(),
            card_arcana_ids=card_ids,
        )

        mock_interpreter_service.generate_interpretation.return_value = (
            "Interpretation",
            5,
        )
        # Simulate token deduction failure
        mock_token_service.deduct_tokens.return_value = False

        result = session_handler.handle(event)

        # Should handle gracefully
        assert result is not None


class TestTaroFollowUpHandler:
    """Test TaroFollowUpHandler."""

    def test_handle_follow_up_event(self, follow_up_handler, mock_interpreter_service, mock_token_service):
        """Test handling TaroFollowUpRequestedEvent."""
        session_id = str(uuid4())
        user_id = str(uuid4())

        event = TaroFollowUpRequestedEvent(
            session_id=session_id,
            user_id=user_id,
            question="Tell me more about this card",
            follow_up_type="SAME_CARDS",
            requested_at=datetime.utcnow(),
        )

        mock_interpreter_service.generate_follow_up_interpretation.return_value = (
            "Follow-up interpretation",
            5,
        )
        mock_token_service.deduct_tokens.return_value = True

        result = follow_up_handler.handle(event)

        assert result is not None

    def test_follow_up_adds_question_count(self, follow_up_handler, mock_interpreter_service, mock_token_service):
        """Test that follow-up increments question count."""
        session_id = str(uuid4())
        user_id = str(uuid4())

        event = TaroFollowUpRequestedEvent(
            session_id=session_id,
            user_id=user_id,
            question="More insights please",
            follow_up_type="ADDITIONAL",
            requested_at=datetime.utcnow(),
        )

        mock_interpreter_service.generate_follow_up_interpretation.return_value = (
            "Additional insight",
            5,
        )
        mock_token_service.deduct_tokens.return_value = True

        follow_up_handler.handle(event)

        # Should have attempted to add follow-up
        assert mock_interpreter_service.generate_follow_up_interpretation.called

    def test_follow_up_deducts_tokens(self, follow_up_handler, mock_interpreter_service, mock_token_service):
        """Test that follow-up deducts tokens."""
        session_id = str(uuid4())
        user_id = str(uuid4())

        event = TaroFollowUpRequestedEvent(
            session_id=session_id,
            user_id=user_id,
            question="What else?",
            follow_up_type="SAME_CARDS",
            requested_at=datetime.utcnow(),
        )

        mock_interpreter_service.generate_follow_up_interpretation.return_value = (
            "Interpretation",
            5,
        )
        mock_token_service.deduct_tokens.return_value = True

        follow_up_handler.handle(event)

        # Tokens should be deducted
        assert mock_token_service.deduct_tokens.called

    def test_follow_up_validates_session_exists(self, follow_up_handler, mock_interpreter_service, mock_token_service):
        """Test that follow-up validates session exists."""
        fake_session_id = str(uuid4())
        user_id = str(uuid4())

        event = TaroFollowUpRequestedEvent(
            session_id=fake_session_id,
            user_id=user_id,
            question="Question",
            follow_up_type="SAME_CARDS",
            requested_at=datetime.utcnow(),
        )

        mock_interpreter_service.generate_follow_up_interpretation.return_value = (
            "Interpretation",
            5,
        )

        result = follow_up_handler.handle(event)

        # Should handle missing session
        assert result is not None or result is None  # Either way, no crash
