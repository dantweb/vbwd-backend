"""Analytics plugin API routes."""
from flask import Blueprint, jsonify, current_app
from src.middleware.auth import require_auth, require_admin

analytics_plugin_bp = Blueprint("analytics_plugin", __name__)


@analytics_plugin_bp.route("/active-sessions", methods=["GET"])
@require_auth
@require_admin
def get_active_sessions():
    """Get active sessions count from analytics plugin."""
    config_store = getattr(current_app, "config_store", None)
    if not config_store:
        return jsonify({"error": "Plugin system not available"}), 404

    entry = config_store.get_by_name("analytics")
    if not entry or entry.status != "enabled":
        return jsonify({"error": "Analytics plugin not enabled"}), 404

    plugin_manager = getattr(current_app, "plugin_manager", None)
    if not plugin_manager:
        return jsonify({"error": "Plugin system not available"}), 404

    plugin = plugin_manager.get_plugin("analytics")
    if not plugin:
        return jsonify({"error": "Analytics plugin not found"}), 404

    return jsonify(plugin.get_active_sessions()), 200
