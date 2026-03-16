# Plugin: yookassa

## Purpose

YooKassa (formerly Yandex.Kassa) payment provider implementing the `IPaymentSdkAdapter` interface for Russian and CIS markets. Handles payment creation, notification webhook processing, and refunds. On successful payment notification, emits `PaymentCapturedEvent` which triggers subscription activation and email notifications.

## Installation

1. Add to `plugins/plugins.json`:
   ```json
   { "name": "yookassa", "enabled": true }
   ```
2. Add config block to `plugins/config.json` (see Configuration).
3. Configure YooKassa webhook in your YooKassa merchant dashboard pointing to `/api/v1/plugins/yookassa/webhook`.
4. Whitelist YooKassa IP ranges on your server.
5. No Alembic migration required.

## Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `shop_id` | string | `""` | YooKassa shop ID |
| `secret_key` | string | `""` | YooKassa secret key |
| `return_url` | string | `""` | Redirect URL after payment |
| `allowed_ips` | list | YooKassa IP ranges | IP whitelist for webhook verification |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/plugins/yookassa/create-payment` | Bearer | Create YooKassa payment |
| POST | `/api/v1/plugins/yookassa/webhook` | YooKassa IP | Receive payment notifications |

## Events Emitted

| Domain event | When |
|-------------|------|
| `PaymentCapturedEvent` | Successful payment notification received |

## Events Consumed

None.

## Architecture

```
plugins/yookassa/
├── __init__.py        # YooKassaPlugin class
├── routes.py          # Blueprint: /api/v1/plugins/yookassa/
├── sdk_adapter.py     # YooKassaSdkAdapter implementing IPaymentSdkAdapter
└── tests/
```

## Extending

YooKassa supports auto-renewal via scheduled payments. Implement the `create_recurring_payment()` method in `sdk_adapter.py` to enable subscription auto-renewal without PayPal/Stripe billing agreements.
