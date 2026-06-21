# DeckPilot RC Report

Generated: 2026-06-16T12:12:18+03:00

Commit under test: `3c749dd`

## Verdict

READY FOR DEMO/CLOSED-BETA RC.

NOT READY FOR PAID PUBLIC LAUNCH until real payment-provider credentials, transactional email delivery, production observability, and backup restore rehearsal are completed.

## Automated Gates

| Gate | Result | Notes |
| --- | --- | --- |
| API lint | PASS | `python -m ruff check .` |
| API tests | PASS | `python -m pytest -q`: 58 passed, 1 Starlette/httpx deprecation warning |
| API dependency audit | PASS | `python -m pip_audit -r requirements.txt`: no known vulnerabilities |
| Web install | PASS | `npm ci` |
| Web lint | PASS | `npm run lint` |
| Web typecheck | PASS | `npm run typecheck` |
| Web build | PASS | `npm run build`, 18 routes generated |
| Web dependency audit | PASS | `npm audit --audit-level=high`: 0 vulnerabilities |
| Compose config | PASS | `docker compose -f docker-compose.yml config --quiet` |
| API Docker image | PASS | `docker build -f docker/api.Dockerfile . -t deckpilot-api:rc` |
| Worker Docker image | PASS | `docker build -f docker/worker.Dockerfile . -t deckpilot-worker:rc` |
| Web Docker image | PASS | `docker build -f docker/web.Dockerfile . -t deckpilot-web:rc` |
| Production bundle localhost audit | PASS | no `http://localhost:8000` in `.next/static` or `.next/server` |

## Security/Scope Audit

| Check | Result |
| --- | --- |
| Client cannot choose billing provider | PASS |
| Mock billing rejected in production settings | PASS |
| Mock webhook hidden in production | PASS |
| Invalid provider signature does not activate subscription | PASS |
| Password reset tokens hashed, expiring, single-use | PASS |
| Browser sessions revocable server-side | PASS |
| Steam integration release mode explicit | PASS |
| Demo mode does not require Steam password | PASS |
| Production rejects password-based Steam credential submission | PASS |
| Trust pages exist (`/terms`, `/privacy`, `/security`, `/status`) | PASS |
| Liveness/readiness endpoints exist | PASS |

## Known Risks

| Category | Risk | Launch Class |
| --- | --- | --- |
| Email | Password reset and email verification primitives exist, but no transactional email provider is wired yet. | Beta acceptable, paid launch blocker |
| Payments | Coinbase abstraction exists, but production credentials/signed webhook fixtures must be verified against a real provider account. | Paid launch blocker |
| Steam | Release mode is demo/official-gated; official linking is not configured. | Beta acceptable if labeled demo |
| Observability | Health endpoints and docs exist, but Sentry/OpenTelemetry/log aggregation are not connected. | Beta acceptable, paid launch blocker |
| Backups | Backup/restore process is documented, but no restore rehearsal has been recorded in this repo. | Paid launch blocker |
| Legacy | Old Flask prototype is preserved under `legacy/` for reference and migration history. | Beta acceptable |

## Manual QA Checklist

- Register user.
- Login/logout.
- Confirm anonymous `/dashboard`, `/billing`, `/settings`, and `/admin` redirect correctly.
- Verify CSRF-protected logout/delete/revoke actions fail without CSRF and pass with CSRF.
- Open dashboard and confirm launch checklist, empty states, demo banner, account add form, games selector, session panel, and activity log.
- Add a demo Steam account with ownership attestation.
- Select games and start/stop a demo session when plan limits allow.
- Open billing and confirm plan cards, current plan, disabled lifetime checkout, payment history, and pending/success/failed pages.
- Confirm checkout request does not expose provider selection.
- Login as admin seed user, open admin overview/users/detail drawer/payments/audit.
- Confirm admin dangerous actions show confirmation and create audit events.
- Open settings and verify email field, session list/revoke, export JSON, and delete confirmation.
- Check 390px mobile layout for landing, dashboard, billing, settings, and admin.

## Rollback Plan

1. Disable checkout at the provider or set the application to maintenance mode if billing integrity is affected.
2. Stop worker containers gracefully and let sessions record stopped/error state.
3. Deploy the previous verified `api`, `worker`, and `web` images.
4. Run `python -m alembic current` and confirm database revision compatibility.
5. Check `/readyz`, billing events, admin audit logs, and worker logs.
6. If database restore is required, restore the latest encrypted PostgreSQL backup into a temporary database first, validate, then promote.
