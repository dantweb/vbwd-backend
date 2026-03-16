# Plugin: stripe

## Purpose

Stripe payment provider implementing the `IPaymentSdkAdapter` interface. Handles Stripe Checkout session creation, session polling, webhook event processing (payments, renewals, refunds), and subscription cancellations. On successful payment, emits `PaymentCapturedEvent` which triggers subscription activation and email notifications.

## Installation

1. Add to `plugins/plugins.json`:
   ```json
   { "name": "stripe", "enabled": true }
   ```
2. Add config block to `plugins/config.json` (see Configuration).
3. Configure Stripe webhook in your Stripe Dashboard pointing to `/api/v1/plugins/stripe/webhook`. Enable events: `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.deleted`, `charge.refunded`, `refund.updated`.
4. No Alembic migration required.

## Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `api_key` | string | `""` | Stripe secret key (`sk_test_…` / `sk_live_…`) |
| `webhook_secret` | string | `""` | Stripe webhook signing secret (`whsec_…`) |
| `success_url` | string | `""` | Redirect URL on successful checkout |
| `cancel_url` | string | `""` | Redirect URL on cancelled checkout |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/plugins/stripe/create-session` | Bearer | Create Stripe Checkout session |
| GET | `/api/v1/plugins/stripe/session-status/<session_id>` | Bearer | Poll session status |
| POST | `/api/v1/plugins/stripe/webhook` | Stripe signature | Receive Stripe webhook events |

## Events Emitted

| Domain event | Stripe trigger |
|-------------|---------------|
| `PaymentCapturedEvent` | `checkout.session.completed`, `invoice.paid` |
| `SubscriptionCancelledEvent` | `customer.subscription.deleted` |
| `PaymentFailedEvent` | `invoice.payment_failed` |
| `PaymentRefundedEvent` | `charge.refunded` |
| `RefundReversedEvent` | `refund.updated` (refund cancelled) |

## Events Consumed

None.

## Architecture

```
plugins/stripe/
├── __init__.py        # StripePlugin class
├── routes.py          # Blueprint: /api/v1/plugins/stripe/
├── sdk_adapter.py     # StripeSdkAdapter implementing IPaymentSdkAdapter
└── tests/
```

## Extending

Add new Stripe webhook event handlers in `sdk_adapter.py` inside the `handle_webhook()` method. Each event type maps to a domain event dispatch.
