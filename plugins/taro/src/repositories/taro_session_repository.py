"""Repository for TaroSession data access."""
from typing import Optional, List
from datetime import datetime
from src.extensions import db
from plugins.taro.src.models.taro_session import TaroSession
from src.models.enums import TaroSessionStatus


class TaroSessionRepository:
    """Repository for TaroSession model database operations."""

    def create(self, **kwargs) -> TaroSession:
        """Create new TaroSession."""
        session = TaroSession(**kwargs)
        db.session.add(session)
        db.session.commit()
        return session

    def get_by_id(self, session_id: str) -> Optional[TaroSession]:
        """Get TaroSession by ID."""
        return db.session.query(TaroSession).filter(TaroSession.id == session_id).first()

    def get_user_sessions(self, user_id: str) -> List[TaroSession]:
        """Get all sessions for a user, ordered by created_at descending."""
        return (
            db.session.query(TaroSession)
            .filter(TaroSession.user_id == user_id)
            .order_by(TaroSession.created_at.desc())
            .all()
        )

    def get_active_session(self, user_id: str) -> Optional[TaroSession]:
        """Get current ACTIVE session for user. Only one active session per user."""
        return (
            db.session.query(TaroSession)
            .filter(
                TaroSession.user_id == user_id,
                TaroSession.status == TaroSessionStatus.ACTIVE.value,
            )
            .first()
        )

    def get_sessions_by_status(self, status: TaroSessionStatus) -> List[TaroSession]:
        """Get all sessions with specific status."""
        return (
            db.session.query(TaroSession)
            .filter(TaroSession.status == status.value)
            .order_by(TaroSession.created_at.desc())
            .all()
        )

    def get_expired_sessions(
        self,
        before: datetime,
        status_only: Optional[TaroSessionStatus] = None,
    ) -> List[TaroSession]:
        """Get sessions expired before given datetime.

        Args:
            before: Only return sessions with expires_at < this datetime
            status_only: If provided, only return sessions with this status
        """
        query = db.session.query(TaroSession).filter(TaroSession.expires_at < before)

        if status_only:
            query = query.filter(TaroSession.status == status_only.value)

        return query.order_by(TaroSession.expires_at.desc()).all()

    def update_status(
        self,
        session_id: str,
        status: TaroSessionStatus,
        ended_at: Optional[datetime] = None,
    ) -> bool:
        """Update session status. Returns True if updated, False if not found."""
        session = self.get_by_id(session_id)
        if not session:
            return False

        session.status = status.value
        if ended_at:
            session.ended_at = ended_at

        db.session.commit()
        return True

    def count_user_sessions(self, user_id: str) -> int:
        """Count total sessions for user."""
        return db.session.query(TaroSession).filter(TaroSession.user_id == user_id).count()

    def count_active_sessions(self, user_id: str) -> int:
        """Count active sessions for user. Should typically be 0 or 1."""
        return (
            db.session.query(TaroSession)
            .filter(
                TaroSession.user_id == user_id,
                TaroSession.status == TaroSessionStatus.ACTIVE.value,
            )
            .count()
        )

    def delete(self, session_id: str) -> bool:
        """Delete TaroSession and cascade to TaroCardDraw. Returns True if deleted."""
        session = self.get_by_id(session_id)
        if session:
            db.session.delete(session)
            db.session.commit()
            return True
        return False

    def update_tokens_consumed(self, session_id: str, tokens: int) -> bool:
        """Add tokens to session consumption. Returns True if updated."""
        session = self.get_by_id(session_id)
        if not session:
            return False

        session.tokens_consumed += tokens
        db.session.commit()
        return True

    def increment_follow_up_count(self, session_id: str) -> bool:
        """Increment follow-up question count. Returns True if successful."""
        session = self.get_by_id(session_id)
        if not session:
            return False

        session.follow_up_count += 1
        db.session.commit()
        return True
