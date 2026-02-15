"""TaroSessionService - business logic for Taro sessions."""
from typing import Optional, Tuple, List
from datetime import datetime, timedelta
from uuid import uuid4
from random import randint
from src.extensions import db
from plugins.taro.src.models.taro_session import TaroSession
from plugins.taro.src.models.taro_card_draw import TaroCardDraw
from plugins.taro.src.repositories.arcana_repository import ArcanaRepository
from plugins.taro.src.repositories.taro_session_repository import TaroSessionRepository
from plugins.taro.src.repositories.taro_card_draw_repository import TaroCardDrawRepository
from src.models.enums import TaroSessionStatus, CardPosition, CardOrientation


class TaroSessionService:
    """Service for managing Taro sessions with business logic."""

    # Token consumption
    SESSION_BASE_TOKENS = 10  # Fixed cost per session
    # Variable cost added based on LLM response (handled in interpreter service)

    def __init__(
        self,
        arcana_repo: ArcanaRepository,
        session_repo: TaroSessionRepository,
        card_draw_repo: TaroCardDrawRepository,
    ):
        """Initialize service with repositories."""
        self.arcana_repo = arcana_repo
        self.session_repo = session_repo
        self.card_draw_repo = card_draw_repo

    def create_session(
        self,
        user_id: str,
        daily_limit: int = 3,
        max_follow_ups: int = 3,
        session_tokens: int = SESSION_BASE_TOKENS,
    ) -> Optional[TaroSession]:
        """Create new Taro session with 3-card spread.

        Args:
            user_id: User creating session
            daily_limit: Max sessions allowed per day for this user
            max_follow_ups: Max follow-up questions allowed
            session_tokens: Tokens to consume for this session

        Returns:
            TaroSession if created, None if daily limit exceeded
        """
        # Check daily limit
        allowed, _ = self.check_daily_limit(user_id, daily_limit)
        if not allowed:
            return None

        # Create session
        now = datetime.utcnow()
        session = self.session_repo.create(
            user_id=user_id,
            status=TaroSessionStatus.ACTIVE.value,
            started_at=now,
            expires_at=now + timedelta(minutes=30),  # 30-minute session
            spread_id=f"spread-{uuid4()}",
            tokens_consumed=session_tokens,
            follow_up_count=0,
            max_follow_ups=max_follow_ups,
        )

        # Generate 3-card spread
        self._generate_spread(session)

        return session

    def _generate_spread(self, session: TaroSession) -> List[TaroCardDraw]:
        """Generate 3-card spread (PAST, PRESENT, FUTURE) for session.

        Args:
            session: TaroSession to generate spread for

        Returns:
            List of 3 TaroCardDraw cards
        """
        # Get 3 random Arcanas
        arcanas = self.arcana_repo.get_random(count=3)
        positions = [CardPosition.PAST, CardPosition.PRESENT, CardPosition.FUTURE]

        cards = []
        for arcana, position in zip(arcanas, positions):
            # Randomize orientation: 70% upright, 30% reversed
            is_upright = randint(1, 100) <= 70
            orientation = (
                CardOrientation.UPRIGHT
                if is_upright
                else CardOrientation.REVERSED
            )

            card = self.card_draw_repo.create(
                session_id=str(session.id),
                arcana_id=str(arcana.id),
                position=position.value,
                orientation=orientation.value,
                ai_interpretation="",  # Will be set by interpreter service
            )
            cards.append(card)

        return cards

    def get_session(self, session_id: str) -> Optional[TaroSession]:
        """Get session by ID."""
        return self.session_repo.get_by_id(session_id)

    def get_user_active_session(self, user_id: str) -> Optional[TaroSession]:
        """Get user's current active session."""
        return self.session_repo.get_active_session(user_id)

    def get_session_spread(self, session_id: str) -> List[TaroCardDraw]:
        """Get 3-card spread for session."""
        return self.card_draw_repo.get_session_cards(session_id)

    def get_user_session_history(self, user_id: str, limit: int = 10) -> List[TaroSession]:
        """Get user's session history (for revisiting past readings)."""
        sessions = self.session_repo.get_user_sessions(user_id)
        return sessions[:limit]

    def count_today_sessions(self, user_id: str) -> int:
        """Count sessions created today for user."""
        sessions = self.session_repo.get_user_sessions(user_id)

        today = datetime.utcnow().date()
        today_count = sum(
            1 for s in sessions
            if s.started_at.date() == today
        )

        return today_count

    def check_daily_limit(
        self,
        user_id: str,
        daily_limit: int,
    ) -> Tuple[bool, int]:
        """Check if user can create session (daily limit).

        Args:
            user_id: User to check
            daily_limit: Max sessions per day for this user

        Returns:
            Tuple of (allowed: bool, remaining: int)
        """
        today_count = self.count_today_sessions(user_id)
        remaining = max(0, daily_limit - today_count)

        return (remaining > 0, remaining)

    def is_session_expired(self, session: TaroSession) -> bool:
        """Check if session has expired."""
        if session.status != TaroSessionStatus.ACTIVE.value:
            return False

        return datetime.utcnow() > session.expires_at

    def has_expiry_warning(self, session: TaroSession) -> bool:
        """Check if session should show 3-minute expiry warning."""
        if session.status != TaroSessionStatus.ACTIVE.value:
            return False

        now = datetime.utcnow()
        time_until_expiry = (session.expires_at - now).total_seconds()

        # Warning when 3 minutes or less remain
        return 0 < time_until_expiry <= 180

    def add_follow_up(self, session_id: str) -> Optional[TaroSession]:
        """Add follow-up question to session.

        Args:
            session_id: Session to add follow-up to

        Returns:
            Updated session if successful, None if limit exceeded or session not found
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # Check if at max follow-ups
        if session.follow_up_count >= session.max_follow_ups:
            return None

        # Check if session expired
        if self.is_session_expired(session):
            return None

        # Increment follow-up count
        self.session_repo.increment_follow_up_count(session_id)

        return self.get_session(session_id)

    def close_session(self, session_id: str) -> bool:
        """Close an active session.

        Args:
            session_id: Session to close

        Returns:
            True if closed, False if not found
        """
        return self.session_repo.update_status(
            session_id,
            TaroSessionStatus.CLOSED,
            ended_at=datetime.utcnow(),
        )

    def cleanup_expired_sessions(self) -> int:
        """Mark expired active sessions as EXPIRED.

        Returns:
            Count of sessions updated
        """
        now = datetime.utcnow()
        expired_sessions = self.session_repo.get_expired_sessions(before=now)

        count = 0
        for session in expired_sessions:
            if session.status == TaroSessionStatus.ACTIVE.value:
                self.session_repo.update_status(session.id, TaroSessionStatus.EXPIRED)
                count += 1

        return count

    def add_tokens_consumed(self, session_id: str, tokens: int) -> bool:
        """Add tokens to session consumption (for LLM response cost).

        Args:
            session_id: Session consuming tokens
            tokens: Tokens to add

        Returns:
            True if updated, False if not found
        """
        return self.session_repo.update_tokens_consumed(session_id, tokens)
