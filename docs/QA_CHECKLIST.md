# QA Checklist

## Automated (CI, all green)
- **API:** 81 tests, `--cov-fail-under=75` (current ~84%): auth, CSRF (positive + negative),
  account ownership (cross-user 404), admin guard, plan limits, billing webhook
  verified/unverified + idempotency + cancel/reactivate, email recovery (outbox),
  session lifecycle idempotency + cross-instance runtime, Steam data (CDN URLs,
  ownership, official-mode mapping), security headers, metrics, config validation, seed.
- **Legacy:** 16 tests.
- **Web:** `npm run lint` + `npm run typecheck` + `npm run build` (all routes compile).
- **CI also:** ruff, pip-audit, npm audit, docker config validation, docker image builds.

## Coverage gaps still open
- No browser E2E in CI (needs a running stack). The `apps/web/scripts/smoke-qa.mjs`
  Playwright harness exists and now matches a seedable demo user (`SEED_DEMO_USER=true`),
  but is not wired into CI.
- No load/concurrency test for the webhook idempotency race or session start race
  (logic is hardened; tests are single-threaded).

## Manual QA (run before a closed-beta invite round)
1. `docker compose up --build` → all services healthy; migrations applied.
2. Open `/` (landing) — premium dark-glass, electric-blue brand, fonts loaded.
3. Register a new user → lands in dashboard.
4. `/onboarding` — four guided steps render with working CTAs.
5. `/accounts` — add a demo account; SteamAvatar + status render; "Refresh" works.
6. `/games` — pick the account; **game artwork loads from Steam CDN**; break a URL → gradient fallback; "Refresh Steam data" works.
7. Select games (dashboard) → start a **demo** session → `/sessions` shows it running → stop it.
8. `/logs` — session events timeline populates.
9. `/billing` — plan + limits; cancel → "cancels at period end"; reactivate.
10. Password reset request (user with email) → check the mailer outbox/console for the link (or real email if SMTP configured).
11. Log in as `admin` → `/admin` overview, user drawer, audit logs.
12. Resize to mobile → sidebar collapses, cards stack, no overflow.
13. `/metrics` returns Prometheus text; logs are structured JSON in prod mode.
14. Switch language (RU/DE/ZH) → nav + auth localized.

## Sign-off gates (see BETA_READINESS.md §"What you must NOT promise")
- Steam session activity is **demo** — label it; don't promise real hours.
- Payments default to mock; Coinbase untested live — don't take real money until verified.
- Email recovery only delivers when `EMAIL_PROVIDER=smtp` is configured.
