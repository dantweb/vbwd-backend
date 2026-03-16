# Plugin: paypal

## Purpose

PayPal payment provider implementing the `IPaymentSdkAdapter` interface. Handles PayPal order creation, subscription setup, payment capture, webhook event processing, and refunds. On successful payment, emits `PaymentCapturedEvent` which triggers subscription activation and email notifications.

## Installation

1. Add to `plugins/plugins.json`:
   ```json
   { "name": "paypal", "enabled": true }
   ```
2. Add config block to `plugins/config.json` (see Configuration).
3. Configure PayPal webhook in your PayPal Developer dashboard pointing to `/api/v1/plugins/paypal/webhook`.
4. No Alembic migration required.

## Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `client_id` | string | `""` | PayPal App client ID |
| `client_secret` | string | `""` | PayPal App client secret |
| `mode` | string | `"sandbox"` | `sandbox` or `live` |
| `webhook_id` | string | `""` | PayPal webhook ID (for signature verification) |
| `return_url` | string | `""` | Redirect URL after approval |
| `cancel_url` | string | `""` | Redirect URL on cancellation |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/plugins/paypal/create-session` | Bearer | Create PayPal order or subscription |
| POST | `/api/v1/plugins/paypal/create-order` | Bearer | Alias for create-session |
| POST | `/api/v1/plugins/paypal/capture-order` | Bearer | Capture an approved payment |
| GET | `/api/v1/plugins/paypal/session-status/<order_id>` | Bearer | Poll order/subscription status |
| POST | `/api/v1/plugins/paypal/webhook` | PayPal signature | Receive PayPal webhook events |

## Events Emitted

| Domain event | When |
|-------------|------|
| `PaymentCapturedEvent` | Successful payment capture |
| `SubscriptionCancelledEvent` | PayPal subscription cancelled |
| `PaymentFailedEvent` | Payment declined |

## Events Consumed

None.

## Architecture

```
plugins/paypal/
├── __init__.py        # PayPalPlugin class
├── routes.py          # Blueprint: /api/v1/plugins/paypal/
├── sdk_adapter.py     # PayPalSdkAdapter implementing IPaymentSdkAdapter
└── tests/
```

## Extending

Override `sdk_adapter.py` methods to support new PayPal API features (e.g., vaulted cards). The adapter protocol is shared with Stripe and YooKassa — new providers follow the same interface.
