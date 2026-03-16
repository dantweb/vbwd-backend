# Plugin: email

## Purpose

Transactional email system with Jinja2-templated HTML/text templates, pluggable sender backends (SMTP, Mandrill), and event-driven dispatch for system lifecycle events. Templates are stored per `event_type` in the database. The admin API exposes template CRUD, preview rendering with example variables, and test-send functionality.

## Installation

1. Add to `plugins/plugins.json`:
   ```json
   { "name": "email", "enabled": true }
   ```
2. Add config block to `plugins/config.json` (see Configuration).
3. Run migration: `flask db upgrade`
4. (Optional) Seed default templates: `./plugins/email/bin/populate-db.sh`

## Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `smtp_host` | string | `"localhost"` | SMTP server hostname |
| `smtp_port` | int | `587` | SMTP port |
| `smtp_user` | string | `""` | SMTP username (blank = no auth) |
| `smtp_password` | string | `""` | SMTP password |
| `smtp_use_tls` | bool | `true` | Enable STARTTLS |
| `smtp_from_email` | string | `"noreply@example.com"` | From address |
| `smtp_from_name` | string | `"VBWD"` | From display name |
| `active_sender` | string | `"smtp"` | Active sender backend (`smtp` or `mandrill`) |
| `log_sends` | bool | `false` | Log all send attempts |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/admin/email/templates` | Admin | List all templates |
| POST | `/api/v1/admin/email/templates` | Admin | Create template |
| GET | `/api/v1/admin/email/templates/<id>` | Admin | Get template |
| PUT | `/api/v1/admin/email/templates/<id>` | Admin | Update template |
| DELETE | `/api/v1/admin/email/templates/<id>` | Admin | Delete template |
| GET | `/api/v1/admin/email/event-types` | Admin | List event types with variable schemas |
| POST | `/api/v1/admin/email/templates/preview` | Admin | Preview template with example data |
| POST | `/api/v1/admin/email/test-send` | Admin | Send test email to an address |

## Events Emitted

None.

## Events Consumed

| EventBus event | Handler | Email sent |
|---------------|---------|------------|
| `subscription.activated` | `on_subscription_activated` | Subscription welcome |
| `subscription.cancelled` | `on_subscription_cancelled` | Cancellation confirmation |
| `subscription.expired` | `on_subscription_expired` | Expiry notification |
| `subscription.payment_failed` | `on_subscription_payment_failed` | Payment failure alert |
| `subscription.renewed` | `on_subscription_renewed` | Renewal receipt |
| `invoice.created` | `on_invoice_created` | Invoice notification |
| `invoice.paid` | `on_invoice_paid` | Payment receipt |
| `user.registered` | `on_user_registered` | Welcome email |
| `user.password_reset` | `on_user_password_reset` | Password reset link |
| `contact_form.received` | `on_contact_form_received` | Contact form notification to admin |

## Event Type Schemas

Defined in `src/services/event_contexts.py` — 12 core schemas auto-registered at import into `EventContextRegistry`. Additional plugins register their own schemas by calling `EventContextRegistry.register()` in `on_enable()`.

## Architecture

```
plugins/email/
├── __init__.py                    # EmailPlugin class
├── src/
│   ├── routes.py                  # Admin API blueprint
│   ├── handlers.py                # EventBus subscriber functions
│   ├── seeds.py                   # Default template seeds
│   ├── models/
│   │   └── email_template.py      # EmailTemplate model
│   ├── repositories/
│   │   └── email_template_repo.py
│   └── services/
│       ├── email_service.py       # Jinja2 render + dispatch
│       ├── smtp_sender.py         # SmtpEmailSender
│       ├── sender_registry.py     # EmailSenderRegistry
│       ├── event_contexts.py      # EVENT_CONTEXTS dict (12 schemas)
│       └── event_context_registry.py  # Open registry for all plugins
└── tests/
```

## Extending

To register a custom event type for a new plugin:

```python
def on_enable(self) -> None:
    from plugins.email.src.services.event_context_registry import register
    register("my_plugin.something_happened", {
        "description": "Sent when something happens",
        "variables": {
            "user_email": {"type": "string", "description": "...", "example": "..."},
        }
    })
```

To add a new sender backend: implement `IEmailSender` protocol and call `registry.register(my_sender)` / `registry.set_active("my_sender")`.
