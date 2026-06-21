# Beta Readiness

Honest status of DeckPilot / SteamHourBooster after the beta-close-all pass.
Companion to `PROJECT_AUDIT_REPORT.md` (the prior full audit).

## TL;DR
A genuinely capable SaaS **beta** whose infrastructure (auth, billing, admin,
data model, tests, CI, Docker) is largely production-shaped. The **headline
feature — real Steam activity — is a transparent demo mock** in the active app and
must be labeled as such. Ship a **clearly-labeled closed/demo beta** now; do not
make paid "it really runs your hours" promises until the core feature, email,
observability depth, and scaling are addressed.

## What WORKS (real, tested)
- Auth: register/login, bcrypt, JWT + **revocable** server-side sessions, banned-user lockout, CSRF (double-submit), rate limits (Redis fail-closed in prod, **now self-healing TTL**).
- Encrypted Steam credentials (Fernet), owner-only access checks, Steam Guard never stored.
- Subscriptions/plans with **enforced** account + active-session limits; Coinbase webhook **HMAC verify + idempotency**, unverified events never grant; **whitelisted** admin subscription statuses.
- Admin control center: overview, user search/filter, detail drawer, ban/unban, role grant (self-revoke guard), subscription changes, force-stop, payments, audit — all audit-logged.
- Session lifecycle: idempotent start/stop, heartbeats, graceful shutdown, full event + audit logging (drives the demo adapter).
- **Steam profile/avatar + game artwork** via official CDN, cached, with frontend fallbacks (`GameImage`/`SteamAvatar`).
- **Security headers** on API (and web): CSP, HSTS (prod), X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy.
- **Observability**: structured JSON logs + request IDs + access logs + optional Sentry hook; normalized error bodies.
- **Non-root** Docker images (multi-stage, no build tools in runtime); compose healthchecks + restart policies + migrations on start.
- Tests: **68 API + 16 legacy** passing; 6-job CI (lint, tests, pip-audit, npm-audit, build, docker).

## What is MOCK / DEMO (labeled, not real)
- **Steam session automation (default)** — `integrations/steam.py` + `sessions/adapters.py` are mocks in the default demo mode. A **real owner-operated idle path** now exists behind explicit triple opt-in (`STEAM_INTEGRATION_MODE=official` + `STEAM_OFFICIAL_LINKING_ENABLED=true` + `STEAM_REAL_SESSIONS_ENABLED=true`); it logs into the owner's account with their Steam Guard code and idles games so hours accrue. It is **gated off by default and NOT tested against live Steam** — see `REAL_SESSIONS.md` for scope, risks, and the no-evasion guardrails. Demo remains the default.
- **Steam profile/owned-games data** in demo mode — deterministic demo values (clearly-labeled persona, default avatar). Real values require `official` mode + `STEAM_API_KEY`.
- **Billing provider** — `mock` by default (blocked in production); Coinbase is wired but unexercised against the live API here.

## What is DISABLED / reserved
- **Official Steam linking** (`STEAM_OFFICIAL_LINKING_ENABLED=false`) — interface exists, implementation reserved.
- **RQ worker** — real infra (`apps/worker`, `app/tasks/sessions.py`) but **not engaged** in demo mode (activation is synchronous inline). The previously-unreachable enqueue path + misleading "queued" event were removed. Worker is reserved for a future official mode.

## What is now FUNCTIONAL (added in beta.2)
- **Email/recovery** — `Mailer` abstraction (console default + SMTP). Password reset
  & verification actually send; set `EMAIL_PROVIDER=smtp` + `SMTP_*` for real delivery.
- **Subscription cancel/reactivate** — cancel at period end (or immediate for no-expiry plans).
- **Session runtime state** — moved to a shared `RuntimeStore` (Redis in prod), so
  heartbeat/stop work across multiple workers. Webhook idempotency race hardened.
- **Steam official mode** — real (gated) Steam Web API calls for profile/owned-games/bans
  when `STEAM_INTEGRATION_MODE=official` + `STEAM_API_KEY` are set; demo/test never call out.
- **Observability** — `/metrics` (Prometheus) + structured logs + request IDs + Sentry hook.
- **App pages** — `/accounts`, `/sessions`, `/games` (Steam-art showcase), `/logs`,
  `/support`, `/onboarding` wired into the shell + i18n.
- **CI coverage gate** — `--cov-fail-under=75` (current ~84%).

## What is PRODUCTION-READY (with config)
- Production config validation (`config.py`): HTTPS URLs, secure cookies, no SQLite, no mock billing, non-wildcard CORS, strong admin password, demo-mode gating.
- Security headers, non-root containers, structured logs, healthchecks, migrations-on-start.

## What you must NOT promise users (yet)
- That the app actually accrues Steam hours / runs real sessions (it's a demo).
- "Risk-free" / ban-proof / undetectable anything — out of scope by design, never implemented.
- That password recovery emails arrive (no provider wired).
- Real card payments (only crypto via Coinbase, untested live; mock by default).

## Required env (beyond defaults)
`SECRET_KEY` (≥32), `ENCRYPTION_KEY` (Fernet), `ADMIN_PASSWORD` (≥12), `DATABASE_URL`
(Postgres), `REDIS_URL`, `CORS_ORIGINS`, `COOKIE_SECURE=true` (prod), `APP_ENV=production`.
Optional: `SENTRY_DSN`, `LOG_JSON`, `STEAM_API_KEY` (official mode), `COINBASE_*`.

## Remaining work (next increments)
Done in beta.2: ✅ email provider · ✅ Steam official mode · ✅ Redis session state +
webhook race · ✅ cancel/reactivate · ✅ metrics · ✅ coverage gate · ✅ app pages
(/accounts /sessions /games /logs /support /onboarding) + Steam-art showcase.

Still open:
1. **Core feature decision (Phase 5):** real owner-consented official session adapter
   (real worker jobs end-to-end, ban-gating) **or** keep demo + audit every UI "Demo" label.
2. **Frontend polish:** adopt the `ui-kit` inside the *existing* dashboard/admin (still
   inline), split admin into sub-routes, Radix focus-trap modal for Steam-Guard, wire
   command-palette search, finish i18n strings inside dashboard/admin/billing bodies.
3. **Billing:** Stripe (card) provider, invoices/receipts, refund execution + admin UI.
4. **Steam official:** background refresh job; real game-icon hashes surfaced in UI.
5. **Observability depth:** OTel traces; frontend client-error reporting to Sentry.
6. **QA:** wire `smoke-qa.mjs`/Playwright into CI against an ephemeral stack; backup
   sidecar + a recorded restore rehearsal (see BACKUPS.md).

## Manual QA checklist (owner)
1. Open landing `/`.
2. Register a user.
3. (When built) complete onboarding.
4. Add a Steam account (demo, ownership attested).
5. Refresh Steam profile → avatar shows (Steam CDN).
6. Refresh owned games → **game images render**, broken ones fall back to gradient tiles.
7. Select games.
8. Start/stop a **demo** session; confirm status + event log update.
9. Open billing; confirm plan + limits.
10. Log in as admin; open a user detail drawer.
11. Check audit logs reflect actions.
12. Resize to mobile; confirm layout holds.
13. `docker compose up --build`; confirm health + migrations.
