# Re-export create_app from app.py for gunicorn compatibility
from vbwd.app import create_app

__all__ = ["create_app"]
