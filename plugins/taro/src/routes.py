"""Routes for Taro plugin - API endpoints."""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from src.extensions import db
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from plugins.taro.src.events import (
    TaroSessionRequestedEvent,
    TaroFollowUpRequestedEvent,
)
from plugins.taro.src.services.taro_session_service import TaroSessionService
from plugins.taro.src.repositories.taro_session_repository import TaroSessionRepository
from plugins.taro.src.repositories.arcana_repository import ArcanaRepository
from plugins.taro.src.repositories.taro_card_draw_repository import TaroCardDrawRepository


taro_bp = Blueprint("taro", __name__, url_prefix="/api/v1/taro")


def _get_taro_services():
    """Get Taro service instances."""
    arcana_repo = ArcanaRepository(db.session)
    session_repo = TaroSessionRepository(db.session)
    card_draw_repo = TaroCardDrawRepository(db.session)

    session_service = TaroSessionService(
        arcana_repo=arcana_repo,
        session_repo=session_repo,
        card_draw_repo=card_draw_repo,
    )

    return session_service


def check_token_balance(user_id: str, tokens_required: int = 10) -> bool:
    """Check if user has sufficient tokens.

    Args:
        user_id: User ID to check
        tokens_required: Number of tokens needed

    Returns:
        True if user has sufficient tokens, False otherwise
    """
    from src.services.token_service import TokenService

    token_service = TokenService(db.session)
    user_balance = token_service.get_balance(user_id)
    return user_balance >= tokens_required


@taro_bp.route("/session", methods=["POST"])
def create_session():
    """Create a new Taro reading session.

    Returns:
        JSON response with session_id and initial 3-card spread
    """
    try:
        user_id = get_jwt_identity()
        session_service = _get_taro_services()

        # Get daily limit from user's tarif plan
        daily_limit = 3  # Default
        max_follow_ups = 3  # Default

        # Use sensible defaults for limits (can be overridden by user's plan)
        # TODO: Lookup user's subscription plan from database if needed

        # Check daily limit
        allowed, remaining = session_service.check_daily_limit(user_id, daily_limit)
        if not allowed:
            return (
                jsonify({
                    "success": False,
                    "message": f"Daily limit reached. You can create {daily_limit} sessions per day.",
                    "remaining": remaining,
                }),
                402,
            )

        # Check token balance (10 tokens base cost)
        if not check_token_balance(user_id, tokens_required=10):
            return (
                jsonify({
                    "success": False,
                    "message": "Insufficient tokens. You need at least 10 tokens to create a reading.",
                }),
                402,
            )

        # Emit event for session creation
        event = TaroSessionRequestedEvent(
            user_id=user_id,
            requested_at=datetime.utcnow(),
            daily_limit=daily_limit,
            max_follow_ups=max_follow_ups,
        )
        current_app.container.event_dispatcher().emit(event)

        # Create session and get response (service handles event processing)
        session = session_service.create_session(
            user_id=user_id,
            daily_limit=daily_limit,
            max_follow_ups=max_follow_ups,
        )

        if not session:
            return (
                jsonify({
                    "success": False,
                    "message": "Failed to create session",
                }),
                500,
            )

        # Get spread cards
        cards = session_service.get_session_spread(session.id)

        return (
            jsonify({
                "success": True,
                "message": "Taro session created successfully",
                "session": {
                    "session_id": str(session.id),
                    "user_id": str(session.user_id),
                    "spread_id": str(session.spread_id),
                    "status": session.status,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                    "cards": [
                        {
                            "card_id": str(card.id),
                            "position": card.position,
                            "orientation": card.orientation,
                            "arcana_id": str(card.arcana_id),
                            "interpretation": card.ai_interpretation,
                        }
                        for card in cards
                    ],
                    "tokens_consumed": session.tokens_consumed,
                },
            }),
            201,
        )

    except Exception as e:
        return (
            jsonify({
                "success": False,
                "message": f"Error creating session: {str(e)}",
            }),
            500,
        )


@taro_bp.route("/session/<session_id>/follow-up", methods=["POST"])
def create_follow_up(session_id: str):
    """Create a follow-up question for an active session.

    Args:
        session_id: ID of the session to add follow-up to

    Returns:
        JSON response with follow-up interpretation
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}

        question = data.get("question", "")
        follow_up_type = data.get("follow_up_type", "SAME_CARDS")

        # Validate follow_up_type
        valid_types = {"SAME_CARDS", "ADDITIONAL", "NEW_SPREAD"}
        if follow_up_type not in valid_types:
            return (
                jsonify({
                    "success": False,
                    "message": f"Invalid follow_up_type. Must be one of {valid_types}",
                }),
                400,
            )

        # Validate question
        if not question or not question.strip():
            return (
                jsonify({
                    "success": False,
                    "message": "Question is required",
                }),
                400,
            )

        session_service = _get_taro_services()

        # Get session
        session = session_service.get_session(session_id)
        if not session:
            return (
                jsonify({
                    "success": False,
                    "message": "Session not found",
                }),
                404,
            )

        # Verify user owns session
        if str(session.user_id) != str(user_id):
            return (
                jsonify({
                    "success": False,
                    "message": "Unauthorized",
                }),
                403,
            )

        # Check if session is expired
        if session.status == "EXPIRED":
            return (
                jsonify({
                    "success": False,
                    "message": "Session has expired",
                }),
                410,
            )

        # Check if session is closed
        if session.status == "CLOSED":
            return (
                jsonify({
                    "success": False,
                    "message": "Session is closed",
                }),
                410,
            )

        # Get max follow-ups from user's plan
        max_follow_ups = 3  # Default
        # Use default max_follow_ups (can be overridden by user's plan)
        # TODO: Lookup user's subscription plan from database if needed

        # Check follow-up count limit
        if session.follow_up_count >= max_follow_ups:
            return (
                jsonify({
                    "success": False,
                    "message": f"Maximum follow-ups ({max_follow_ups}) reached for this session",
                }),
                402,
            )

        # Check token balance for follow-up (5 base + LLM tokens)
        if not check_token_balance(user_id, tokens_required=15):
            return (
                jsonify({
                    "success": False,
                    "message": "Insufficient tokens. You need at least 15 tokens for a follow-up",
                }),
                402,
            )

        # Emit follow-up event
        event = TaroFollowUpRequestedEvent(
            session_id=session_id,
            user_id=user_id,
            question=question,
            follow_up_type=follow_up_type,
            requested_at=datetime.utcnow(),
        )
        current_app.container.event_dispatcher().emit(event)

        # Return success response
        return (
            jsonify({
                "success": True,
                "message": "Follow-up question submitted successfully",
                "follow_up": {
                    "session_id": session_id,
                    "question": question,
                    "follow_up_type": follow_up_type,
                    "follow_up_count": session.follow_up_count + 1,
                    "requested_at": datetime.utcnow().isoformat(),
                },
            }),
            201,
        )

    except Exception as e:
        return (
            jsonify({
                "success": False,
                "message": f"Error creating follow-up: {str(e)}",
            }),
            500,
        )


@taro_bp.route("/history", methods=["GET"])
def get_session_history():
    """Get user's Taro session history.

    Query parameters:
        limit: Number of sessions to return (default 10)
        offset: Offset for pagination (default 0)
        status: Filter by status (ACTIVE, EXPIRED, CLOSED)

    Returns:
        JSON response with list of sessions
    """
    try:
        user_id = get_jwt_identity()

        # Get pagination parameters
        limit = request.args.get("limit", 10, type=int)
        offset = request.args.get("offset", 0, type=int)
        status_filter = request.args.get("status", None)

        # Validate pagination
        limit = min(limit, 100)  # Max 100 items per request
        limit = max(limit, 1)

        session_service = _get_taro_services()

        # Get sessions
        sessions = session_service.get_user_sessions(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

        # Filter by status if provided
        if status_filter:
            sessions = [s for s in sessions if s.status == status_filter]

        # Format response
        sessions_data = []
        for session in sessions:
            cards = session_service.get_session_spread(session.id)

            sessions_data.append({
                "session_id": str(session.id),
                "user_id": str(session.user_id),
                "status": session.status,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "tokens_consumed": session.tokens_consumed,
                "follow_up_count": session.follow_up_count,
                "cards": [
                    {
                        "card_id": str(card.id),
                        "position": card.position,
                        "orientation": card.orientation,
                        "arcana_id": str(card.arcana_id),
                        "interpretation": card.ai_interpretation,
                    }
                    for card in cards
                ],
            })

        return (
            jsonify({
                "success": True,
                "message": "Session history retrieved successfully",
                "sessions": sessions_data,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": session_service.count_user_sessions(user_id),
                },
            }),
            200,
        )

    except Exception as e:
        return (
            jsonify({
                "success": False,
                "message": f"Error retrieving history: {str(e)}",
            }),
            500,
        )


@taro_bp.route("/limits", methods=["GET"])
def get_daily_limits():
    """Get user's daily Taro limits and current usage.

    Returns:
        JSON response with daily limits and remaining sessions
    """
    try:
        user_id = get_jwt_identity()

        # Get daily limit from user's tarif plan
        daily_limit = 3  # Default
        plan_name = "Unknown"

        # Use default daily_limit and plan_name
        # TODO: Lookup user's subscription plan from database if needed

        session_service = _get_taro_services()

        # Check daily limit
        allowed, remaining = session_service.check_daily_limit(user_id, daily_limit)

        # Get active session if exists
        active_session = session_service.get_active_session(user_id)
        session_expiry_warning = None

        if active_session:
            has_warning = session_service.has_expiry_warning(active_session)
            if has_warning:
                time_remaining = (active_session.expires_at - datetime.utcnow()).total_seconds()
                session_expiry_warning = {
                    "has_warning": True,
                    "session_id": str(active_session.id),
                    "expires_at": active_session.expires_at.isoformat() if active_session.expires_at else None,
                    "seconds_remaining": int(time_remaining),
                }

        response_data = {
            "success": True,
            "message": "Limits retrieved successfully",
            "limits": {
                "daily_total": daily_limit,
                "daily_remaining": remaining,
                "daily_used": daily_limit - remaining,
                "plan_name": plan_name,
                "can_create": allowed,
            },
        }

        if session_expiry_warning:
            response_data["session_expiry_warning"] = session_expiry_warning

        return jsonify(response_data), 200

    except Exception as e:
        return (
            jsonify({
                "success": False,
                "message": f"Error retrieving limits: {str(e)}",
            }),
            500,
        )
