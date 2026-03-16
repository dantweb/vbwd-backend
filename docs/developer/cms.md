# Plugin: cms

## Purpose

Headless CMS for managing pages, categories, images, widgets, layouts, style sheets, routing rules, and contact form submissions. Supports full ZIP import/export. Integrates with `CmsRoutingMiddleware` for before-request page routing. Contact form submissions publish `contact_form.received` to the EventBus.

## Installation

1. Add to `plugins/plugins.json`:
   ```json
   { "name": "cms", "enabled": true }
   ```
2. Add config block to `plugins/config.json` (see Configuration).
3. Run migration: `flask db upgrade`

## Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `uploads_base_path` | string | `"/app/uploads"` | Filesystem directory for uploads |
| `uploads_base_url` | string | `"/uploads"` | URL prefix for serving uploads |
| `allowed_mime_types` | list | `["image/jpeg","image/png","image/gif","image/webp","image/svg+xml","video/mp4"]` | Allowed upload MIME types |
| `max_file_size_bytes` | int | `10485760` | Max upload size (10 MB) |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/contact` | Public | Submit contact form |
| GET | `/api/v1/cms/categories` | Public | List categories |
| GET | `/api/v1/cms/pages` | Public | List published pages (paginated) |
| GET | `/api/v1/cms/pages/<slug>` | Public | Get page by slug |
| GET | `/uploads/<path>` | Public | Serve uploaded file |
| GET/POST | `/api/v1/admin/cms/pages` | Admin | List / create pages |
| GET/PUT/DELETE | `/api/v1/admin/cms/pages/<id>` | Admin | Page CRUD |
| POST | `/api/v1/admin/cms/pages/bulk` | Admin | Bulk operations |
| POST | `/api/v1/admin/cms/pages/export` | Admin | Export pages as JSON |
| POST | `/api/v1/admin/cms/pages/import` | Admin | Import pages from JSON |
| GET/POST | `/api/v1/admin/cms/categories` | Admin | Category CRUD |
| GET/PUT/DELETE | `/api/v1/admin/cms/categories/<id>` | Admin | Category detail |
| GET/POST | `/api/v1/admin/cms/images` | Admin | Image CRUD |
| POST | `/api/v1/admin/cms/images/upload` | Admin | Upload image |
| POST | `/api/v1/admin/cms/images/<id>/resize` | Admin | Resize image |
| GET/POST | `/api/v1/admin/cms/widgets` | Admin | Widget CRUD |
| GET/POST | `/api/v1/admin/cms/layouts` | Admin | Layout CRUD |
| GET/POST | `/api/v1/admin/cms/styles` | Admin | Style CRUD |
| GET/POST | `/api/v1/admin/cms/routing-rules` | Admin | Routing rule CRUD |
| POST | `/api/v1/admin/cms/routing-rules/reload` | Admin | Apply & reload Nginx config |
| POST | `/api/v1/admin/cms/export` | Admin | Export full CMS as ZIP |
| POST | `/api/v1/admin/cms/import` | Admin | Import CMS from ZIP |

## Events Emitted

| Event | When | Payload |
|-------|------|---------|
| `contact_form.received` | Contact form widget submitted | `widget_slug`, `recipient_email`, `fields[]`, `remote_ip` |

## Events Consumed

None.

## Architecture

```
plugins/cms/
├── __init__.py
├── src/
│   ├── routes.py
│   ├── middleware/          # CmsRoutingMiddleware
│   ├── repositories/        # Page, Category, Image, Widget, Layout, Style, RoutingRule
│   └── services/            # CmsPageService, CmsImageService, CmsRoutingService, etc.
├── migrations/
└── tests/
```

## Extending

Register custom Vue widget components in `vbwd-fe-user/plugins/cms/src/registry/vueComponentRegistry.ts`. Backend widgets are stored in the `cms_widget` table with a `type` discriminator.
