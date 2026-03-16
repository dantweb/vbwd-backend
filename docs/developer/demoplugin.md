# Plugin: demoplugin

## Purpose

Minimal reference implementation for the vbwd plugin system. Returns `{"success": true}` when enabled and `404` when disabled. Use this as a template when creating new backend plugins.

> **Note:** Not included in public plugin repositories (Phase D of Sprint 10) — reference implementation only.

## Installation

1. Add to `plugins/plugins.json`:
   ```json
   { "name": "demoplugin", "enabled": true }
   ```
2. No config block required.
3. No Alembic migration required.

## Configuration

No configuration keys.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/backend-demo-plugin` | Bearer | Returns `{"success": true}` |

## Events Emitted

None.

## Events Consumed

None.

## Architecture

```
plugins/demoplugin/
├── __init__.py       # DemoPlugin class
├── routes.py         # Blueprint: /api/v1/backend-demo-plugin
├── config.json
└── admin-config.json
```

## Extending

Copy this directory as the starting point for a new plugin. Rename the class in `__init__.py`, update `metadata`, and replace `routes.py` with your own Blueprint.
