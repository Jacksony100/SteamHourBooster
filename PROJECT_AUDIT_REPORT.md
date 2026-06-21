# SteamHourBooster — Project Audit Report

> **Audit date:** 2026-06-21
> **Auditor scope:** product/tech lead, backend/frontend architect, security auditor, UX/UI auditor, QA lead
> **Repository:** https://github.com/Jacksony100/SteamHourBooster (working branch `pre/backend-refactor`)
> **Framing:** legitimate account/session manager for **user-owned** Steam accounts. This report does **not** cover or recommend anti-fraud bypass, Steam Guard bypass, anti-detect, ban evasion, proxy-rotation evasion, or hidden automation.

---

## ⚠️ Important framing correction (read first)

The task brief describes "an old Flask/Gevent/SQLite project that needs to be reworked." **That is no longer what the repository contains.** The rework has largely **already happened**. The repo is now a monorepo branded **DeckPilot `2.0.0-beta.1`** containing three layers:

| Layer | Location | State |
|---|---|---|
| **New FastAPI backend** | `apps/api/` | Real, modular, tested (58 tests pass), the active product |
| **New Next.js 15 frontend** | `apps/web/` | Real, dark-glass SaaS UI, builds & runs |
| **Legacy Flask app (preserved)** | `legacy/flask/` | Already modularized + hardened; **still contains the only real Steam automation** |

So the practical question is not "should we rewrite the old Flask app?" (Option B in the brief is ~70% done) but **"is the new beta production-ready, and do its docs over-claim?"** This report answers that, audits both layers, and verifies the README/docs claims against the actual code.

**Methodology:** every finding below was read in source and cross-checked. Both test suites were executed (**58/58 API + 16/16 legacy passing**). README/CHANGELOG/docs security claims were individually verified against code (results in §8).

---

## 1. Executive Summary

**What it is.** DeckPilot is a dark-first SaaS dashboard for transparent management of user-owned Steam accounts: registration/login, subscriptions & billing, adding Steam accounts (encrypted), game selection, an activity-"session" lifecycle, ban/risk info display, and an admin control center with audit logs.

**Stage.** Genuine **beta / release candidate**, far beyond a prototype. FastAPI + SQLAlchemy + Alembic backend, Next.js 15 frontend, PostgreSQL + Redis + worker Docker Compose stack, a 6-job CI matrix, and ~16 docs files. Engineering quality of the *plumbing* is high and, in places (production-config validation, billing webhook verification, revocable sessions), better than many shipped products.

**Readiness.** As a **closed-beta / demo of the dashboard and account-management surface: ~75% ready.** As a **paid production product that actually delivers the headline feature (real Steam activity / "hour" accrual): ~35–40%** — because that feature is intentionally a **demo mock** in the new app.

**The single most important fact.** In `apps/api/` the Steam integration is a **pure mock** (`integrations/steam.py`, `sessions/adapters.py`): it returns fake `steamid64`/games/ban data and toggles an in-memory set. No real login, no real activity. The only working real automation lives in the **legacy** Flask app (`legacy/flask/.../steam_client_service.py`). The new SaaS therefore currently sells a dashboard around a feature that does nothing in the shipped build (this is by-design and openly documented, but it is the gating product gap).

**Main problems (headline).**
1. Core feature is a demo mock in the active app; real "official linking" is gated off and unimplemented.
2. **Zero in-application observability** (no logging, metrics, tracing, error tracking) — a true production blocker.
3. **No HTTP security headers** on the API (only CORS); no security headers on the web app either.
4. All Docker images **run as root**.
5. Email delivery is **stubbed** — password-reset / verification tokens are created but never sent, so account recovery is non-functional.
6. The advertised **Redis/RQ background worker is dead code**; "session" activation runs synchronously inline.
7. Repo hygiene: committed `.next/` build artifacts, `test.db`, and four `DeckPilot-*.zip` snapshots in the working tree.

**Verdict (short).** **Do not market this as a working "hour booster" yet** — the active build can't do it. You *can* ship a clearly-labeled **closed/demo beta** of the management dashboard now. Before any paid public launch: implement (or honestly remove) the core feature, add observability + email, drop root in containers, add security headers, and fix the scaling/worker gaps. See §15 for the precise gate list.

---

## 2. What Already Exists

Status legend: ✅ working · 🟡 partial/scaffold · 🧪 demo-mock-only · 🗄️ legacy-only.

| Capability | Where | Status | Notes |
|---|---|---|---|
| **Registration / login** | `apps/api/app/auth/{routes,service}.py` | ✅ | bcrypt hashing, JWT session token + DB-backed revocable session row, rate-limited, failed-login auditing |
| **Server-side session revocation** | `core/deps.py:28-42`, `auth/service.py` | ✅ | `user_sessions` row required & non-revoked on every request; banned users blocked |
| **CSRF protection** | `core/deps.py:46-53` | 🟡 | Double-submit cookie/header; works but token is unsigned & not session-bound (§8) |
| **Subscriptions & plans** | `billing/service.py:13-214`, `core/models.py:197-234` | ✅ | 5 plans (trial/starter/pro/ultra/lifetime), auto-trial, expiry, plan limits enforced |
| **Plan-limit enforcement** | `assert_account_limit` (`steam_accounts/service.py`), `assert_active_session_limit` (`sessions/manager.py:159`) | ✅ | Real choke points, `402` on breach |
| **Billing checkout + providers** | `billing/providers.py`, `billing/routes.py` | 🟡 | Provider abstraction (Mock + Coinbase); Coinbase HTTP checkout real; mock blocked in prod |
| **Webhook verification + idempotency** | `billing/providers.py:103-133`, `billing/service.py:282-302` | ✅ | Constant-time HMAC-SHA256 verify; unverified events never grant; unique `idempotency_key` dedup |
| **Add Steam accounts (encrypted)** | `steam_accounts/{routes,service}.py`, `core/security.py:54-65` | ✅ | Fernet-encrypted username+password; owner-scoped; Steam Guard never stored |
| **Game selection** | `games/routes.py`, `account_games` table | ✅ | Per-account selected games with unique constraint |
| **Steam API integration (login/games/ban)** | `integrations/steam.py` | 🧪 | **Mock**: fake steamid/games/ban payloads in demo mode; error otherwise |
| **Real hour-boost automation** | `legacy/flask/.../steam_client_service.py:36-133` | 🗄️ | **Real** `steam` lib login + `client.games_played()` loop — legacy only |
| **Session lifecycle (start/stop/heartbeat)** | `sessions/manager.py` | ✅/🧪 | Clean idempotent DB-persisted lifecycle, but drives the mock adapter |
| **Ban / risk info display** | `integrations/steam.py:32-47`, `BanCache` model | 🧪 | Data shape exists; values are mock |
| **Admin control center** | `admin/{routes,service}.py` | ✅ | Overview metrics, user search/filter, detail drawer, sub changes, ban/unban, force-stop, payments, audit |
| **Audit logging** | `audit/service.py`, `audit_logs` table | ✅ | All admin mutations + billing grants logged |
| **Payment "stub"** | Mock provider | ✅ | Functional simulated provider for dev/tests |
| **Themes / language** | `apps/web/components/theme-toggle.tsx`, `lib/i18n.ts` | 🟡 | 3 themes (next-themes) + 4-language catalog, but authenticated app is hardcoded English (§6) |
| **Frontend dashboard UI** | `apps/web/app`, `features/`, `components/` | ✅ | Real pages, dark-glass design system, modals, drawers, toasts, command palette |
| **Account security settings** | `features/settings/`, migration `005` | ✅ | Active sessions, data export, account deletion |
| **Legal/trust pages** | `app/{privacy,security,terms,status}` | ✅ | Present (hardcoded English) |
| **Health endpoints** | `app/main.py:55-87` | ✅ | `/health`, `/healthz`/`/health/live`, `/readyz`/`/health/ready` with DB+Redis checks |
| **Docs** | `docs/*` (16 files) | ✅ | Architecture, Security, Billing, Session Manager, Deployment, Roadmap, RC report, pre-redesign audit |
| **README** | `README.md` | ✅ | Accurate and candid about beta scope |
| **Migrations** | `apps/api/alembic/versions/001-005` | ✅ | Sequential, run on container start |
| **Tests** | `apps/api/tests/*` (58), `legacy/flask/tests/*` (16) | ✅ | All passing |
| **CI/CD** | `.github/workflows/ci.yml` | ✅ | lint + tests + pip-audit + npm-audit + docker build (6 jobs) |
| **Docker / Compose** | `docker/*`, `docker-compose*.yml` | ✅ | API/web/worker/postgres/redis with healthchecks |

---

## 3. What Is Missing

- **Real Steam integration** — the "official linking" path is gated (`steam_official_linking_enabled=false`) and unimplemented in the new app. The product's reason to exist is currently a mock.
- **Observability** — no application logging, no request/correlation IDs, no metrics (Prometheus/OTel), no error tracking (Sentry). `grep` finds zero `logging` usage in `apps/api/app`. **Production blocker.**
- **Transactional email** — password reset & email verification create hashed tokens but there is **no email provider**; recovery is non-functional (README is honest about this).
- **Working background worker** — the RQ enqueue branch in `sessions/manager.py:171-185` is unreachable (see §5). The `worker` container runs but has nothing to do.
- **Horizontal scalability** — the Steam adapter singleton is in-process/in-memory (`sessions/adapters.py:41,81-98`); multiple API workers or a separate worker break heartbeat/stop semantics.
- **Automated DB backups** — only manual `pg_dump`/restore documented; no scheduled job, no restore rehearsal.
- **TLS / reverse proxy in the deployment** — Compose has no nginx/Traefik; TLS termination is assumed external and undocumented in-stack.
- **Production-grade auth hardening** — no 2FA/MFA (user or admin), no per-username account lockout (only IP throttle), no atomic rate-limit (§8).
- **Security headers** — none on API responses or in `next.config.mjs` (§6, §8).
- **Billing completeness** — no cancellation/refund/proration, no invoices/receipts, no customer billing portal, single provider (Coinbase only) — no Stripe/cards, no tax handling.
- **Real session lifecycle semantics** — single session model in use, but a duplicate unused one exists (`activity_sessions`); no ban/risk gate before start.
- **Test depth** — no negative CSRF test, no coverage gate, no load/concurrency tests (§11).
- **DB hardening** — missing CHECK/enum constraints on status fields, some missing FK indexes, migration vs model drift (§7).
- **Frontend completeness** — the entire `ui-kit/` component library is dead code; command-palette search is non-functional; full i18n of the app; web security headers; accessibility on hand-rolled modals (§6).
- **Error handling polish** — readiness probe and global handler leak raw exception strings (§8).
- **Repo hygiene** — committed build artifacts (`apps/web/.next/`), `test.db`, and four `DeckPilot-*.zip` archives.

---

## 4. Critical Problems

> Severity is assigned for the **active app as a product**. There are **no classic critical RCE/auth-bypass holes** in the new backend — its security core is solid. The "Critical" items below are **product/launch blockers**, not exploit chains. All findings were verified in source.

### C1 — Headline feature is a demo mock (Critical · product)
- **Why:** Users would pay for "Steam activity / hour management" that the shipped app cannot perform. `integrations/steam.py` and `sessions/adapters.py` are mocks; `sessions/manager.py:132-135` hard-blocks any non-demo mode with `503`.
- **Where:** `apps/api/app/integrations/steam.py:14-47`, `apps/api/app/sessions/adapters.py:30-98`, `sessions/manager.py:132-135`.
- **Fix:** Decide explicitly: (a) ship a clearly-labeled **demo/closed beta** (relabel UI/marketing), or (b) implement a real, owner-consented `SteamClientAdapter` for accounts the user owns and remove the mock gate. Do not market as functional until one is true.

### C2 — Zero in-application observability (Critical · operability)
- **Why:** In production you cannot debug incidents, trace auth/billing failures, or alert. No logs, request IDs, metrics, or error tracking exist anywhere in `apps/api/app`.
- **Where:** `apps/api/app/main.py` (no logging middleware); whole package (`grep` → no `logging`/Sentry/OTel).
- **Fix:** Add structured JSON logging + request/correlation ID middleware, wire Sentry (or equivalent) for unhandled exceptions, expose Prometheus metrics or OTel traces. Gate paid launch on this.

### C3 — Account recovery is non-functional (High→Critical · functional)
- **Why:** Password reset and email verification mint hashed tokens but **no email is sent** (no provider). A user who forgets a password cannot recover; verification can't complete in practice.
- **Where:** `auth/service.py:121-193` (tokens created), no mail integration anywhere.
- **Fix:** Integrate a transactional email provider (Postmark/SES/Resend) behind a `Mailer` interface; until then disable/hide the flows in the UI to avoid dead ends.

### C4 — All container images run as root (High)
- **Why:** A container escape or in-process RCE runs as root; with dev bind-mounts, root maps to host root.
- **Where:** `docker/api.Dockerfile`, `docker/worker.Dockerfile`, `docker/web.Dockerfile`, `docker/web.dev.Dockerfile`, root `Dockerfile` — none has a `USER` directive.
- **Fix:** Add a non-root user (`useradd app && USER app`) to every image; multi-stage build to drop `build-essential` from runtime.

### C5 — No HTTP security headers (High)
- **Why:** The API sets only CORS (`main.py:41-47`); no HSTS/CSP/X-Frame-Options/X-Content-Type-Options/Referrer-Policy on any response (incl. `/docs`). The CSRF token sits in a JS-readable cookie, so a missing CSP raises XSS blast radius. The web app's `next.config.mjs` also sets no headers. `SECURITY.md` admits these are merely "recommended proxy headers."
- **Where:** `apps/api/app/main.py:41-47`; `apps/web/next.config.mjs`.
- **Fix:** Add a response-header middleware in FastAPI and a `headers()` block in `next.config.mjs` (HSTS, CSP, X-Frame-Options=DENY, X-Content-Type-Options=nosniff, Referrer-Policy). Don't rely on a perfectly configured proxy being present.

### C6 — Advertised background worker is dead code (High · architecture/claims)
- **Why:** `SESSION_MANAGER.md` and the in-app event message claim a Redis/RQ worker drives sessions. In reality `start_session` requires `mode=="demo"` (`manager.py:134`) and the demo branch activates **synchronously inline** (`manager.py:171-172`); the RQ `enqueue` branch (`:173-185`) is unreachable. The `worker` container has no real work.
- **Where:** `sessions/manager.py:132-185`, `core/config.py:26-27`.
- **Fix:** Either implement the official path that actually enqueues, or remove the worker/queue scaffolding and update the docs. Don't ship claims the code contradicts.

### C7 — In-memory, per-process session adapter (High · scalability)
- **Why:** `MockSteamClientAdapter.started_accounts` is an instance set and `_adapter` is a module-global singleton. With >1 uvicorn worker or a separate worker process, `heartbeat()`/`stop()` may hit a process that never saw `start()`. Breaks the multi-service Compose topology the docs imply.
- **Where:** `sessions/adapters.py:41,55,59,66,81-98`.
- **Fix:** Persist runtime ownership (DB/Redis) keyed by session, or pin sessions to a single worker, before scaling beyond one process.

### C8 — Repo hygiene / committed artifacts (Medium, but fix immediately)
- **Why:** Working tree carries `apps/web/.next/` build output, `test.db` (204 KB), and four `DeckPilot-*.zip` snapshots. Bloats the repo, risks stale/secret leakage, and confuses reviewers.
- **Where:** repo root + `apps/web/.next/`.
- **Fix:** `.gitignore` them, `git rm --cached`, delete the zips.

---

## 5. Backend Audit

### 5.1 New FastAPI backend — what is done well
- **Modular feature packages**: `auth`, `steam_accounts`, `games`, `sessions`, `billing`, `admin`, `audit`, `dashboard`, `system`, each with `routes/service/schemas`. Clean separation; routes thin, logic in services.
- **App wiring** (`main.py`): CORS, global `ValueError→400` handler, three-tier health endpoints, lifespan graceful shutdown of active sessions, `/api/v1` prefix.
- **Config & production validation** (`core/config.py`): genuinely excellent. Pydantic settings with a `model_validator` that, in production, rejects weak secrets, non-HTTPS URLs, localhost URLs, insecure cookies, `SQLite`, `mock` billing, wildcard/empty CORS, and ungated demo mode. This is better than most shipped products.
- **DI guards** (`core/deps.py`): `current_user` (JWT + revocable DB session + banned check), `admin_user`, `active_subscription`, `require_csrf`, ownership via per-query `user_id` scoping.
- **Security primitives** (`core/security.py`): bcrypt (passlib), Fernet credential encryption, JWT HS256 session tokens, SHA-256 token hashing, `secrets.token_urlsafe` ids.
- **Billing logic** (`billing/service.py`): plan catalog, trial auto-provision, expiry handling, **plan limits enforced**, webhook idempotency + verified-only grants, admin manual grants (audited).
- **Admin** (`admin/service.py`): a real control center — overview, paginated search/filter, detail drawer, ban/unban, role grant with self-revoke guard, subscription edits, force-stop, payments, audit listing.
- **Session manager** (`sessions/manager.py`): idempotent start (returns existing active session), ownership scoping, plan checks, heartbeat, error/stop transitions, event + audit logging, graceful shutdown.

### 5.2 What is done poorly / needs work
- **RQ worker is unreachable dead code** (§C6); "queued for transparent worker" event message is misleading.
- **In-memory adapter singleton** (§C7) is not multi-process safe.
- **TOCTOU races**: `start_session` does SELECT-existing → `assert_active_session_limit` count → INSERT without a row lock or unique constraint; two concurrent starts can both pass the limit. Same pattern in webhook idempotency (check-then-insert, no `IntegrityError` handling).
- **No ban/risk gate before start**: `start_session` only checks `status == online`; `BanCache` is populated but not consulted. A legitimate manager should refuse to start for a flagged account.
- **Admin free-text status/plan**: `admin_update_subscription`/`update_user` assign `status`/`plan_code` directly with no whitelist; an invalid `status` silently breaks entitlement logic.
- **Audit granularity**: ban/unban/role-grant collapse into one `admin.user_update` action with no before-state captured.
- **Error leakage**: `readyz` and the global `ValueError` handler return `str(exc)` in all environments.
- **Two session data models**: `activity_sessions`/`session_logs` defined + indexed but unused; live model is `steam_sessions`/`session_events`.

### 5.3 Legacy Flask backend
- Already **well-modularized**: `create_app` factory, blueprint-per-domain, a dedicated `security/` package (CSRF constant-time compare, Fernet encryption, password service with legacy auto-migration, rate limit, **log redaction filter**), SQLite with a versioned migration runner, global security headers/CSP.
- **Contains the only real automation**: `accounts/steam_client_service.py` does real `SteamClient.login`, `executor.submit(client.run_forever)`, and a `while True: client.games_played(game_ids); sleep(60)` gevent farm loop over a process-global `clients = {}` dict.
- **Problems**: mixed `ThreadPoolExecutor` + gevent over process-global mutable state (not thread-safe, not multi-worker safe); unbounded farm loop; legacy Coinbase webhook verifies signature but **grants no subscription and has no idempotency** (`billing/routes.py:38-46`); rate-limit bucket dict grows unbounded and keys on spoofable `remote_addr`.

### 5.4 Target backend structure (already mostly realized)
The new app already follows a sound target shape. Recommended consolidation:
```
apps/api/app/
  core/         config, database, deps, security, rate_limit, models, logging(NEW), telemetry(NEW)
  auth/  users/  steam_accounts/  games/
  sessions/     manager, service, adapters, routes, schemas, runtime_state(NEW: Redis-backed)
  billing/      providers/{base,mock,coinbase,stripe(NEW)}, service, routes, schemas
  admin/  audit/
  integrations/ steam(real adapter behind official flag), mailer(NEW)
  tasks/        real worker jobs (or delete)
```
Key moves: pull session runtime state out of the in-process singleton into Redis/DB; add `mailer` + `telemetry`; either make `tasks/` real or remove it; collapse the duplicate session model.

---

## 6. Frontend / UX/UI Audit

**Overall:** the Next.js 15 app is **real, working software**, not a scaffold — full page coverage, a dark-glass design system (CSS variables + Tailwind tokens), 3 themes via `next-themes`, a 4-language i18n catalog, 3-layer route protection (edge middleware + server-side `/auth/me` + admin-enforcing layout guard), and a cookie-credentialed API client with CSRF double-submit + 401 redirect. Quality is **uneven**, though.

| Surface | State | Notes |
|---|---|---|
| login / register | ✅ | `auth-form.tsx`, i18n-localized, validation |
| dashboard | ✅ | `features/dashboard/dashboard-client.tsx` — inline-built, polls every 5s |
| accounts | ✅ | Inline cards (not the ui-kit `AccountCard`) |
| modals | 🟡 | Hand-rolled `fixed` div Steam-Guard modal: **no focus trap, no Esc, no `role=dialog`** |
| admin panel | ✅ | `features/admin/admin-client.tsx` — full control center client |
| billing / pricing | ✅ | `features/billing/*`, pricing cards, payment-status pages |
| no-subscription / buy | ✅ | Plan gating + checkout entry |
| command palette | 🟡 | Search input is **non-functional** (no `value`/`onChange`/filter) |
| legal pages | 🟡 | Present but hardcoded English |

**Strengths:** cohesive dark-glass aesthetic, design tokens (`lib/design-tokens.ts`), loading (`app/loading.tsx`)/error (`app/error.tsx`)/not-found states, toasts (Sonner), responsive layout, sensible API client (`lib/api.ts`) with credentials + CSRF header + 401 handling, real 3-layer auth protection (`middleware.ts`, `lib/server-auth.ts`, `(app)/layout.tsx`).

**Key problems (verified):**
- **Entire `ui-kit/` is dead code** — `account-card`, `session-card`, `game-card`, `metric-card`, `data-table`, `status-badge`, `empty-state`, `error-state`, `loading-skeleton`, `shell` are exported from `ui-kit/index.ts` but imported nowhere (only `pricing-card` is used). Dashboard/admin re-implement these inline, so `DESIGN_SYSTEM.md` documents components no screen uses. (Medium · tech debt)
- **Authenticated app is hardcoded English** despite the 4-language catalog — `t()`/`useLanguage` are used only in auth/command-palette/nav/landing; dashboard/admin/billing/settings + 4 legal pages are literal English. (Medium)
- **Command-palette search non-functional** (`features/command-palette.tsx:27-33`). (Medium)
- **Steam-Guard modal accessibility** — no focus trap/Esc/ARIA. (Medium)
- **No web security headers** (`next.config.mjs`). (Medium)
- **Dashboard polling** — 5s interval with a per-session N+1 `/sessions/{id}/events` fetch, no visibility gating, no abort on unmount; plus a divergent `SystemMode` type duplicated in two files. (Low)

**Recommendations for a premium SaaS UI:** actually **use the ui-kit** (delete inline duplicates), add a persistent **sidebar + topbar `Shell`**, metric **cards** on the dashboard, a dedicated **session panel** with live status, a real **game selector** with search, polished **pricing cards** with current-plan state, an **admin control center** layout (filters + drawer using `DataTable`/`Drawer`), finish the **dark-glass** token system, replace hand-rolled modals with Radix Dialog (focus trap), wire the **command palette** to real fuzzy search, and complete **i18n** across the app. Replace polling with SWR/React Query + visibility gating.

---

## 7. Database Audit

**Engine:** PostgreSQL in prod (default `postgresql+psycopg`); SQLite only for tests (hard-blocked in prod by `config.py:124-125`). Alembic migrations `001–005` run on container start. Legacy app uses SQLite with its own SQL migration runner.

**Current model (`apps/api/app/core/models.py`, 16 tables):**

| Group | Tables |
|---|---|
| Identity/auth | `users`, `user_sessions` (revocable, hashed), `password_reset_tokens` |
| Steam | `steam_accounts` (Fernet-encrypted creds), `games`, `account_games` (unique `account_id+game_id`), `ban_cache` |
| Sessions (v1, **unused**) | `activity_sessions`, `session_logs` |
| Sessions (v2, **live**) | `steam_sessions`, `session_events`, `account_status` (heartbeat) |
| Billing | `plans`, `subscriptions` (unique per user), `payments` (unique `idempotency_key`), `billing_events` (unique `idempotency_key`) |
| Audit | `audit_logs` |

**Strengths:** explicit `ondelete` on all FKs (`CASCADE` for owned rows, `SET NULL` for audit/event refs); unique idempotency keys for replay safety; sensible indexes on `payments` (user/provider/status/idempotency); `email_verified_at`/`last_ip`/`last_seen_at`/`banned` on users.

**Gaps & problems (verified):**
- **High — migration drift:** `steam_accounts.status`, `activity_sessions.status/current_games` are `NOT NULL` with **no server_default** in migration `001` (defaults are Python-only). Any non-ORM insert violates `NOT NULL`. Same for `subscriptions.status/plan_code` (Medium).
- **Medium — no CHECK/enum on status fields:** `AccountStatus`/`SessionStatus` stored as `String(32)`; the DB will store any string. Combined with two parallel session tables, state can silently corrupt.
- **Medium — missing FK indexes:** `subscriptions.plan_id` and `payments.plan_id` are unindexed FKs → seq-scans on plan delete/update and slower joins.
- **Medium — redundant session subsystems:** `activity_sessions`/`session_logs` vs `steam_sessions`/`session_events` model the same concept with no coupling; only v2 is used.
- **Low — lost audit indexes:** legacy `002_security_hardening.sql` indexed `audit_logs.actor_user_id` and `(target_type,target_id)`; the new `audit_logs` only indexes `action`, so admin lookups by actor/target seq-scan.
- **Low — `updated_at` never auto-updates:** `server_default=now()` but no `onupdate`/trigger (subscriptions, payments, steam_sessions, account_status).
- **Low — case-sensitive email uniqueness:** `ix_users_email` is unique on the raw string; `User@x.com` ≠ `user@x.com`.
- **No `login_attempts` table** — failed-login throttling is Redis-based (not DB); failed logins are recorded in `audit_logs` instead. Acceptable, but means no DB-level lockout history.

**Recommended additions:** `CHECK`/native enums on status; index `plan_id` FKs and restore `audit_logs(actor_user_id)` + `(target_type,target_id)`; add `server_default` to all `NOT NULL` columns; `onupdate=func.now()` on `updated_at`; `citext`/lower-index for email; drop the unused v1 session tables; consider a dedicated `login_attempts` table if you want lockout history.

---

## 8. Security Audit

**Bottom line:** the new app's **auth/session/CSRF/rate-limit/crypto core is genuinely solid** and most README/SECURITY claims **verify true**. The real cross-cutting gaps are **headers**, **observability-as-security**, **container hardening**, and a few medium items.

### Verified findings
| ID | Sev | Finding | Location |
|---|---|---|---|
| S1 | High | No HTTP security headers on API or web (§C5) | `main.py:41-47`, `next.config.mjs` |
| S2 | Med | CSRF token unsigned & not session-bound; `==` compare; relies on SameSite=Lax | `core/deps.py:46-53` |
| S3 | Med | Password-reset request enables username/email enumeration via timing (work only for real users) | `auth/service.py:135-140` |
| S4 | Med | Redis rate-limit `INCR` then `EXPIRE` not atomic → crash between leaves TTL-less key → **permanent lockout** | `core/rate_limit.py:44-54` |
| S5 | Med | Webhook endpoint unrate-limited + persists unverified events (storage/DoS) | `billing/routes.py:93`, `service.py:289` |
| S6 | Med | Admin can set arbitrary subscription `status`/`plan_code` (no whitelist) | `billing/service.py:350`, `admin/service.py:236` |
| S7 | Med | Raw exception strings returned (`readyz`, global `ValueError`) | `main.py:52,75,85` |
| S8 | Low | bcrypt 72-byte silent truncation (schema allows 256 chars) | `auth/schemas.py:9`, `security.py:13` |
| S9 | Low | bcrypt 4.0.1 + passlib 1.7.4 known incompatibility (works, warns; passlib unmaintained since 2020) | `apps/api/requirements.txt:2,7` |
| S10 | Low | Hard-coded legacy `shb_session`/`shb_csrf` cookie acceptance widens trusted surface | `core/deps.py:11-17,46-51` |
| S11 | Low | No account lockout; failed-login throttle keys on IP only | `auth/routes.py:76`, `rate_limit.py:27-31` |
| S12 | Low | Auth cookies set/deleted without explicit `path` | `core/deps.py:67-115` |

### Claims verification (README / CHANGELOG / SECURITY.md vs code)
| Claim | Verdict | Evidence |
|---|---|---|
| Passwords hashed (bcrypt/passlib) | ✅ true | `security.py:10-18` |
| HTTP-only session cookies | ✅ true | `deps.py:69-77` (`httponly=True`) |
| Server-side session revocation | ✅ true | `deps.py:28-34`, `auth/service.py:84-114` |
| CSRF protection | 🟡 partial | exists but unsigned/session-unbound (S2) |
| Password-reset tokens hashed/expiring/single-use, revoke sessions | ✅ true | `auth/service.py:121-160` |
| Email verification tokens hashed, never returned in prod | ✅ true | `auth/service.py:163-193`, `routes.py:137` |
| Rate limits, Redis fail-closed in prod | ✅ true | `rate_limit.py:57-77`; test asserts `503` |
| Encrypted Steam creds + owner-only access | ✅ true | Fernet + `user_id` scoping |
| Steam Guard never stored | ✅ true | passed to adapter only, never persisted |
| Real Steam automation disabled unless official linking configured | ✅ true | `manager.py:132-135`, `DisabledSteamClientAdapter` |
| Webhooks can't activate from unverified events | ✅ true | `service.py:298` (`if event.verified and payment`) |
| Webhooks provider-scoped | ✅ true | `find_payment_for_event` filters `provider` |
| Idempotent billing | ✅ true | unique `idempotency_key` + dedup |
| Strict production settings validation | ✅ true | `config.py:94-136` |
| No TLS verification disabled | ✅ true | no `verify=False` anywhere; mock makes no outbound HTTP |
| No secrets in logs | ✅ true | failed login records username+IP only; legacy has a redaction filter |
| Security headers provided by deployment | 🟡 partial | labeled "recommended proxy headers"; API sets none (S1) |
| Error details normalized before return | 🟡 partial | not followed by `readyz`/`ValueError` handler (S7) |

### Security checklist (action items)
- [ ] Add API + web security headers (HSTS/CSP/X-Frame-Options/X-Content-Type-Options/Referrer-Policy).
- [ ] Make rate-limit `INCR`+`EXPIRE` atomic (Lua/`SET NX EX` / pipeline).
- [ ] Sign + session-bind the CSRF token; constant-time compare; add Origin/Referer fallback.
- [ ] Normalize external error bodies; never return `str(exc)`.
- [ ] Whitelist admin subscription `status`/`plan_code`.
- [ ] Rate-limit the webhook endpoint; cap/sweep unverified events.
- [ ] Add per-username login lockout in addition to IP throttle; consider 2FA.
- [ ] Upgrade the bcrypt/passlib stack (or move to `argon2`).
- [ ] Drop root in containers; remove legacy hard-coded cookie acceptance once migration is done.
- [ ] Add structured logging + error tracking (security-relevant).

---

## 9. Billing / Subscription Audit

**What exists (and is good):**
- **Plans** (`PLAN_DEFINITIONS`): trial/starter/pro/ultra/lifetime with `account_limit` + `active_session_limit` + features, synced to DB (`sync_default_plans`).
- **Subscription status lifecycle**: trial auto-provision, `active`/`trialing`/`expired`/`canceled`, expiry computed and lazily transitioned (`current_subscription`).
- **Plan limits enforced** at real choke points (account add, session start) → `402`.
- **Provider abstraction**: `BillingProvider` base, `MockProvider`, `CoinbaseProvider` (real Commerce checkout via `httpx`).
- **Webhook verification**: constant-time HMAC-SHA256 (`hmac.compare_digest`); **unverified events never grant** (`service.py:298`).
- **Idempotency**: unique `billing_events.idempotency_key` + pre-insert dedup; provider-scoped payment lookup.
- **Payment status transitions**: `pending → paid/failed/canceled`; `paid` activates subscription (audited).
- **Admin manual grants**: `admin_update_subscription` (plan/status/extend/expiry, `manual_override`, audited).

**Why it is not yet production-ready:**
- **Single provider (Coinbase only)** — no Stripe/cards/PayPal; crypto-only checkout is a narrow market.
- **Check-then-insert idempotency race** — no `IntegrityError` handling on concurrent duplicate webhooks (Low).
- **Webhook endpoint unrate-limited** and stores unverified events (Medium, §S5).
- **Admin free-text status/plan** (Medium, §S6).
- **No lifecycle completeness** — no cancellation/refund/proration, no invoices/receipts, no dunning/retry, no customer billing portal, no tax handling.
- **Coinbase checkout is synchronous `httpx.post`** inside the request (15s timeout) — should be resilient/retried.

**How to do it right:** keep the provider abstraction (it's good); add a Stripe provider; make webhook processing transactional + idempotent under races (insert-first, catch unique violation); rate-limit and authenticate webhooks; add subscription state machine with cancel/refund/proration + invoices; persist provider event payloads (already done) and add a reconciliation job; whitelist admin-settable states; add manual-grant + comp flows (present) with stronger audit (before/after).

---

## 10. Admin Panel Audit

**What exists:** a genuine control center (`admin/{routes,service}.py`), every route gated by `admin_user`, mutations also require CSRF, all mutations audited.
- Overview metrics (users, active/expired subs, banned, active sessions, failed logins, revenue).
- User list with username search + filters (all/active/banned/admin/subscribed/expired) + pagination.
- User detail drawer (accounts, sessions, payments, audit events).
- Update user: ban/unban, admin grant/revoke (**self-revoke confirmation guard**), subscription status/plan.
- Subscription controls (plan/status/extend/expiry).
- Force-stop sessions (per user) with event + audit logging.
- Payments view + subscription-change log + audit search.

**What's missing / dangerous:**
- **Coarse audit for the most sensitive ops** — ban/unban/role-grant share one `admin.user_update` action with no before-state (Medium).
- **No guardrails** against banning the last admin / removing the last admin via a non-self path (Low).
- **Search by username only** (no email/id).
- **`force_logout` hides partial failures** — response returns `stopped_sessions` but not the `failed` count (Low).
- **No "force logout web sessions"** (revoke `user_sessions`) action — only Steam "sessions" (mock). Banning relies on per-request `banned` check.
- **No payments detail/refund** action, no impersonation-for-support, no bulk actions, no export.

**Add:** richer user filters (email/date/spend), a fuller user drawer, granular per-action audit with before/after, explicit ban/unban + **force web-session logout**, subscription comp/refund controls, last-admin protection, a payments drawer with provider event timeline, and overview charts.

---

## 11. Testing / QA Audit

**Tests exist and pass:** **58/58 API** (`apps/api/tests/`, 12 files) + **16/16 legacy** (`legacy/flask/tests/`), executed during this audit.

**API coverage (real):** auth (8), accounts incl. cross-user ownership (6), admin control center (5), billing incl. webhook signature rejection + idempotency + limits (11), production-config validation (5), guards & sessions (2), health (1), rate-limit fail-closed (2), session manager lifecycle (7), system mode (1).

**Coverage gaps (must-add):**
- **Negative CSRF test** — every mutating test *sends* the token; none asserts `403` on missing/invalid. A regression disabling CSRF would pass CI. (Medium)
- **No coverage gate** — `pytest` runs but no `--cov` threshold; silent test deletion wouldn't fail CI.
- **Concurrency/race tests** — none for the start/limit TOCTOU or webhook idempotency race.
- **`smoke-qa.mjs` uses an unseeded `demo` user** — `seed.py` only creates `admin`, so the web smoke login would fail as written. (Medium)
- **Frontend** — no component/E2E tests beyond the smoke script; no Playwright in CI.
- **Email/recovery flows** — untested end-to-end (no provider).

**Mandatory test list:** registration (dup/validation), login (success/fail/lockout), CSRF reject, subscription guard (`402`), admin guard (`403`), account ownership (cross-user `404`), add/delete account, Steam adapter mock (start/stop/heartbeat/error), session start/stop idempotency + limit race, billing mock + **webhook verified/unverified + replay**, security headers present, error-body normalization, plus frontend auth-flow E2E.

---

## 12. DevOps / Production Readiness

**Strong for a beta:**
- 6-job CI: API (ruff + pytest + pip-audit), web (lint + typecheck + npm-audit + build), legacy (pytest + pip-audit), compose config validation, Docker image builds. Dependabot + pre-commit (ruff) + `release-check.sh` gate + Playwright smoke harness.
- Compose: postgres:16 + redis:7 (healthchecks + persistent volume), API runs `alembic upgrade head && seed && uvicorn` with `/readyz` healthcheck, services gate on `depends_on: healthy`.
- Three-tier health endpoints; production-config validation enforced + tested.

**Gaps:**
- **No observability** (logs/metrics/traces/error tracking) — §C2.
- **All images run as root** + `build-essential` retained in runtime (api/worker) — §C4.
- **No automated backups** / no restore rehearsal (only manual `pg_dump` docs).
- **No resource limits / restart policies** in Compose; worker crash has no recovery.
- **No TLS/reverse proxy** in-stack; single uvicorn process (consistent with §C7).
- **No coverage gate**; `readyz` leaks raw errors.
- **Worker container is idle** (no reachable jobs).

**Production checklist:**
- [ ] Structured logging + request IDs + Sentry + metrics/traces.
- [ ] Non-root containers; multi-stage builds; minimal runtime images.
- [ ] Scheduled encrypted DB backups + tested restore.
- [ ] Reverse proxy + TLS termination + security headers at edge **and** app.
- [ ] Resource limits + `restart: unless-stopped` + autoscaling story (after §C7 fix).
- [ ] Coverage gate; negative-security tests in CI.
- [ ] Secrets via a real secret manager (not compose defaults).
- [ ] Make the worker real or remove it; document migrations/rollback.

---

## 13. Target Architecture

### Option A — Keep the current stack, finish it (recommended)
The Option-B rewrite is essentially already built. The pragmatic path is to **harden what exists**, not rewrite again.
- **Pros:** ~70% done; solid auth/billing/admin cores; tests + CI + Docker already exist; fastest path to a real beta.
- **Cons:** must resolve the core-feature decision (real vs demo), the worker/scaling gaps, and observability before paid launch; some tech debt (dead ui-kit, duplicate session model).
- **Structure:** as in §5.4 — add `core/logging`, `core/telemetry`, `integrations/mailer`, Redis-backed session runtime state, a real or removed worker, a second billing provider, and finish the frontend ui-kit/i18n.
- **Roadmap:** §14 Phases 1–8 directly apply.

### Option B — Full rewrite (Next.js + FastAPI + PostgreSQL + Redis + Worker)
- **Pros:** clean slate; chance to design the session-runtime/observability correctly from day one.
- **Cons:** **largely redundant** — the repo already *is* this stack. A rewrite would throw away working auth/billing/admin/tests for little gain.
- **Verdict:** **not justified.** The existing code already realizes this architecture; treat the remaining work as "finish Option A," not "rewrite."

```
deckpilot/
  apps/web   (Next.js 15 — App Router, ui-kit, i18n)
  apps/api   (FastAPI — feature packages, telemetry, mailer)
  apps/worker(real RQ jobs OR removed)
  packages/shared (contracts/types)
  docker/ docs/ legacy/(archive)
```

---

## 14. Roadmap

### Phase 0 — Audit & backup ✅ (this report)
- **Goal:** know the real state. **Done.** **Acceptance:** this document. **Add:** tag/snapshot, then purge committed artifacts (`.next/`, `test.db`, zips).

### Phase 1 — Security hardening
- **Tasks:** API+web security headers; atomic rate-limit; signed/bound CSRF; error-body normalization; admin status/plan whitelist; webhook rate-limit; non-root containers; bcrypt/passlib upgrade.
- **Acceptance:** headers present (scanned); negative CSRF/authz tests green; no `str(exc)` in responses; images run as non-root. **Risk:** low; mostly additive.

### Phase 2 — Backend refactor / correctness
- **Tasks:** fix start/limit + webhook TOCTOU (locks/unique+IntegrityError); add ban/risk gate; resolve worker (real or remove); move session runtime state to Redis; collapse duplicate session model; migration server_defaults + indexes + constraints.
- **Acceptance:** concurrency tests pass; single session model; alembic↔models parity check green. **Risk:** medium (data-model migration).

### Phase 3 — UI/UX redesign
- **Tasks:** adopt the ui-kit (delete inline dupes); sidebar+topbar Shell; Radix modals (focus trap); finish i18n; wire command-palette search; replace polling with SWR + visibility gating; web security headers.
- **Acceptance:** zero dead ui-kit; a11y checks pass on dialogs; all app strings localized. **Risk:** low/medium.

### Phase 4 — Billing / subscriptions
- **Tasks:** add Stripe provider; transactional idempotent webhooks; cancellation/refund/proration; invoices/receipts; billing portal; dunning.
- **Acceptance:** Stripe sandbox e2e (checkout→webhook→grant→cancel→refund) tested; reconciliation job. **Risk:** medium (money paths).

### Phase 5 — Session manager (core feature decision)
- **Tasks:** **decide:** ship demo-labeled, or implement a real owner-consented adapter behind official linking with Redis-backed runtime ownership, real worker jobs, heartbeats, and ban-gating.
- **Acceptance:** if real — multi-worker safe start/stop/heartbeat with persisted ownership + integration tests; if demo — UI/marketing clearly labeled "demo." **Risk:** high (this is the product).

### Phase 6 — Admin control center
- **Tasks:** granular audit (before/after), force web-session logout, last-admin protection, richer filters/drawer, payments/refund drawer, overview charts.
- **Acceptance:** every sensitive action has discrete audit + before-state; admin e2e tests. **Risk:** low.

### Phase 7 — Tests / CI / Docker / Observability
- **Tasks:** coverage gate; negative-security suite; Playwright in CI; structured logging + Sentry + metrics; non-root multi-stage images; backups + restore rehearsal; resource limits/restart; TLS/proxy.
- **Acceptance:** coverage threshold enforced; logs/traces visible; restore drill recorded. **Risk:** low/medium.

### Phase 8 — Beta release
- **Tasks:** finalize legal/privacy, email provider live, status page, runbooks, rate-limit/load test, secret manager.
- **Acceptance:** closed beta with real users, monitored, recoverable. **Risk:** medium.

---

## 15. Final Verdict

**Readiness (honest):**
- **Engineering completeness toward a production SaaS skeleton:** **~70%.** The auth, billing, admin, data model, tests, CI, and Docker are real and mostly well-built.
- **Completeness as a *shippable product that performs its headline feature*:** **~35–40%.** The active app cannot do real Steam activity — it's a demo mock — and lacks observability, email, and multi-process safety.

**Can you show it to users?** **Yes — as a clearly-labeled demo / closed beta** of the dashboard and account management. The UI is presentable and the flows work end-to-end in demo mode.

**Can you launch an open beta?** **Not yet.** Open beta with paying users would be misleading (core feature mocked) and operationally blind (no logs/metrics) with recovery dead ends (no email).

**Must-do before any public/paid launch (hard gates):**
1. Resolve the **core feature** — implement a real owner-consented session adapter, **or** relabel the product as a demo and remove paid claims (§C1, Phase 5).
2. **Observability** — logging + error tracking + metrics (§C2).
3. **Email provider** — make recovery/verification real (§C3).
4. **Containers non-root** + security headers (API + web) (§C4, §C5).
5. **Worker + scaling** — make the worker real or remove it; move session runtime state off the in-process singleton (§C6, §C7).
6. **Billing completeness** — at least cancellation/refund + a card provider before charging real money (§9).
7. **Repo hygiene** — purge `.next/`, `test.db`, zips (§C8).

**Can wait (post-launch):** full i18n of the app, ui-kit consolidation, command-palette search, DB `CHECK`/enum constraints + index tuning, granular admin audit, last-admin guardrails, the bcrypt/passlib upgrade, removing the duplicate session model.

**One-line conclusion:** This is a **surprisingly mature, honestly-documented SaaS beta** whose *infrastructure* is largely production-grade, gated by one decisive product question (real feature vs. demo) and a short list of operability fixes. Finish Option A — do **not** rewrite.

---

*Prepared from direct source review of `apps/api`, `apps/web`, and `legacy/flask`, an 8-dimension parallel audit with claim verification, and execution of both test suites (58 API + 16 legacy, all passing). No code was modified.*
