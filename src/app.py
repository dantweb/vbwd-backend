"""Flask application factory."""
from flask import Flask, jsonify
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
    from src.extensions import db
    db.init_app(app)

    # Register blueprints
    from src.routes.auth import auth_bp
    from src.routes.user import user_bp
    from src.routes.tarif_plans import tarif_plans_bp
    from src.routes.subscriptions import subscriptions_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(tarif_plans_bp, url_prefix="/api/v1/tarif-plans")
    app.register_blueprint(subscriptions_bp, url_prefix="/api/v1/user/subscriptions")

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

    return app
