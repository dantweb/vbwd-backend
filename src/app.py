"""Flask application factory."""
from flask import Flask, jsonify, make_response
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def _register_event_handlers(app: Flask, container) -> None:
    """
    Register event handlers with the dispatcher.

    Args:
        app: Flask application instance
        container: DI container
    """
    from src.events.security_events import PasswordResetRequestEvent, PasswordResetExecuteEvent
    from src.handlers.password_reset_handler import PasswordResetHandler

    try:
        dispatcher = container.event_dispatcher()

        # Create a mock email service for now if not configured
        # In production, this should be properly configured
        class MockEmailService:
            def send_template(self, to, template, context):
                logger.info(f"[MockEmail] Would send '{template}' to {to}")
                return type('EmailResult', (), {'success': True})()

        email_service = MockEmailService()

        # Create password reset handler
        password_reset_handler = PasswordResetHandler(
            password_reset_service=container.password_reset_service(),
            email_service=email_service,
            activity_logger=container.activity_logger(),
            reset_url_base=app.config.get('RESET_URL_BASE', 'http://localhost:5173/reset-password')
        )

        # Register handlers for security events
        dispatcher.register("security.password_reset.request", password_reset_handler)
        dispatcher.register("security.password_reset.execute", password_reset_handler)

        logger.info("Event handlers registered successfully")

    except Exception as e:
        logger.warning(f"Failed to register event handlers: {e}")


def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create and configure Flask application.

    Args:
        config: Optional configuration dictionary to override defaults.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Disable strict slashes to prevent redirects that break nginx proxy
    app.url_map.strict_slashes = False

    # Load configuration
    if config:
        app.config.update(config)
    else:
        from src.config import get_config
        app.config.from_object(get_config())

    # Initialize extensions
    from src.extensions import db, limiter, csrf
    db.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    # Exempt API routes from CSRF (they use JWT authentication)
    # CSRF is only needed for browser form submissions, not API calls
    from src.routes.auth import auth_bp
    from src.routes.user import user_bp
    from src.routes.tarif_plans import tarif_plans_bp
    from src.routes.subscriptions import subscriptions_bp
    from src.routes.invoices import invoices_bp
    from src.routes.events import events_bp
    from src.routes.admin import (
        admin_users_bp,
        admin_subs_bp,
        admin_invoices_bp,
        admin_plans_bp
    )
    csrf.exempt(auth_bp)
    csrf.exempt(user_bp)
    csrf.exempt(tarif_plans_bp)
    csrf.exempt(subscriptions_bp)
    csrf.exempt(invoices_bp)
    csrf.exempt(events_bp)
    csrf.exempt(admin_users_bp)
    csrf.exempt(admin_subs_bp)
    csrf.exempt(admin_invoices_bp)
    csrf.exempt(admin_plans_bp)

    # Initialize DI container
    from src.container import Container
    container = Container()

    # Wire container to use Flask-SQLAlchemy session
    # Initial override for app startup (event handlers, etc.)
    # Per-request override happens in before_request hook
    app.container = container

    # Override db_session for app initialization (required for event handlers)
    with app.app_context():
        container.db_session.override(db.session)

    @app.before_request
    def inject_db_session():
        """Inject db session into container for each request."""
        container.db_session.override(db.session)

    # Register event handlers (now db_session is available)
    with app.app_context():
        _register_event_handlers(app, container)

    # Register blueprints (already imported above for CSRF exemption)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(tarif_plans_bp, url_prefix="/api/v1/tarif-plans")
    app.register_blueprint(subscriptions_bp, url_prefix="/api/v1/user/subscriptions")
    app.register_blueprint(invoices_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(admin_users_bp)
    app.register_blueprint(admin_subs_bp)
    app.register_blueprint(admin_invoices_bp)
    app.register_blueprint(admin_plans_bp)

    # Health check endpoint
    @app.route("/api/v1/health")
    def health():
        """Health check endpoint."""
        return jsonify({
            "status": "ok",
            "service": "vbwd-api",
            "version": "0.1.0"
        }), 200

    # Root endpoint
    @app.route("/")
    def root():
        """Root endpoint."""
        return jsonify({
            "message": "VBWD API",
            "version": "0.1.0",
            "health": "/api/v1/health"
        }), 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(429)
    def ratelimit_handler(error):
        """Handle rate limit exceeded errors with JSON response."""
        response = make_response(jsonify({
            "error": "Rate limit exceeded",
            "message": str(error.description)
        }), 429)
        # Add Retry-After header from the error if available
        if hasattr(error, 'description') and 'retry after' in str(error.description).lower():
            # Extract retry time from description
            import re
            match = re.search(r'(\d+)\s*(second|minute)', str(error.description).lower())
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                retry_after = value if 'second' in unit else value * 60
                response.headers['Retry-After'] = str(retry_after)
        else:
            # Default to 60 seconds
            response.headers['Retry-After'] = '60'
        return response

    # Register CLI commands
    from src.cli.test_data import seed_test_data_command, cleanup_test_data_command
    app.cli.add_command(seed_test_data_command)
    app.cli.add_command(cleanup_test_data_command)

    return app
