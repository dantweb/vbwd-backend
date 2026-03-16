# Plugin: mailchimp

## Purpose

Alternative email sender backend using Mailchimp Transactional (Mandrill) API. When enabled and set as active sender in the `email` plugin config, all transactional emails are routed through Mandrill instead of direct SMTP. Provides no API routes of its own.

## Installation

1. Add to `plugins/plugins.json`:
   ```json
   { "name": "mailchimp", "enabled": true }
   ```
2. Add config block to `plugins/config.json` (see Configuration).
3. In `plugins/config.json` for the `email` plugin, set `"active_sender": "mandrill"`.
4. No Alembic migration required.

## Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `mandrill_api_key` | string | `""` | Mailchimp Transactional (Mandrill) API key |
| `from_email` | string | `"noreply@example.com"` | Default from address |
| `from_name` | string | `"VBWD"` | Default from display name |

## API Endpoints

None.

## Events Emitted

None.

## Events Consumed

None.

## Architecture

```
plugins/mailchimp/
├── __init__.py                # MailchimpPlugin — registers MandrillEmailSender on enable
└── src/
    └── services/
        └── mandrill_sender.py # MandrillEmailSender implementing IEmailSender
```

## Extending

`MandrillEmailSender` implements the `IEmailSender` protocol used by `EmailSenderRegistry`. To add another cloud provider (SendGrid, Postmark, etc.), implement the same protocol and register in `on_enable()`.
