"""Flask application factory."""
from flask import Flask, jsonify, make_response
from typing import Optional, Dict, Any


def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create and configure Flask application.

    Args:
        config: Optional configuration dictionary to override defaults.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    if config:
        app.config.update(config)
    else:
        from src.config import get_config
        app.config.from_object(get_config())

    # Initialize extensions
    from src.extensions import db, limiter
    db.init_app(app)
    limiter.init_app(app)

    # Initialize DI container
    from src.container import Container
    container = Container()

    # Wire container to use Flask-SQLAlchemy session
    # The session is overridden per-request via before_request hook
    app.container = container

    @app.before_request
    def inject_db_session():
        """Inject db session into container for each request."""
        container.db_session.override(db.session)

    # Register blueprints
    from src.routes.auth import auth_bp
    from src.routes.user import user_bp
    from src.routes.tarif_plans import tarif_plans_bp
    from src.routes.subscriptions import subscriptions_bp
    from src.routes.invoices import invoices_bp
    from src.routes.admin import (
        admin_users_bp,
        admin_subs_bp,
        admin_invoices_bp,
        admin_plans_bp
    )
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(tarif_plans_bp, url_prefix="/api/v1/tarif-plans")
    app.register_blueprint(subscriptions_bp, url_prefix="/api/v1/user/subscriptions")
    app.register_blueprint(invoices_bp)
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

    return app
