# Security

This document covers the SaaS 2.0 application. The preserved Flask app under `legacy/flask` is not the production target.

## Safety Scope

DeckPilot is a transparent account/session manager for accounts owned by the user. Do not add platform-circumvention features, hidden automation, network-routing evasion, fingerprint manipulation, credential harvesting, or mass-abuse workflows.

## Secrets

Required secret-like values:

- `SECRET_KEY`: session token signing secret, at least 32 characters.
- `ENCRYPTION_KEY`: Fernet key for encrypted Steam credentials.
- `COINBASE_API_KEY`: optional provider key.
- `COINBASE_WEBHOOK_SECRET`: optional provider webhook secret.
- `ADMIN_PASSWORD`: initial admin seed password.

Never commit:

- `.env`;
- database files;
- encryption keys;
- logs;
- generated local state;
- provider secrets.

## Authentication

- Passwords are hashed with passlib/bcrypt.
- Session tokens are stored in HTTP-only `deckpilot_session` cookies.
- Session JWTs contain a server-side `sid`; the API accepts them only when a matching, non-revoked `user_sessions` row exists.
- CSRF token is stored in `deckpilot_csrf` and must be sent in `X-CSRF-Token` for unsafe authenticated browser requests.
- Login, registration, password reset, checkout, and session start/stop routes are rate-limited.
- Failed logins are audited without passwords.
- Password reset tokens are stored only as SHA-256 hashes, expire after 30 minutes, are single-use, and revoke active web sessions after a successful reset.
- Email verification tokens are stored only as hashes and never returned from production-facing responses.
- Users can export non-secret account data and delete their workspace account from settings.

## Authorization

- `current_user` rejects missing, invalid, and banned users.
- `admin_user` guards all `/api/v1/admin/*` routes.
- Account, game, risk/status, and session routes enforce owner-only access.
- Admin self-demotion requires explicit confirmation in the backend.

## Credential Storage

Demo mode does not require Steam passwords. Legacy/test password fields are retained only for compatibility and are rejected in production or official integration mode. Steam account identifiers and any compatibility credentials are encrypted with Fernet through `ENCRYPTION_KEY`.

Do not log:

- application passwords;
- Steam passwords;
- Steam Guard codes;
- API keys;
- session tokens;
- encryption keys;
- Authorization headers.

## Billing Security

- Checkout creates a pending payment only.
- Checkout provider is selected only by server-side configuration.
- Client payloads cannot choose or override billing providers.
- Mock billing is allowed only in development/test and is rejected in production.
- Redirects never grant subscription access.
- Webhooks must be verified and idempotent before payment state transitions.
- Webhooks from one provider cannot mutate another provider's payment.
- Unverified provider events can be stored for audit but never activate subscriptions.
- Admin subscription overrides are audited.
- Lifetime checkout is disabled by default.

## Session Security

- Browser sessions are tracked in `user_sessions`; logout and settings-based revocation invalidate the server-side session row.
- `STEAM_INTEGRATION_MODE=demo` uses simulated, clearly labeled account/session behavior.
- `STEAM_INTEGRATION_MODE=official` must use official Steam/OpenID/Web API style flows only; if it is not configured, linking and sessions fail closed with a controlled error.
- `SessionManager` owns start/stop/heartbeat lifecycle.
- Start and stop are idempotent.
- Active session limits are enforced through billing entitlements.
- Session events are written for sensitive lifecycle changes.
- API and worker shutdown paths close active adapter clients gracefully.

## Network

- Do not disable TLS verification.
- Provider and integration calls must use explicit timeouts.
- External error details should be normalized before returning to users.

## Headers And Cookies

Production deployments should terminate HTTPS at a reverse proxy or managed platform. In production mode cookies are configured as secure where applicable. The API temporarily accepts legacy `shb_session` and `shb_csrf` cookies for migration, but new logins issue only `deckpilot_*` cookies.

Recommended proxy headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- a CSP tuned to the final deployed frontend and payment provider

## Dependency Audits

Run:

```bash
python -m pip_audit -r apps/api/requirements.txt
cd apps/web && npm audit --audit-level=high
```

CI runs dependency audit checks for the API, web app, and preserved legacy Flask app.

## Operational Checklist

- Rotate all default secrets before deployment.
- Restrict database and Redis network access.
- Encrypt and test database backups.
- Review admin users regularly.
- Review audit logs for billing and role changes.
- Keep dependencies pinned and updated through Dependabot or an equivalent process.
