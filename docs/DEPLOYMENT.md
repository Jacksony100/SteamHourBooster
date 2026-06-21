# Deployment

The supported deployment path is Docker Compose with separate web, API, worker, PostgreSQL, and Redis services.

## Prerequisites

- Docker Engine or Docker Desktop.
- A production `.env` created from `.env.example`.
- Generated `SECRET_KEY` and `ENCRYPTION_KEY`.
- DNS/TLS handled by a reverse proxy or hosting platform.

## Local Docker

```bash
cp .env.example .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
docker compose up --build
```

Set a long random `SECRET_KEY` and use the generated value as `ENCRYPTION_KEY` before starting the stack.

Open:

- Web: `http://localhost:3000`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

## Server Deployment

1. Copy the repository to the server.
2. Create `.env` from `.env.example`.
3. Replace all default secrets.
4. Set `APP_ENV=production`.
5. Set public URLs and same-origin API routing:

```env
WEB_BASE_URL=https://your-domain.example
API_BASE_URL=https://your-domain.example
INTERNAL_API_URL=http://api:8000/api/v1
INTERNAL_API_ORIGIN=http://api:8000
NEXT_PUBLIC_API_BASE_PATH=/api/v1
CORS_ORIGINS=https://your-domain.example
SESSION_COOKIE_NAME=deckpilot_session
CSRF_COOKIE_NAME=deckpilot_csrf
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
STEAM_INTEGRATION_MODE=demo
ALLOW_DEMO_MODE_IN_PRODUCTION=true
```

6. Start:

```bash
docker compose up -d --build
```

7. Check health:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
curl http://localhost:3000
```

## Migrations

The API service command runs migrations before startup:

```bash
python -m alembic upgrade head
python -m app.seed
```

For manual migration:

```bash
docker compose run --rm api python -m alembic upgrade head
```

## Reverse Proxy

Terminate TLS at a reverse proxy such as Caddy, Nginx, Traefik, or a managed platform.

Recommended routing:

- `/` -> web service on port `3000`;
- `/api/*` -> API service on port `8000`;
- `/docs` -> API service on port `8000` only if public API docs are intended.

The browser app defaults to relative `/api/v1` requests. Do not bake internal Docker hosts or localhost URLs into `NEXT_PUBLIC_*` variables.

## Vercel Frontend Deployment

Vercel is supported for the Next.js frontend in `apps/web`.

Recommended project settings:

- Root Directory: `apps/web`
- Framework Preset: Next.js
- Install Command: `npm ci`
- Build Command: `npm run build`

Required environment variables when the FastAPI backend is deployed elsewhere:

```env
NEXT_PUBLIC_API_BASE_PATH=/api/v1
INTERNAL_API_ORIGIN=https://api.your-domain.example
INTERNAL_API_URL=https://api.your-domain.example/api/v1
```

If these backend variables are missing on Vercel, landing/legal pages still build, but auth/dashboard/billing/settings cannot complete API requests. Deploy the API, PostgreSQL, Redis, and worker on a server or container platform before enabling real users.

## Backups

PostgreSQL data lives in the `postgres-data` volume by default. For production:

- use managed PostgreSQL when possible;
- schedule encrypted backups;
- test restores;
- restrict direct database access.

Example Docker backup:

```bash
docker compose exec postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > deckpilot-backup.sql
gpg -c deckpilot-backup.sql
```

Example restore rehearsal into a temporary database:

```bash
docker compose exec postgres createdb -U "$POSTGRES_USER" deckpilot_restore_test
cat deckpilot-backup.sql | docker compose exec -T postgres psql -U "$POSTGRES_USER" deckpilot_restore_test
```

Document the last successful restore test date before accepting paid users.

## Payment Provider

Development uses `BILLING_PROVIDER=mock`. Before real checkout:

- configure provider keys through environment;
- configure webhook endpoint;
- verify webhook signatures;
- test idempotency;
- keep redirect pages informational only.

Production refuses to start with `BILLING_PROVIDER=mock`. Public checkout must use a real configured provider, and subscriptions are activated only from verified provider webhooks or audited admin actions.

## Steam Mode

The first release-safe mode is `STEAM_INTEGRATION_MODE=demo`. It does not collect Steam passwords and uses simulated sessions/games for preview. If you deploy demo mode with `APP_ENV=production`, set `ALLOW_DEMO_MODE_IN_PRODUCTION=true` and label the product as demo/beta.

`STEAM_INTEGRATION_MODE=official` must be configured only for official Steam/OpenID/Web API style linking. Until that is implemented and reviewed, official mode fails closed with clear unavailable responses.

## Healthchecks

Compose includes healthchecks for PostgreSQL, Redis, API, and web. Worker depends on Redis and API startup.

API endpoints:

- `/healthz`: liveness; the process is running.
- `/readyz`: readiness; database is checked in every environment and Redis is checked in production.
- `/health/live` and `/health/ready`: aliases for platforms that prefer nested health paths.

Do not route production traffic to a new release until readiness returns `200`.

## Observability

Minimum beta operations:

- collect API, worker, web, PostgreSQL, and Redis container logs;
- alert on `/readyz` failures, worker exits, Redis restarts, and repeated billing webhook failures;
- do not log passwords, Steam credentials, Steam Guard codes, cookies, CSRF tokens, provider secrets, or API keys;
- connect Sentry/OpenTelemetry before paid public launch if available in the hosting environment.

## Rate Limiting

`APP_ENV=production` requires Redis to be available for rate-limited routes. The API fails closed if Redis cannot be reached, instead of silently falling back to process memory. Development and tests may use in-memory buckets for deterministic local runs.

## Troubleshooting

- If Docker cannot pull images, confirm the daemon is running.
- If web cannot call API, check the `/api/*` reverse proxy, `NEXT_PUBLIC_API_BASE_PATH`, and `CORS_ORIGINS`.
- If auth cookies do not persist in production, check HTTPS, cookie domain, and proxy headers.
- If worker jobs do not run, check Redis health and worker logs.
