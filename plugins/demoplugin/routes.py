"""Demo plugin API routes."""
from flask import Blueprint, jsonify, current_app
from src.middleware.auth import require_auth

demo_plugin_bp = Blueprint("demo_plugin", __name__)


@demo_plugin_bp.route("", methods=["GET"])
@require_auth
def demo_endpoint():
    """Return success if plugin is enabled, 404 otherwise."""
    # Check config_store (shared JSON) for enabled status — consistent across workers
    config_store = getattr(current_app, "config_store", None)
    if not config_store:
        return jsonify({"error": "Plugin system not available"}), 404

    entry = config_store.get_by_name("backend-demo-plugin")
    if not entry or entry.status != "enabled":
        return jsonify({"error": "Plugin not enabled"}), 404

    # Read greeting from saved config
    config = config_store.get_config("backend-demo-plugin")
    greeting = config.get("greeting", "Hello from demo plugin!")

    return jsonify({"success": True, "greeting": greeting}), 200
