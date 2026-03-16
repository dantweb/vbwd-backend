# Plugin: analytics

## Purpose

Dashboard analytics widget providing platform metrics for the admin backoffice. Exposes active session counts and core KPIs: MRR, total revenue, user counts, subscription activity, churn rate, conversion rate, and ARPU. No database tables — queries core tables directly.

## Installation

1. Add to `plugins/plugins.json`:
   ```json
   { "name": "analytics", "enabled": true }
   ```
2. Add config block to `plugins/config.json`:
   ```json
   { "analytics": {} }
   ```
3. No Alembic migration required.

## Configuration

No configuration keys. The plugin uses no external services.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/plugins/analytics/active-sessions` | Bearer + Admin | Active sessions count |
| GET | `/api/v1/admin/analytics/dashboard` | Bearer + Admin | Full dashboard metrics |

### Dashboard response fields

`mrr`, `revenue_total`, `revenue_this_month`, `user_count`, `new_users_this_month`, `active_subscriptions`, `cancelled_this_month`, `churn_rate`, `conversion_rate`, `arpu`

## Events Emitted

None.

## Events Consumed

None.

## Architecture

```
plugins/analytics/
├── __init__.py          # AnalyticsPlugin class
├── src/
│   └── routes.py        # Blueprint: /api/v1/admin/analytics/ + /api/v1/plugins/analytics/
└── tests/
    ├── conftest.py
    ├── test_plugin.py
    └── test_routes.py
```

## Extending

Add new metric endpoints directly to `src/routes.py`. All queries use `db.session` — no additional repositories needed for read-only analytics.
