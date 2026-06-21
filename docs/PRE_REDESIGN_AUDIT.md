# Pre-Redesign Audit

Audit source: `Jacksony100/SteamHourBooster` remote snapshot `3c749dd` (`main`).

Local workspace note: the current workspace directory contained only an empty git repository with no commits and no remote. The code audit below is based on a shallow temporary clone of the public GitHub repository requested in the task.

## Executive summary

Steam Hour Booster is a compact Flask prototype, not a production-ready SaaS foundation. The application combines authentication, subscription checks, Steam account credential storage, Steam client runtime management, background activity loops, admin operations, Steam Web API calls, and billing stubs in a single `main.py` file.

The highest-risk issue is secret handling. User passwords are stored with reversible Fernet encryption instead of password hashing. Steam usernames, passwords, and `shared_secret` values are also reversibly encrypted with the same local `key.key` approach, and encrypted Steam credentials are logged. If the database and key leak together, user passwords and Steam credentials are recoverable.

The second highest-risk issue is transport security. The app globally disables TLS certificate verification and also calls Steam API endpoints with `verify=False`. This creates avoidable man-in-the-middle risk for API traffic and any library code affected by the modified default SSL context.

The third highest-risk issue is the runtime model. Long-lived Steam clients and activity loops live inside global in-memory process state (`clients = {}`), while gevent monkey patching, Flask threaded mode, and `ThreadPoolExecutor` are mixed in the same process. This cannot be scaled, safely restarted, observed, or recovered in a modern SaaS deployment.

The current UI is functional prototype UI: Bootstrap tables, inline CSS and JavaScript, weak status modeling, no onboarding, no dashboard metrics, no billing state machine, no loading/empty/error design system, and no mobile-first product experience.

Recommendation: do not incrementally patch this code into production. Freeze unsafe behavior, extract requirements, and rebuild around a typed API, PostgreSQL migrations, proper auth, encrypted secret vaulting, a job queue, auditable account/session lifecycle, rate limits, tests, and a modern frontend.

## Current architecture

### Repository structure

- `main.py`: monolithic Flask application, database schema creation, auth, subscriptions, Steam account management, Steam login, activity loop, Steam API calls, admin panel, and billing stub.
- `auth.py`: separate legacy auth helper using Werkzeug password hashing, but it is not used by `main.py`. It defines a conflicting `users` table shape.
- `generate_key.py`: creates `key.key` for Fernet encryption.
- `templates/*.html`: Jinja templates with Bootstrap CDN usage, inline styles, inline JavaScript, tables, modals, and forms.
- `static/style.css`: unused or mostly disconnected CSS.
- `static/script.js`: unused loading helper expecting a `#loading` element.
- `screenshots/*.jpg`: UI screenshots.
- `requirements.txt`: pinned Flask/gevent/cryptography/steam/requests dependencies.

### Runtime model

- Flask app is created directly in module scope.
- SQLite database path is hardcoded as `steam_accounts.db`.
- Fernet key is read from a local `key.key` file at import time.
- Flask `secret_key` is generated with `os.urandom(24).hex()` on each process start.
- Steam clients are held in a module-level dictionary keyed by decrypted Steam username.
- `ThreadPoolExecutor(max_workers=5)` runs `client.run_forever`.
- gevent monkey patching is enabled globally.
- Activity loops are spawned as gevent greenlets and call `client.games_played(game_ids)` every 60 seconds.
- The same web process handles user HTTP traffic, admin actions, Steam client sessions, and background loops.

### Data model

`main.py` creates tables directly with `CREATE TABLE IF NOT EXISTS`:

- `users`: username, reversible encrypted password, subscription end, admin flag, banned flag, last IP, last seen.
- `accounts`: reversible encrypted Steam username, password, shared secret, SteamID64, user ID.
- `games`: Steam app ID and game name.
- `account_games`: many-to-many join between accounts and games.

No migration system, schema versioning, seed data strategy, indexes, timestamps, audit records, payment records, job records, secret metadata, or retention policy exist.

## Critical risks

1. Reversible user password storage

   `main.py` encrypts app user passwords with Fernet and decrypts them during login. Passwords must be hashed with Argon2id, bcrypt, or scrypt. Reversible password storage is a critical breach impact multiplier.

2. Reversible Steam credential storage

   Steam login, password, and `shared_secret` values are stored in SQLite using the same Fernet key file pattern. This makes the database and local key a single point of compromise. The product should avoid storing Steam passwords and should not collect Steam Guard shared secrets.

3. TLS verification disabled

   The app sets `ssl._create_default_https_context = ssl._create_unverified_context` and uses `requests.get(..., verify=False)` for Steam API calls. This must be removed before any real deployment.

4. Secrets logged

   `api_add_account` logs encrypted Steam usernames and passwords. Encrypted secrets are still secrets because they can be decrypted if the Fernet key is available, and logs tend to be widely retained and exported.

5. Missing CSRF protection

   Login, registration, billing, admin POSTs, and JSON mutation endpoints rely on cookie sessions without CSRF tokens. Admin privilege changes are especially exposed.

6. Missing rate limits and abuse controls

   Login, registration, Steam login, game fetching, ban checks, and account creation have no rate limits, lockouts, quotas, CAPTCHA, or anomaly detection.

7. Global in-memory Steam clients

   Steam sessions disappear on process restart, cannot be distributed across workers, cannot be reconciled after crashes, and are not guarded by persistent job state or distributed locks.

8. Unsafe mixed concurrency

   gevent monkey patching, Flask threaded mode, Steam client loops, and `ThreadPoolExecutor` are mixed without lifecycle management. This risks stuck sessions, leaked greenlets, locked SQLite writes, and inconsistent state.

9. Admin panel lacks production controls

   Admin state comes from session data and a simple `is_admin` flag. There is no RBAC, no admin re-authentication, no audit log, no CSRF protection, no pagination, no confirmation flows, and no two-person control for sensitive actions.

10. Billing is incomplete and broken

   `create_crypto_charge` references undefined `COINBASE_API_KEY` and `COINBASE_CHARGE_URL`. The billing form posts `subscription_duration`, while the backend expects `plan` and `payment_method`. There are no payment records, webhook verification, idempotency keys, receipts, or subscription state transitions.

## UX/UI problems

- The primary interface is a Bootstrap table with action buttons in every row. It does not scale to many accounts, many games, or mobile screens.
- UI logic is mostly inline inside `templates/index.html`; static assets are not coherently used.
- `templates/index.html` mixes layout, translation dictionaries, API calls, modals, status rendering, and mutation logic in one file.
- The product has no dashboard metrics such as active sessions, accounts needing attention, failed logins, queued jobs, API errors, active subscription, usage limits, or security warnings.
- Account status is only `online` or `offline`; there are no states for connecting, Steam Guard required, paused, rate-limited, failed, degraded, stopping, syncing games, or requires user action.
- The game selector is a raw checkbox grid without search, filters, virtualized list, selected count, recommended limits, last synced time, or confirmation copy.
- The app asks for Steam username, password, and optional `shared_secret` up front. This is a poor trust experience and should be replaced with a safer account/session flow.
- There is no onboarding path that explains safe use, ownership requirements, account risk, limits, data storage, and how sessions work.
- Billing UX is a prototype stub. There are no pricing cards, current plan state, invoice history, payment failure states, cancellation flow, or upgrade/downgrade UX.
- Empty states are missing for no accounts, no games, no active sessions, no subscription history, failed game sync, and missing SteamID64.
- Loading states are mostly absent. The unused `static/script.js` expects an element that templates do not provide.
- Error states are generic modal popups. There is no field-level validation, retry guidance, or persistent activity log.
- The UI is not mobile-first. Tables and dense row action buttons will be hard to use on small screens.
- Inline `innerHTML` rendering with API data creates stored or reflected XSS risk if a Steam account name, game name, or server error contains markup.
- External CDN assets are used directly. Font Awesome has a fake integrity value (`sha512-...`), which is not a real SRI hash.
- Login and registration forms are minimal and incomplete: no password requirements, no confirm password, no terms acceptance, no forgot password, no MFA, no device/session visibility.

## Backend problems

- `main.py` is a monolith that mixes routes, database access, security, billing, Steam integration, background jobs, and templates.
- There is no application factory, blueprint/module separation, dependency injection, or testable service layer.
- SQLite is used directly from many functions with inconsistent connection patterns.
- `check_same_thread=False` is used as a workaround for concurrency pressure instead of designing a safe persistence layer.
- Schema is created by `CREATE TABLE IF NOT EXISTS`; there are no Alembic or equivalent migrations.
- There is no typed request/response contract. API payloads are ad hoc JSON objects.
- Many handlers assume `request.json` exists and contains expected keys; malformed input can raise exceptions.
- There is no centralized validation, normalization, or error response format.
- There is no centralized authorization policy beyond checking session and sometimes filtering by `user_id`.
- Background work has no durable jobs, retries, timeouts, cancellation records, idempotency, backoff, or dead-letter handling.
- There is no graceful worker lifecycle for Steam clients on deploy, shutdown, crash, or scale-out.
- Steam client login and long-running session logic run inside the same process as HTTP request handling.
- Logging is unstructured and contains sensitive account identifiers. There is no trace ID, request ID, job ID, or user-safe audit stream.
- No observability stack exists: no metrics, no health checks, no readiness checks, no distributed traces, no Sentry-style error reporting.
- Dependency versions are pinned but there is no dependency audit workflow, lockfile, Renovate/Dependabot setup, or CI scan.
- There is no Dockerfile, compose file, deployment configuration, or environment-specific settings.
- `auth.py` conflicts with `main.py` auth logic and is effectively dead or legacy code.

## Security problems

### Authentication and sessions

- App user passwords are reversibly encrypted instead of hashed.
- Password comparison decrypts stored passwords and compares plaintext strings.
- No password policy, breach-password check, lockout, MFA, email verification, password reset, or session revocation exists.
- Flask session secret changes on every restart, invalidating sessions and making multi-instance deployments impossible.
- Session cookie security flags are not configured explicitly (`Secure`, `HttpOnly`, `SameSite`, max age, rotation).
- Admin privileges are copied into the session at login and may become stale if role changes in the database.

### CSRF and request safety

- No CSRF framework or tokens are present.
- Admin POSTs can change subscription, ban state, and admin status without CSRF protection.
- JSON mutation endpoints are also unprotected from CSRF-style abuse in a cookie-auth app.
- No CORS policy is defined.

### Secrets and credentials

- Fernet key is a local file (`key.key`) and there is no rotation, envelope encryption, key ID, KMS/Vault integration, or per-secret metadata.
- User passwords, Steam usernames, Steam passwords, and Steam `shared_secret` values share the same broad encryption model.
- Encrypted Steam credentials are logged.
- Steam usernames are logged in plaintext during login, logout, farming, and error paths.
- Steam Guard codes are sent to the backend as plain request payloads and have no explicit short-lived handling policy.
- The app asks for `shared_secret`, which should not be part of the redesigned product.

### Transport and network

- TLS certificate verification is globally disabled.
- Steam Web API requests explicitly use `verify=False`.
- Coinbase request handling logs full error response text, which may contain sensitive diagnostic details.

### Authorization and access control

- Authorization is scattered across route handlers.
- Admin access is a single boolean with no role model or permission boundaries.
- There is no audit trail for who changed subscriptions, bans, roles, or account state.
- There is no defense against IDOR beyond repeated manual `user_id` filters. This pattern is easy to miss as the app grows.

### Abuse prevention

- No rate limiting for login, registration, Steam login attempts, account creation, game sync, ban checks, or admin actions.
- No per-user account caps, active session caps, game selection caps, or queue quotas.
- No anomaly detection, alerting, or automated stop condition when repeated Steam login failures occur.
- No IP/device/session history visible to users.

### Frontend security

- API data is rendered with `innerHTML` in multiple places.
- Modal content uses template strings and unsanitized message HTML.
- CDN resources are not consistently protected with real SRI hashes.

## Data model problems

- No migrations or schema versioning.
- No `created_at`, `updated_at`, `deleted_at`, or audit fields.
- No explicit indexes on lookup paths such as `accounts.user_id`, `account_games.account_id`, or `users.username` beyond the username uniqueness constraint.
- No organization/team model, which limits SaaS account management and billing.
- No payment, invoice, subscription plan, entitlement, or webhook event tables.
- No durable job/session tables for Steam connection attempts, activity sessions, game sync jobs, ban checks, or stop events.
- No account status model beyond inferred in-memory online/offline state.
- No consent/ownership attestation records for connected Steam accounts.
- No secret metadata such as key version, encrypted-at, rotated-at, last-used-at, or deletion status.
- No account-level risk state, failure counters, cooldowns, or user-facing warning records.
- No retention policy for `last_ip` or other personal data.
- No foreign key enforcement strategy. SQLite requires explicit `PRAGMA foreign_keys = ON`.
- `accounts` has no uniqueness constraint, but code catches `sqlite3.IntegrityError` as if duplicates were prevented.
- `auth.py` and `main.py` define incompatible user schemas, which would make future migrations error-prone.

## Proposed target architecture

### Product direction

Reframe the product as a legitimate Steam account/session manager for accounts owned by the user. The product should provide transparent session controls, account inventory, safety limits, logs, warnings, and user-controlled deletion. It should not promise hidden activity, platform-rule circumvention, Steam Guard circumvention, or artificial engagement.

### Frontend

- Next.js with TypeScript, or a comparable typed React stack.
- Design system based on accessible primitives such as Radix UI, shadcn/ui, or a custom component library.
- TanStack Query or equivalent for typed server state.
- Form validation with Zod or equivalent.
- Premium SaaS UI with dashboard, account list, session timeline, job/activity log, billing area, settings, and admin console.
- Mobile-first layouts that replace row-button tables with responsive list/detail views and bulk-safe actions.
- Explicit UI states for loading, empty, failed, retrying, paused, rate-limited, needs Steam Guard, connected, disconnected, and degraded.
- No inline JavaScript or inline CSS in templates.
- Escaped rendering by default; no direct `innerHTML` for untrusted content.

### Backend

- Python API service using FastAPI or a modern Flask app-factory structure. FastAPI is recommended for typed OpenAPI generation and request/response validation.
- Domain modules:
  - `auth`
  - `users`
  - `billing`
  - `steam_accounts`
  - `steam_sessions`
  - `games`
  - `jobs`
  - `admin`
  - `audit`
  - `notifications`
- SQLAlchemy 2.x ORM or SQLModel with PostgreSQL.
- Alembic migrations with reviewed migration files.
- Pydantic schemas for all API inputs and outputs.
- OpenAPI contract with generated TypeScript client.
- Centralized error model with request IDs.
- Centralized authorization policy and RBAC.
- Secure config via environment variables and typed settings.

### Secrets and auth

- Hash app user passwords with Argon2id or bcrypt.
- Use a stable `SECRET_KEY` from environment or a secret manager.
- Configure secure session cookies and CSRF protection.
- Add MFA support for app admin accounts.
- Do not store Steam Guard shared secrets.
- Avoid storing Steam passwords where possible. If a session flow requires sensitive credentials, handle them ephemerally and discard after use.
- If any Steam account secret must be stored, use envelope encryption with KMS/Vault, per-secret key metadata, rotation, access logging, and strict retention.
- Redact all secrets and sensitive identifiers from logs.

### Jobs and workers

- Move Steam connection/session work out of the web process.
- Use Redis plus Celery/RQ/Arq, or another durable queue, for background jobs.
- Persist job state in PostgreSQL.
- Use distributed locks per Steam account to prevent overlapping sessions.
- Add explicit job states: queued, running, waiting_for_user, rate_limited, stopping, stopped, failed, expired.
- Add timeouts, retries with backoff, cancellation, idempotency keys, and dead-letter handling.
- Add graceful shutdown hooks to stop sessions cleanly.

### Observability

- Structured JSON logs with request ID, user ID, account ID, job ID, and redaction.
- Metrics for login attempts, Steam connection failures, job duration, queue depth, active sessions, API latency, and error rates.
- Health and readiness endpoints.
- Sentry or equivalent error monitoring.
- OpenTelemetry traces across API, database, queue, and worker.
- User-facing audit/activity log for account/session changes.

### Billing

- Prefer Stripe/Paddle for SaaS billing unless crypto is an explicit business requirement.
- If crypto remains, implement signed webhook verification, payment records, idempotency, reconciliation, subscription state transitions, and clear risk/compliance review.
- Add tables for plans, subscriptions, payments, invoices, webhook events, and entitlements.
- Admin changes to billing entitlements must be audited.

### Safety and compliance controls

- Require user attestation that each connected Steam account is owned by them.
- Add clear warnings about Steam platform rules and account risk.
- Enforce conservative account, session, game, and API limits.
- Make session activity visible to the user with timestamps and stop controls.
- Add a global emergency stop and per-account stop.
- Avoid language that implies hidden automation, artificial engagement, or platform-rule circumvention in the product surface.
- Provide account deletion and secret deletion workflows.

## Work phases

### Phase 0 - Freeze and safety baseline

- Mark the current project as prototype-only.
- Disable or remove collection of `shared_secret`.
- Remove logging of encrypted and plaintext account identifiers.
- Remove `verify=False` and global SSL override.
- Add a security note to the README before any public deployment.
- Add a minimal test harness and static checks to prevent regressions during migration.

### Phase 1 - Product and compliance definition

- Define the legitimate account/session manager scope.
- Write terms, user warnings, ownership attestation, data retention, and abuse policy.
- Define allowed account/session limits.
- Define what Steam integration is permitted and what must not be automated.

### Phase 2 - New application skeleton

- Create backend app structure with typed config, database connection, migrations, and health checks.
- Create frontend app structure with TypeScript, design system, routing, auth shell, and API client generation.
- Add CI for linting, tests, type checks, dependency audit, and migration checks.

### Phase 3 - Identity, sessions, and security

- Implement user registration/login with hashed passwords.
- Implement secure cookies, CSRF protection, MFA-ready session model, password reset, and session/device management.
- Add RBAC and admin audit log.
- Add rate limits and lockouts for auth and mutation endpoints.

### Phase 4 - Data model and migration path

- Design PostgreSQL schema for users, accounts, sessions, jobs, games, billing, audit, and secrets metadata.
- Add Alembic migrations.
- Build one-way migration scripts from the SQLite prototype only for non-sensitive data where legally and technically appropriate.
- Do not migrate reversible user passwords into the new system. Force password reset.
- Do not migrate Steam passwords or shared secrets without explicit user re-consent.

### Phase 5 - Account/session manager

- Build account CRUD with ownership attestation and secret deletion.
- Build safe connection flow with ephemeral Steam Guard code handling.
- Persist account status separately from worker runtime state.
- Add job queue and worker lifecycle.
- Add session timeline, stop controls, cooldowns, and failure reasons.

### Phase 6 - Games and Steam API integration

- Implement owned-games sync with TLS verification enabled.
- Add typed Steam API client wrapper with retries, timeouts, rate limits, and redacted logs.
- Build searchable game selector with limits and clear selected state.
- Persist sync jobs and last sync status.

### Phase 7 - Billing and entitlements

- Implement real plan, subscription, payment, invoice, webhook, and entitlement records.
- Add billing UI: current plan, limits, payment status, invoices, cancellation, upgrade/downgrade.
- Add webhook verification and idempotency.
- Gate features through entitlements, not scattered decorators.

### Phase 8 - Admin, observability, and operations

- Build admin console with RBAC, search, pagination, confirmations, audit history, and admin re-authentication for sensitive changes.
- Add structured logs, metrics, tracing, alerts, health checks, and dashboards.
- Add runbooks for incident response, secret rotation, worker restarts, and emergency stops.

### Phase 9 - Premium UI redesign

- Build a polished dashboard-first interface.
- Add onboarding and trust-building security copy.
- Add responsive account cards/detail panels, activity timeline, job logs, billing pages, settings, and admin views.
- Add accessible loading, empty, error, warning, and success states.
- Perform accessibility, responsive, and visual QA.

### Phase 10 - Release hardening

- Run threat modeling.
- Run dependency scans, static analysis, and secrets scans.
- Run load tests for API and worker queues.
- Run privacy review for stored IPs and Steam account data.
- Prepare docs: setup, architecture, security model, data model, API, worker operations, billing operations, and admin runbook.

## Acceptance criteria

### Security

- App user passwords are hashed with Argon2id/bcrypt and never decrypted.
- No `verify=False` and no global TLS verification override remain.
- No Steam Guard shared secret collection exists.
- Secrets are not logged.
- Sensitive account secrets are absent or stored through KMS/Vault envelope encryption with key rotation metadata.
- CSRF protection covers browser-authenticated mutations.
- Rate limiting covers auth, Steam actions, billing, and admin changes.
- Admin actions require RBAC, are audited, and sensitive actions require re-authentication.
- Session cookies explicitly set `Secure`, `HttpOnly`, `SameSite`, expiration, and rotation behavior.
- A threat model exists and is reviewed before production launch.

### Backend

- Web requests do not run long-lived Steam sessions directly.
- Background work uses durable jobs with persistent state, retries, timeouts, and cancellation.
- PostgreSQL is used with migrations.
- API requests and responses are typed and validated.
- There is a generated OpenAPI contract and typed frontend client.
- All mutation endpoints return consistent error objects with request IDs.
- Health/readiness endpoints exist.
- Structured logs, metrics, traces, and error monitoring are configured.

### Data

- Schema includes users, accounts, account statuses, session jobs, games, account game preferences, billing, payments, webhook events, audit events, and secret metadata.
- Critical lookup columns are indexed.
- All sensitive data has retention and deletion behavior.
- SQLite prototype migration is documented and tested.
- User passwords and Steam credentials from the prototype are not blindly migrated.

### UX/UI

- First screen after login is a useful dashboard, not a raw table.
- Account states are explicit and actionable.
- Game selection supports search, filters, counts, and safe limits.
- Billing UI shows current plan, limits, invoices, and payment status.
- Onboarding explains allowed use, account ownership, risk, limits, and data handling.
- All major views have loading, empty, error, and success states.
- Mobile layouts are tested.
- Accessibility checks pass for keyboard navigation, color contrast, labels, and focus states.

### Testing

- Unit tests cover auth, authorization, validation, billing entitlement logic, and Steam API wrapper behavior.
- Integration tests cover account lifecycle, job lifecycle, billing webhook handling, admin changes, and CSRF enforcement.
- E2E tests cover onboarding, login, account add/remove, game sync, start/stop session, billing flow, and admin updates.
- Security tests include dependency audit, secrets scan, CSRF checks, rate-limit checks, and XSS regression tests.
- Worker lifecycle tests cover shutdown, cancellation, retries, duplicate job prevention, and crash recovery.

### Documentation

- README explains safe scope and local setup.
- Architecture documentation explains services, data model, job lifecycle, secrets model, and observability.
- API documentation is generated from OpenAPI.
- Admin runbook covers user support, billing corrections, emergency stop, and audit review.
- Security documentation covers threat model, secret rotation, data deletion, and incident response.

## What NOT to build for safety/compliance

- Do not build platform-rule circumvention systems.
- Do not build account-risk evasion or risk hiding.
- Do not build Steam Guard circumvention.
- Do not store or use Steam Guard `shared_secret` to avoid user participation.
- Do not hide activity from Steam or from the account owner.
- Do not sidestep Steam limits, rate limits, or platform safeguards.
- Do not create mass account automation, spam automation, account creation automation, credential stuffing, or scraping workflows.
- Do not market the product as guaranteed hour boosting, farming, or risk-free activity manipulation.
- Do not add network-routing evasion, fingerprint manipulation, headless evasion, CAPTCHA circumvention, or similar platform-rule circumvention.
- Do not keep user passwords or Steam passwords in reversible storage without a reviewed, explicit, narrowly scoped security design.
- Do not silently retry failed Steam logins in a way that can lock or endanger accounts.
- Do not run background sessions without visible user consent, logs, limits, and stop controls.
