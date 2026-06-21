# Billing

DeckPilot uses a SaaS billing model with explicit plan limits, pending payments, verified provider events, and audited admin overrides.

## Plans

Default plans are seeded by `app.billing.service.sync_default_plans` and `python -m app.seed`.

| Code | Name | Duration | Account limit | Active session limit | Support |
| --- | --- | ---: | ---: | ---: | --- |
| `trial` | Trial / Demo | 14 days | 1 | 0 | community |
| `starter` | Starter | 30 days | 3 | 1 | community |
| `pro` | Pro | 30 days | 10 | 3 | priority |
| `ultra` | Ultra | 30 days | 30 | 10 | priority+ |
| `lifetime` | Lifetime | none | 30 | 10 | lifetime |

`lifetime` checkout is disabled by default. It should be granted manually by an admin or enabled only for a dedicated provider flow with verified webhooks.

## Data Model

- `plans`: product plans and limits.
- `subscriptions`: one current subscription per user.
- `payments`: checkout attempts and provider payment status.
- `billing_events`: verified/unverified provider events with idempotency keys.
- `audit_logs`: admin and billing-sensitive actions.

## Subscription Rules

A user has usable entitlement only when:

- user is not banned;
- subscription status is `active` or `trialing`;
- `expires_at` is empty or in the future;
- requested action is inside plan limits.

Enforced limits:

- adding Steam accounts checks `account_limit`;
- starting activity sessions checks `active_session_limit`;
- Trial allows one account but no active activity sessions.

## Checkout Flow

1. Client calls `POST /api/v1/billing/checkout` with `plan_code`.
2. API selects the provider from server-side `BILLING_PROVIDER`; clients cannot choose or override providers.
3. API creates a `payments` row with `pending` status.
4. Provider returns a checkout URL.
5. Redirect pages show pending/success/failed state only.
6. API does not grant a subscription from redirect alone.
7. Provider webhook is parsed and verified.
8. A unique `billing_events.idempotency_key` prevents duplicate processing.
9. Webhooks can only mutate payments from the same provider.
10. Only a verified paid event transitions payment to `paid` and activates the subscription.

## Providers

### MockProvider

Used in development and tests only. `BILLING_PROVIDER=mock` is rejected in production, and `/api/v1/billing/webhook/mock` is hidden in production.

Create checkout:

```bash
curl -X POST http://localhost:8000/api/v1/billing/checkout \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <csrf-cookie>" \
  --cookie "deckpilot_session=<session>; deckpilot_csrf=<csrf>" \
  -d '{"plan_code":"starter"}'
```

Confirm checkout in dev by sending a mock webhook with the returned `idempotency_key`:

```bash
curl -X POST http://localhost:8000/api/v1/billing/webhook/mock \
  -H "Content-Type: application/json" \
  -d '{"event_id":"evt_dev_starter_paid","event_type":"payment.paid","status":"paid","provider_payment_id":"mock_<idempotency_key>"}'
```

### CoinbaseProvider

Configuration:

```env
BILLING_PROVIDER=coinbase
COINBASE_API_KEY=
COINBASE_WEBHOOK_SECRET=
COINBASE_CHARGE_URL=https://api.commerce.coinbase.com/charges
```

Coinbase webhook requests must include `X-CC-Webhook-Signature`. The API verifies the HMAC-SHA256 signature against `COINBASE_WEBHOOK_SECRET` before applying payment state.

Missing or invalid signatures may be recorded as unverified billing events for audit/debugging, but they never activate subscriptions.

## Admin Billing

Admins can:

- change a user plan;
- grant active subscription;
- extend by days;
- cancel subscription;
- grant lifetime manually.

Endpoint:

```text
PATCH /api/v1/admin/users/{user_id}/subscription
```

Every admin subscription change writes an `admin.subscription_update` audit log.

## Migrations

Billing schema migration:

```text
apps/api/alembic/versions/002_billing_saas.py
```

Run:

```bash
cd apps/api
alembic upgrade head
python -m app.seed
```

Docker runs both automatically for the API service:

```bash
docker compose up --build
```

## Environment

Required billing env:

```env
BILLING_PROVIDER=mock
BILLING_CURRENCY=USD
COINBASE_API_KEY=
COINBASE_WEBHOOK_SECRET=
COINBASE_CHARGE_URL=https://api.commerce.coinbase.com/charges
ENABLE_LIFETIME_CHECKOUT=false
```

## Tests

```bash
cd apps/api
pytest
```

Covered:

- default plans and limits;
- trial subscription on registration;
- trial account limit;
- checkout stays pending until webhook;
- idempotent mock webhook activation;
- provider mismatch protection;
- invalid Coinbase signature does not activate subscriptions;
- unknown webhook provider returns a controlled error;
- admin grant/extend/cancel with audit logs.

## Safety Notes

- Never grant subscription after redirect only.
- Never let the client select `mock`, `coinbase`, or any internal provider.
- Never allow a webhook from one provider to mutate another provider's payment.
- Never activate subscriptions from unverified webhooks.
- Never hardcode provider secrets.
- Never store provider webhooks without idempotency keys.
- Never use billing state to enable platform-rule circumvention, network-routing evasion, credential capture, or hidden automation.
