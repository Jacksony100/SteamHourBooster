# Changelog

All notable changes for DeckPilot will be documented here.

## 2.0.0-beta.1 - 2026-06-16

### Added

- Next.js 15 dashboard UI.
- FastAPI backend with secure cookie auth and CSRF protection.
- SQLAlchemy/Alembic database layer.
- PostgreSQL/Redis Docker Compose stack.
- SessionManager with `steam_sessions`, `session_events`, heartbeat, idempotent start/stop, and graceful shutdown.
- SaaS billing layer with plans, subscriptions, payments, provider abstraction, and idempotent webhooks.
- Admin control center with overview metrics, user filters, detail drawer data, billing controls, force-stop sessions, payments, and audit logs.
- Public documentation for architecture, security, deployment, API, billing, sessions, and roadmap.
- Account security settings for active sessions, data export, and account deletion.
- Legal/trust pages for terms, privacy, security, and system status.
- Liveness and readiness endpoints for deployment health checks.

### Preserved

- Legacy Flask prototype under `legacy/flask` for reference and migration planning.

### Security

- One-way password hashing.
- Encrypted Steam credentials.
- Owner-only account/session access checks.
- Admin-only control center routes.
- Dependency audit checks in CI.
- Strict production settings validation for secrets, HTTPS URLs, secure cookies, CORS, SQLite, mock billing, and demo mode.
- Server-side billing provider selection with mock billing blocked in production.
- Revocable web sessions backed by `user_sessions`.
- Password reset tokens are hashed, expiring, single-use, and revoke active sessions after reset.
- Email verification tokens are hashed and never returned from production-facing responses.
- Redis-backed rate limits in production with fail-closed behavior if Redis is unavailable.
