from flask import Blueprint, jsonify
from src.extensions import db
from sqlalchemy import text

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Docker/k8s."""
    try:
        db.session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return (
        jsonify(
            {
                "status": "healthy" if db_status == "healthy" else "unhealthy",
                "database": db_status,
            }
        ),
        200 if db_status == "healthy" else 503,
    )
