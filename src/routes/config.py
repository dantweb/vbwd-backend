"""Configuration routes for public settings."""
from flask import Blueprint, jsonify
from src.config import AVAILABLE_LANGUAGES, DEFAULT_LANGUAGE

config_bp = Blueprint("config", __name__, url_prefix="/api/v1/config")


@config_bp.route("/languages", methods=["GET"])
def get_languages():
    """
    Get available languages and default language.

    No authentication required - public endpoint.

    Returns:
        200: List of available languages and default
    """
    return jsonify({"languages": AVAILABLE_LANGUAGES, "default": DEFAULT_LANGUAGE}), 200
