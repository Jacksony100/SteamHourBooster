# Observability

## Structured logging
`apps/api/app/core/observability.py` configures a single stdout handler at startup
(`configure_logging`). In production (or when `LOG_JSON=true`) logs are emitted as
single-line JSON; in dev/test they are plain text.

Each log line carries the current **request id** (correlation id). Sensitive keys
(`password`, `secret`, `token`, `api_key`, `authorization`, `encryption_key`,
`steam_guard_code`, `auth_code`, `shared_secret`) are never serialized from
structured extras.

## Request context / access logs
`RequestContextMiddleware` (`apps/api/app/core/middleware.py`):
- Generates a request id, or reuses a caller-supplied `X-Request-ID` (≤64 chars).
- Exposes it on every response as `X-Request-ID`.
- Emits exactly one access log line per request: `METHOD path -> status (Nms)` with
  structured fields `{method, path, status, duration_ms, client}`.

## Error reporting (Sentry, optional)
`init_sentry` activates Sentry only when `SENTRY_DSN` is set **and** `sentry-sdk`
is installed; otherwise it is a no-op (the service runs identically without it).
`send_default_pii=False`. Configure with:

```
SENTRY_DSN=https://...ingest.sentry.io/...
SENTRY_TRACES_SAMPLE_RATE=0.1
```

To enable, add `sentry-sdk` to `apps/api/requirements.txt`.

## Unhandled errors
A global exception handler logs full server-side detail and returns a generic
`{"detail": "Internal server error"}` in production (full type/message in dev). The
readiness probe (`/readyz`) no longer leaks raw driver exceptions in production.

## Health endpoints
- `/health`, `/healthz`, `/health/live` — liveness.
- `/readyz`, `/health/ready` — readiness (DB always; Redis in production).

## Frontend
- `app/error.tsx`, `app/not-found.tsx`, `app/loading.tsx` provide user-facing
  error/empty/loading states.
- A client error-reporting hook can be wired to the same Sentry project (TODO).

## Env vars
| Var | Default | Meaning |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Root log level |
| `LOG_JSON` | `false` | Force JSON logs outside production |
| `SENTRY_DSN` | (empty) | Enable error tracking |
| `SENTRY_TRACES_SAMPLE_RATE` | `0.0` | Trace sampling |

## Not yet wired (TODO)
- Metrics endpoint (Prometheus) / OpenTelemetry traces.
- Log shipping/retention config (operator concern; see DEPLOYMENT.md).
- Frontend client-error reporting integration.
