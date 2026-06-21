# Architecture

DeckPilot is organized as a monorepo with a modern web app, API service, worker service, shared package area, Docker deployment assets, and preserved legacy Flask code.

## System Overview

```text
Browser
  -> Next.js web app
     -> FastAPI API
        -> PostgreSQL
        -> Redis/RQ
        -> Worker service
        -> Payment provider abstraction
        -> Steam integration abstraction
```

## Applications

### `apps/web`

Next.js 15 App Router application:

- premium dark dashboard UI;
- auth screens;
- dashboard, billing, settings, admin control center;
- client-side API helper with CSRF support;
- loading, error, and empty states.

### `apps/api`

FastAPI backend:

- secure cookie auth;
- CSRF guard for mutating browser requests;
- SQLAlchemy models and Alembic migrations;
- billing/subscription service;
- Steam account service;
- session manager;
- admin control center API;
- Redis-backed production rate limiting with memory fallback only in dev/test;
- audit logs.

### `apps/worker`

RQ worker process:

- transparent activity session lifecycle jobs;
- heartbeat updates;
- graceful shutdown through `SessionManager`.

## Core Domain Modules

| Module | Responsibility |
| --- | --- |
| `auth` | Register, login, logout, revocable web sessions, password reset, email verification, account export/delete. |
| `steam_accounts` | Owner-only encrypted account records and account status. |
| `games` | Owned-game lookup abstraction and selected game persistence. |
| `sessions` | `SessionManager`, `steam_sessions`, session events, worker lifecycle. |
| `billing` | Plans, subscriptions, payments, provider webhooks, entitlement limits. |
| `admin` | Overview, users, actions, payments, subscription changes, audit. |
| `audit` | Append-only administrative and sensitive action records. |

## Rate Limiting

Production uses Redis-backed counters keyed by route group and user/IP identity. If Redis is unavailable in production, protected endpoints fail closed with `503 Rate limit store unavailable`.

Development and tests use deterministic in-memory buckets only. This fallback must not be used silently in production.

## Data Stores

Production-like deployments use PostgreSQL and Redis.

SQLite is used only for tests and local smoke runs. Do not use SQLite for public multi-user deployments.

Account security uses these tables:

- `user_sessions`: server-side browser sessions keyed by hashed `sid` values from signed cookies.
- `password_reset_tokens`: single-use hashed reset tokens with short expiry.
- `users.email_*`: optional email verification state and hashed verification token.

## Session Lifecycle

Sessions are canonical in `steam_sessions`:

1. User selects games for an owned account.
2. API checks entitlement and `active_session_limit`.
3. `SessionManager` creates or returns an active session idempotently.
4. Worker starts/heartbeats/stops through `SteamClientAdapter`.
5. Events are appended to `session_events`.
6. API and worker shutdown paths close active adapter clients gracefully.

Admin force-stop attempts to stop the adapter/runtime before marking sessions stopped. If stop fails, the session is marked `error` and an audit event records the failure instead of pretending the runtime stopped.

## Billing Lifecycle

1. API creates a pending `payments` row.
2. Provider checkout is created through a provider adapter.
3. Redirect pages do not grant access.
4. Verified, idempotent webhook events transition payment state.
5. Successful payment activates or updates the user subscription.
6. Manual admin changes write audit records.

## Security Boundaries

- User passwords are one-way hashes.
- Steam credentials are encrypted at rest with `ENCRYPTION_KEY`.
- Demo mode does not require Steam passwords. Official mode must use official linking only and fails closed until configured.
- Admin routes require authenticated admin users.
- Mutating browser routes require CSRF.
- Ownership checks are enforced in accounts, games, sessions, and risk/status endpoints.
- Secrets are loaded from environment only.

## Legacy Code

Legacy Flask code lives in `legacy/flask` for reference and migration only. New work should target the SaaS 2.0 apps.
