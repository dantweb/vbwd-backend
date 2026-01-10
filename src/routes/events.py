"""Frontend events receiver route.

Receives events from frontend EventBus and dispatches them
to the backend event system for processing.
"""
from flask import Blueprint, request, jsonify, current_app, g
from marshmallow import Schema, fields, ValidationError, validate
from src.middleware.auth import require_auth
from src.extensions import limiter
from src.events.dispatcher import Event


# Create blueprint
events_bp = Blueprint("events", __name__, url_prefix="/api/v1/events")


class FrontendEventSchema(Schema):
    """Schema for a single frontend event."""

    type = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    data = fields.Dict(required=False, load_default={})
    timestamp = fields.Str(required=False)


class EventsBatchSchema(Schema):
    """Schema for batch of frontend events."""

    events = fields.List(fields.Nested(FrontendEventSchema), required=True)


# Initialize schemas
event_schema = FrontendEventSchema()
events_batch_schema = EventsBatchSchema()


# Allowed frontend event types (whitelist for security)
ALLOWED_EVENT_TYPES = {
    # Auth events
    "auth:login",
    "auth:logout",
    "auth:token-refreshed",
    "auth:session-expired",
    # User events
    "user:registered",
    "user:updated",
    "user:deleted",
    # Subscription events
    "subscription:created",
    "subscription:activated",
    "subscription:upgraded",
    "subscription:downgraded",
    "subscription:cancelled",
    "subscription:expired",
    # Payment events
    "payment:initiated",
    "payment:completed",
    "payment:failed",
    "payment:refunded",
    # Plugin events
    "plugin:registered",
    "plugin:initialized",
    "plugin:error",
    "plugin:stopped",
}


@events_bp.route("", methods=["POST"])
@require_auth
@limiter.limit("100 per minute")
def receive_events():
    """
    Receive events from frontend EventBus.

    Events are validated, filtered by whitelist, and dispatched
    to the backend event system.

    ---
    Request body:
        {
            "events": [
                {
                    "type": "subscription:created",
                    "data": { "subscriptionId": "123", "planId": "456" },
                    "timestamp": "2026-01-05T10:30:00.000Z"
                }
            ]
        }

    Returns:
        200: {
            "received": 3,
            "processed": 2,
            "errors": ["Event type 'invalid:event' not allowed"]
        }
    """
    try:
        data = events_batch_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"success": False, "error": str(err.messages)}), 400

    events = data.get("events", [])
    user_id = g.user_id

    # Get dispatcher from container
    try:
        dispatcher = current_app.container.event_dispatcher()
    except Exception:
        # Fallback if container not configured
        dispatcher = None

    received = len(events)
    processed = 0
    errors = []

    for event_data in events:
        event_type = event_data.get("type")

        # Validate event type against whitelist
        if event_type not in ALLOWED_EVENT_TYPES:
            errors.append(f"Event type '{event_type}' not allowed")
            continue

        # Create backend event
        backend_event = Event(
            name=f"frontend:{event_type}",
            data={
                "user_id": user_id,
                "frontend_data": event_data.get("data", {}),
                "timestamp": event_data.get("timestamp"),
                "source": "frontend",
            },
        )

        # Dispatch event
        if dispatcher:
            try:
                dispatcher.dispatch(backend_event)
                processed += 1
            except Exception as e:
                errors.append(f"Error processing '{event_type}': {str(e)}")
        else:
            # No dispatcher - just log
            current_app.logger.info(f"Frontend event: {event_type} from user {user_id}")
            processed += 1

    return (
        jsonify(
            {
                "received": received,
                "processed": processed,
                "errors": errors if errors else None,
            }
        ),
        200,
    )


@events_bp.route("/types", methods=["GET"])
@require_auth
def list_event_types():
    """
    List allowed event types.

    Useful for frontend to know which events will be processed.

    ---
    Returns:
        200: {
            "event_types": ["auth:login", "auth:logout", ...]
        }
    """
    return jsonify({"event_types": sorted(list(ALLOWED_EVENT_TYPES))}), 200
