"""CMS plugin API routes.

Public endpoints:
    GET  /api/v1/cms/pages/<slug>
    GET  /api/v1/cms/pages            ?category=<slug>&page=1&per_page=20

Admin endpoints (require_admin):
    Pages:
        GET    /api/v1/admin/cms/pages
        POST   /api/v1/admin/cms/pages
        GET    /api/v1/admin/cms/pages/<id>
        PUT    /api/v1/admin/cms/pages/<id>
        DELETE /api/v1/admin/cms/pages/<id>
        POST   /api/v1/admin/cms/pages/bulk
        POST   /api/v1/admin/cms/pages/export
        POST   /api/v1/admin/cms/pages/import

    Categories:
        GET    /api/v1/admin/cms/categories
        POST   /api/v1/admin/cms/categories
        PUT    /api/v1/admin/cms/categories/<id>
        DELETE /api/v1/admin/cms/categories/<id>

    Images:
        GET    /api/v1/admin/cms/images
        POST   /api/v1/admin/cms/images/upload
        PUT    /api/v1/admin/cms/images/<id>
        POST   /api/v1/admin/cms/images/<id>/resize
        DELETE /api/v1/admin/cms/images/<id>
        POST   /api/v1/admin/cms/images/bulk
        GET    /api/v1/admin/cms/images/export
"""
import logging
import os
from flask import Blueprint, jsonify, request, current_app, send_from_directory
from src.extensions import db
from src.middleware.auth import require_auth, require_admin

from plugins.cms.src.repositories.cms_page_repository import CmsPageRepository
from plugins.cms.src.repositories.cms_category_repository import CmsCategoryRepository
from plugins.cms.src.repositories.cms_image_repository import CmsImageRepository
from plugins.cms.src.services.cms_page_service import (
    CmsPageService, CmsPageNotFoundError, CmsPageSlugConflictError,
)
from plugins.cms.src.services.cms_category_service import (
    CmsCategoryService, CmsCategoryConflictError,
)
from plugins.cms.src.services.cms_image_service import CmsImageService, CmsImageNotFoundError
from plugins.cms.src.services.file_storage import LocalFileStorage

logger = logging.getLogger(__name__)

# Blueprint with no url_prefix — routes are defined with absolute paths.
cms_bp = Blueprint("cms", __name__)


# ── Service factory helpers ───────────────────────────────────────────────────

def _page_service() -> CmsPageService:
    page_repo = CmsPageRepository(db.session)
    cat_repo = CmsCategoryRepository(db.session)
    return CmsPageService(page_repo, cat_repo)


def _category_service() -> CmsCategoryService:
    return CmsCategoryService(CmsCategoryRepository(db.session))


def _image_service() -> CmsImageService:
    config = _cms_config()
    storage = LocalFileStorage(
        base_path=config.get("uploads_base_path", "/app/uploads"),
        base_url=config.get("uploads_base_url", "/uploads"),
    )
    return CmsImageService(CmsImageRepository(db.session), storage)


def _cms_config() -> dict:
    config_store = getattr(current_app, "config_store", None)
    if config_store:
        cfg = config_store.get_config("cms")
        if cfg:
            return cfg
    return {
        "uploads_base_path": "/app/uploads",
        "uploads_base_url": "/uploads",
    }


# ════════════════════════════════════════════════════════════════════════════
# UPLOADS — serve uploaded media files
# ════════════════════════════════════════════════════════════════════════════

@cms_bp.route("/uploads/<path:filename>", methods=["GET"])
def serve_upload(filename: str):
    """Serve uploaded files from the uploads directory.

    In production this is handled by nginx directly; in development
    Flask serves the files from the configured uploads_base_path.
    """
    config = _cms_config()
    uploads_dir = config.get("uploads_base_path", "/app/uploads")
    return send_from_directory(uploads_dir, filename)


# ════════════════════════════════════════════════════════════════════════════
# PUBLIC — CMS pages (no auth required)
# ════════════════════════════════════════════════════════════════════════════

@cms_bp.route("/api/v1/cms/categories", methods=["GET"])
def list_public_categories():
    """GET /api/v1/cms/categories — list all CMS categories (public)."""
    return jsonify(_category_service().list_categories()), 200


@cms_bp.route("/api/v1/cms/pages/<slug>", methods=["GET"])
def get_published_page(slug: str):
    """GET /api/v1/cms/pages/<slug> — fetch a published page by slug."""
    try:
        page = _page_service().get_page(slug, published_only=True)
        return jsonify(page), 200
    except CmsPageNotFoundError as e:
        return jsonify({"error": str(e)}), 404


@cms_bp.route("/api/v1/cms/pages", methods=["GET"])
def list_published_pages():
    """GET /api/v1/cms/pages — list published pages, optionally filtered by category."""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    filters = {}
    if request.args.get("category"):
        filters["category_slug"] = request.args.get("category")

    result = _page_service().list_pages(
        page=page, per_page=per_page, published_only=True, filters=filters
    )
    return jsonify(result), 200


# ════════════════════════════════════════════════════════════════════════════
# ADMIN — Pages
# ════════════════════════════════════════════════════════════════════════════

@cms_bp.route("/api/v1/admin/cms/pages", methods=["GET"])
@require_auth
@require_admin
def admin_list_pages():
    """GET /api/v1/admin/cms/pages — paginated list with filters."""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    sort_by = request.args.get("sort_by", "updated_at")
    sort_dir = request.args.get("sort_dir", "desc")

    filters = {}
    if request.args.get("category_id"):
        filters["category_id"] = request.args.get("category_id")
    if request.args.get("language"):
        filters["language"] = request.args.get("language")
    if request.args.get("is_published") is not None:
        val = request.args.get("is_published", "").lower()
        if val in ("true", "1"):
            filters["is_published"] = True
        elif val in ("false", "0"):
            filters["is_published"] = False
    if request.args.get("search"):
        filters["search"] = request.args.get("search")

    result = _page_service().list_pages(
        page=page, per_page=per_page,
        sort_by=sort_by, sort_dir=sort_dir,
        filters=filters,
    )
    return jsonify(result), 200


@cms_bp.route("/api/v1/admin/cms/pages", methods=["POST"])
@require_auth
@require_admin
def admin_create_page():
    """POST /api/v1/admin/cms/pages — create a new page."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    try:
        page = _page_service().create_page(data)
        return jsonify(page), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except CmsPageSlugConflictError as e:
        return jsonify({"error": str(e)}), 409


@cms_bp.route("/api/v1/admin/cms/pages/bulk", methods=["POST"])
@require_auth
@require_admin
def admin_bulk_pages():
    """POST /api/v1/admin/cms/pages/bulk — bulk actions on pages.

    Body: {"ids": [...], "action": "publish|unpublish|delete|set_category",
           "params": {"category_id": "..."}}
    """
    data = request.get_json()
    if not data or "ids" not in data or "action" not in data:
        return jsonify({"error": "ids and action are required"}), 400
    try:
        result = _page_service().bulk_action(
            data["ids"], data["action"], data.get("params")
        )
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@cms_bp.route("/api/v1/admin/cms/pages/export", methods=["POST"])
@require_auth
@require_admin
def admin_export_pages():
    """POST /api/v1/admin/cms/pages/export — export pages as JSON.

    Body: {"ids": [...], "format": "json"}
    """
    from flask import Response
    data = request.get_json() or {}
    ids = data.get("ids", [])
    fmt = data.get("format", "json")

    payload = _page_service().export_pages(ids, fmt)
    return Response(payload, mimetype="application/json",
                    headers={"Content-Disposition": "attachment; filename=cms-pages.json"})


@cms_bp.route("/api/v1/admin/cms/pages/import", methods=["POST"])
@require_auth
@require_admin
def admin_import_pages():
    """POST /api/v1/admin/cms/pages/import — import pages from JSON."""
    raw = request.get_data()
    if not raw:
        return jsonify({"error": "Request body required"}), 400
    try:
        result = _page_service().import_pages(raw)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Import failed: {e}"}), 400


@cms_bp.route("/api/v1/admin/cms/pages/<page_id>", methods=["GET"])
@require_auth
@require_admin
def admin_get_page(page_id: str):
    """GET /api/v1/admin/cms/pages/<id> — get a single page (any publish state)."""
    svc = _page_service()
    # Find by ID, not slug
    page_obj = svc._repo.find_by_id(page_id)
    if not page_obj:
        return jsonify({"error": "Page not found"}), 404
    return jsonify(page_obj.to_dict()), 200


@cms_bp.route("/api/v1/admin/cms/pages/<page_id>", methods=["PUT"])
@require_auth
@require_admin
def admin_update_page(page_id: str):
    """PUT /api/v1/admin/cms/pages/<id> — update a page."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    try:
        page = _page_service().update_page(page_id, data)
        return jsonify(page), 200
    except CmsPageNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except (ValueError, CmsPageSlugConflictError) as e:
        return jsonify({"error": str(e)}), 409


@cms_bp.route("/api/v1/admin/cms/pages/<page_id>", methods=["DELETE"])
@require_auth
@require_admin
def admin_delete_page(page_id: str):
    """DELETE /api/v1/admin/cms/pages/<id> — delete a page."""
    try:
        _page_service().delete_page(page_id)
        return jsonify({"deleted": page_id}), 200
    except CmsPageNotFoundError as e:
        return jsonify({"error": str(e)}), 404


# ════════════════════════════════════════════════════════════════════════════
# ADMIN — Categories
# ════════════════════════════════════════════════════════════════════════════

@cms_bp.route("/api/v1/admin/cms/categories", methods=["GET"])
@require_auth
@require_admin
def admin_list_categories():
    """GET /api/v1/admin/cms/categories — list all categories."""
    return jsonify(_category_service().list_categories()), 200


@cms_bp.route("/api/v1/admin/cms/categories", methods=["POST"])
@require_auth
@require_admin
def admin_create_category():
    """POST /api/v1/admin/cms/categories — create a category."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    try:
        cat = _category_service().create_category(data)
        return jsonify(cat), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@cms_bp.route("/api/v1/admin/cms/categories/<cat_id>", methods=["PUT"])
@require_auth
@require_admin
def admin_update_category(cat_id: str):
    """PUT /api/v1/admin/cms/categories/<id> — update a category."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    try:
        cat = _category_service().update_category(cat_id, data)
        return jsonify(cat), 200
    except KeyError as e:
        return jsonify({"error": str(e)}), 404


@cms_bp.route("/api/v1/admin/cms/categories/<cat_id>", methods=["DELETE"])
@require_auth
@require_admin
def admin_delete_category(cat_id: str):
    """DELETE /api/v1/admin/cms/categories/<id> — delete a category."""
    try:
        _category_service().delete_category(cat_id)
        return jsonify({"deleted": cat_id}), 200
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    except CmsCategoryConflictError as e:
        return jsonify({"error": str(e)}), 409


# ════════════════════════════════════════════════════════════════════════════
# ADMIN — Images
# ════════════════════════════════════════════════════════════════════════════

@cms_bp.route("/api/v1/admin/cms/images", methods=["GET"])
@require_auth
@require_admin
def admin_list_images():
    """GET /api/v1/admin/cms/images — paginated image list."""
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 24, type=int), 100)
    sort_by = request.args.get("sort_by", "created_at")
    sort_dir = request.args.get("sort_dir", "desc")
    search = request.args.get("search")

    result = _image_service().list_images(
        page=page, per_page=per_page,
        sort_by=sort_by, sort_dir=sort_dir,
        search=search,
    )
    return jsonify(result), 200


@cms_bp.route("/api/v1/admin/cms/images/upload", methods=["POST"])
@require_auth
@require_admin
def admin_upload_image():
    """POST /api/v1/admin/cms/images/upload — upload an image (multipart/form-data)."""
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400

    caption = request.form.get("caption")
    file_data = f.read()
    mime_type = f.content_type or "application/octet-stream"

    try:
        image = _image_service().upload_image(
            file_data=file_data,
            filename=f.filename,
            mime_type=mime_type,
            caption=caption,
        )
        return jsonify(image), 201
    except Exception as e:
        logger.error("Image upload failed: %s", e)
        return jsonify({"error": str(e)}), 500


@cms_bp.route("/api/v1/admin/cms/images/export", methods=["GET"])
@require_auth
@require_admin
def admin_export_images():
    """GET /api/v1/admin/cms/images/export?ids=id1,id2 — export ZIP of selected images."""
    from flask import Response
    ids_param = request.args.get("ids", "")
    ids = [i.strip() for i in ids_param.split(",") if i.strip()]
    if not ids:
        return jsonify({"error": "ids query parameter required"}), 400

    payload = _image_service().export_zip(ids)
    return Response(
        payload,
        mimetype="application/zip",
        headers={"Content-Disposition": "attachment; filename=cms-images.zip"},
    )


@cms_bp.route("/api/v1/admin/cms/images/bulk", methods=["POST"])
@require_auth
@require_admin
def admin_bulk_images():
    """POST /api/v1/admin/cms/images/bulk — bulk delete.

    Body: {"ids": [...], "action": "delete"}
    """
    data = request.get_json()
    if not data or "ids" not in data:
        return jsonify({"error": "ids required"}), 400

    action = data.get("action", "delete")
    if action != "delete":
        return jsonify({"error": f"Unknown action: {action}"}), 400

    result = _image_service().bulk_delete(data["ids"])
    return jsonify(result), 200


@cms_bp.route("/api/v1/admin/cms/images/<image_id>", methods=["PUT"])
@require_auth
@require_admin
def admin_update_image(image_id: str):
    """PUT /api/v1/admin/cms/images/<id> — update image caption/SEO."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    try:
        image = _image_service().update_image(image_id, data)
        return jsonify(image), 200
    except CmsImageNotFoundError as e:
        return jsonify({"error": str(e)}), 404


@cms_bp.route("/api/v1/admin/cms/images/<image_id>/resize", methods=["POST"])
@require_auth
@require_admin
def admin_resize_image(image_id: str):
    """POST /api/v1/admin/cms/images/<id>/resize — resize an image.

    Body: {"width": 800, "height": 600}
    """
    data = request.get_json()
    if not data or "width" not in data or "height" not in data:
        return jsonify({"error": "width and height are required"}), 400
    try:
        image = _image_service().resize_image(image_id, data["width"], data["height"])
        return jsonify(image), 200
    except CmsImageNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503


@cms_bp.route("/api/v1/admin/cms/images/<image_id>", methods=["DELETE"])
@require_auth
@require_admin
def admin_delete_image(image_id: str):
    """DELETE /api/v1/admin/cms/images/<id> — delete an image and its file."""
    try:
        _image_service().delete_image(image_id)
        return jsonify({"deleted": image_id}), 200
    except CmsImageNotFoundError as e:
        return jsonify({"error": str(e)}), 404
