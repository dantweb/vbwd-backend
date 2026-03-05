"""CMS Pages plugin — pages, categories, and image gallery."""
from typing import Optional, Dict, Any, TYPE_CHECKING
from src.plugins.base import BasePlugin, PluginMetadata

if TYPE_CHECKING:
    from flask import Blueprint


DEFAULT_CONFIG = {
    "uploads_base_path": "/app/uploads",
    "uploads_base_url": "/uploads",
    "allowed_mime_types": [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        "video/mp4",
    ],
    "max_file_size_bytes": 10 * 1024 * 1024,  # 10 MB
}


class CmsPlugin(BasePlugin):
    """CMS system: pages, categories, and image gallery.

    Class MUST be defined in __init__.py (not re-exported) due to
    discovery check obj.__module__ != full_module in manager.py.
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="cms",
            version="1.0.0",
            author="VBWD Team",
            description="CMS Pages — manage content pages, categories, and media",
            dependencies=[],
        )

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        merged = {**DEFAULT_CONFIG}
        if config:
            merged.update(config)
        super().initialize(merged)

    def get_blueprint(self) -> Optional["Blueprint"]:
        from plugins.cms.src.routes import cms_bp
        return cms_bp

    def get_url_prefix(self) -> Optional[str]:
        # Routes are defined with absolute paths — no prefix needed.
        return ""

    def on_enable(self) -> None:
        pass

    def on_disable(self) -> None:
        pass
