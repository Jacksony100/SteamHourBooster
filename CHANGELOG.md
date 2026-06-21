# Changelog

All notable changes for DeckPilot will be documented here.

## 2.0.0-beta.2 - 2026-06-21

### Added

- Steam public-data layer: profile/avatar + owned-games + game-artwork endpoints
  (`steam_data` module) with DB caching, ownership checks, CSRF + rate-limited
  refresh, and frontend `GameImage` / `SteamAvatar` components with fallbacks.
- Observability: structured JSON logging, request-id/correlation middleware,
  access logs, optional Sentry hook (`OBSERVABILITY.md`).
- HTTP security headers on the API (CSP, HSTS in prod, X-Frame-Options,
  X-Content-Type-Options, Referrer-Policy, Permissions-Policy) and on the web app
  (`next.config.mjs`).
- Design-system import from the prototype: exact token palette (electric blue /
  violet / neon green), Satoshi + General Sans fonts, signature radial-glow
  background, brand/CTA gradients (`DESIGN_IMPORT_NOTES.md`).
- Migration `006_steam_data` (Steam cache tables + audit/plan_id index hardening).
- Docs: `BETA_READINESS.md`, `STEAM_DATA_INTEGRATION.md`, `OBSERVABILITY.md`,
  `DESIGN_IMPORT_NOTES.md`, `BASELINE_STATUS.md`, `REPO_HYGIENE.md`.

### Changed

- Docker images run as a **non-root** user via multi-stage builds (no build tools
  in runtime); compose gains `restart: unless-stopped`.
- Admin subscription status is whitelisted; webhook endpoint is rate-limited.
- Rate-limit Redis path is self-healing (no permanent-lockout on a TTL-less key).
- Unhandled errors and the readiness probe no longer leak internals in production.

### Removed

- Unreachable RQ enqueue branch + misleading "queued for worker" event in the
  session manager; demo session activation is documented as synchronous inline.

### Security

- API + web security headers; non-root containers; webhook rate limiting;
  whitelisted admin subscription statuses; normalized error responses.

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
