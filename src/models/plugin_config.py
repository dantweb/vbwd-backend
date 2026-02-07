"""Plugin configuration model for persisting plugin state."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from src.extensions import db


class PluginConfig(db.Model):
    """Persists plugin enabled/disabled state and configuration across restarts."""

    __tablename__ = "plugin_config"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plugin_name = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), nullable=False, default="disabled")
    config = Column(JSONB, default=dict)
    enabled_at = Column(DateTime, nullable=True)
    disabled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PluginConfig {self.plugin_name} ({self.status})>"
