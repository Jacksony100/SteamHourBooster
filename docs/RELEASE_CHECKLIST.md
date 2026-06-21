# Release Checklist

This checklist is the required gate before tagging a DeckPilot demo/beta release.

## One-command Local Gate

Linux/macOS/Git Bash:

```bash
./scripts/release-check.sh
```

Windows PowerShell:

```powershell
.\scripts\release-check.ps1
```

Docker image builds are optional in the default script because they require a running Docker daemon. To include them:

```bash
RUN_DOCKER_BUILD=1 ./scripts/release-check.sh
```

```powershell
$env:RUN_DOCKER_BUILD = "1"
.\scripts\release-check.ps1
```

## API Gates

```bash
cd apps/api
python -m ruff check .
python -m pytest -q
python -m pip_audit -r requirements.txt
```

Required result: all pass. Do not ship with high or critical dependency findings unless a documented exception exists.

## Web Gates

```bash
cd apps/web
npm run lint
npm run typecheck
rm -rf .next
npm run build
npm audit --audit-level=high
grep -R "http://localhost:8000" .next/static .next/server || true
```

Required result: lint/typecheck/build/audit pass and no production browser output calls `http://localhost:8000`.

## Docker Gates

```bash
docker compose -f docker-compose.yml config
docker compose -f docker-compose.yml build api worker web
docker compose -f docker-compose.yml up -d
```

Required result: Compose config renders, images build, and services become healthy.

## Smoke QA

With API and web running:

```bash
cd apps/web
npm run qa:smoke
```

Manual checks:

- Landing opens.
- Terms, Privacy, Security, and Status pages open.
- Theme and language toggles work.
- Anonymous protected routes redirect to `/login`.
- Register works.
- Login works.
- Dashboard renders after refresh.
- CSRF-protected logout works.
- Demo Steam account flow is clearly labeled.
- Billing plans load.
- Checkout is server-provider managed and never grants access on redirect alone.
- Admin routes are hidden/blocked for non-admin users.
- Settings export/delete/security controls render.
- Mobile width around 390px has no horizontal overflow on landing and app screens.

## Security Gates

- `APP_ENV=production` rejects weak/default secrets.
- `COOKIE_SECURE=true` is required in production.
- `COOKIE_SAMESITE` is `lax`, `strict`, or `none`; `none` requires secure cookies.
- `BILLING_PROVIDER=mock` is forbidden in production.
- Checkout requests reject client-supplied provider fields.
- Mock webhook is hidden in production.
- Provider mismatch webhooks do not mutate payments.
- Invalid or missing real-provider webhook signatures do not activate subscriptions.
- Coinbase production mode requires API and webhook secrets.
- SQLite is forbidden in production.
- Wildcard CORS is forbidden in production.
- `STEAM_TEST_MODE=true` in production requires `ALLOW_DEMO_MODE_IN_PRODUCTION=true`.
- Demo mode UI banner is visible on landing and app screens.
- Real Steam sessions are not claimed as enabled unless a safe, reviewed adapter exists.
- Password reset request responses are generic.
- Data export does not include password hashes, encrypted credentials, token hashes, cookies, or CSRF values.

## Deployment Gates

- `/healthz` returns `200`.
- `/readyz` returns `200` before traffic is routed.
- Production logs are collected for API, worker, web, PostgreSQL, and Redis.
- PostgreSQL backup job is configured and restore has been rehearsed.
- Rollback image/tag is known and available.

## Rollback Plan

1. Disable checkout or route billing webhooks to maintenance handling if payment integrity is affected.
2. Stop worker containers gracefully so active demo sessions can mark stopped/error.
3. Re-deploy the previous verified API, worker, and web images.
4. Run `python -m alembic current` and confirm database revision compatibility.
5. Check `/readyz`, admin audit logs, billing events, and worker logs.

## Honest Release State

If `STEAM_TEST_MODE=true` or `/api/v1/system/mode` reports `real_steam_enabled=false`, the release is a demo/beta candidate only. Do not market it as a paid production Steam runtime.
