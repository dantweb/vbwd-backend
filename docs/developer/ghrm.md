# Plugin: ghrm

## Purpose

GitHub Repo Manager — software catalogue with subscription-gated GitHub repository access. Syncs README, CHANGELOG, docs, screenshots, and releases from GitHub repos. Automatically adds/removes GitHub collaborators based on subscription lifecycle events. Supports GitHub App authentication and GitHub OAuth for users.

## Installation

1. Add to `plugins/plugins.json`:
   ```json
   { "name": "ghrm", "enabled": true }
   ```
2. Add config block to `plugins/config.json` (see Configuration).
3. Place GitHub App private key at the configured path.
4. Run migration: `flask db upgrade`
5. (Optional) Seed packages: `./plugins/ghrm/bin/populate-db.sh`

## Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `github_app_id` | string | `""` | GitHub App ID |
| `github_app_private_key_path` | string | `"/app/plugins/ghrm/auth/github-app.pem"` | Path to GitHub App `.pem` key |
| `github_installation_id` | string | `""` | GitHub App installation ID |
| `github_oauth_client_id` | string | `""` | OAuth App client ID |
| `github_oauth_client_secret` | string | `""` | OAuth App client secret |
| `github_oauth_redirect_uri` | string | `"http://localhost:8080/ghrm/auth/github/callback"` | OAuth callback URL |
| `software_category_slugs` | list | `["backend","fe-user","fe-admin"]` | CMS category slugs for GHRM software |
| `software_catalogue_cms_layout_slug` | string | `"ghrm-category"` | CMS layout for catalogue pages |
| `software_detail_cms_layout_slug` | string | `"ghrm-software-detail"` | CMS layout for detail pages |
| `grace_period_fallback_days` | int | `7` | Days of access after subscription cancellation |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/ghrm/config` | Public | Public plugin config |
| GET | `/api/v1/ghrm/categories` | Public | Software categories |
| GET | `/api/v1/ghrm/packages` | Public | Package catalogue (paginated) |
| GET | `/api/v1/ghrm/packages/<slug>` | Public | Package detail |
| GET | `/api/v1/ghrm/packages/<slug>/related` | Public | Related packages |
| GET | `/api/v1/ghrm/packages/<slug>/versions` | Public | Release versions |
| GET | `/api/v1/ghrm/packages/by-plan/<plan_id>` | Public | Package for a plan |
| GET | `/api/v1/ghrm/packages/<slug>/install` | Public | Install instructions |
| GET/POST | `/api/v1/ghrm/sync` | Public | Sync package from GitHub |
| GET | `/api/v1/ghrm/auth/github` | Public | Start GitHub OAuth |
| POST | `/api/v1/ghrm/auth/github/callback` | Public | GitHub OAuth callback |
| DELETE | `/api/v1/ghrm/auth/github` | Bearer | Disconnect GitHub account |
| GET | `/api/v1/ghrm/access` | Bearer | User's access status |
| GET/POST | `/api/v1/admin/ghrm/packages` | Admin | Package list / create |
| PUT | `/api/v1/admin/ghrm/packages/<id>` | Admin | Update package |
| DELETE | `/api/v1/admin/ghrm/packages/<id>` | Admin | Delete package |
| POST | `/api/v1/admin/ghrm/packages/<id>/rotate-key` | Admin | Rotate sync API key |

## Events Emitted

None (uses EventBus only as consumer).

## Events Consumed

| EventBus event | Effect |
|---------------|--------|
| `subscription.activated` | Grant GitHub repo collaborator access |
| `subscription.cancelled` | Schedule access revocation after grace period |
| `subscription.payment_failed` | Revoke access immediately |
| `subscription.renewed` | Grant fresh collaborator access |

## Architecture

```
plugins/ghrm/
├── __init__.py
├── src/
│   ├── routes.py
│   ├── scheduler.py         # Grace-period revocation scheduler
│   ├── repositories/        # Package, Version, Access, OAuthToken repos
│   └── services/            # GhrmService, GitHubAppClient, OAuthService
├── auth/
│   └── github-app.pem       # GitHub App private key (gitignored)
├── migrations/
└── tests/
```

## Extending

Add new package metadata fields to the `ghrm_package` model and the sync service. The scheduler runs revocation jobs in-process — replace with Celery for production workloads.
