# Real Owner-Operated Idle Sessions

> **Read this fully before enabling.** This makes real Steam playtime accrue on
> accounts you own by logging in and reporting games as played (the same
> mechanism as open tools like ArchiSteamFarm). It is **off by default**.

## Scope & guardrails (non-negotiable)
- **Owner-operated only.** Requires the account's own credentials **and** a Steam
  Guard code supplied by the owner at session start. There is **no Steam Guard bypass**.
- **Transparent.** Every step writes a session event; sessions are stoppable on
  demand and auto-stop at `STEAM_SESSION_MAX_MINUTES`.
- **No evasion.** No anti-detect, no proxy rotation, no ban/VAC evasion, no hidden
  automation. None of these will be added.

## Risks (yours to accept)
- Steam may **lock or ban** accounts for third-party automation.
- Inflating hours to **resell accounts** violates the Steam Subscriber Agreement;
  using it to manipulate **CS2 trust factor / matchmaking** violates game rules.
  This tool is for managing your own accounts, not for those uses.
- Credentials are stored **Fernet-encrypted** at rest (needed to log in). Treat the
  `ENCRYPTION_KEY` and DB as highly sensitive.

## Architecture
- Real login + `games_played` idle loop run in the **worker** process only
  (`apps/api/app/tasks/sessions.py::run_real_activity_session`). The async API never
  imports the Steam library.
- The Steam client (`steam[client]`, ValvePython) is installed **only** in the
  worker image (`apps/worker/requirements.txt`).
- Start enqueues an RQ job; stop sets a cooperative stop flag in the runtime store
  (Redis in prod) that the worker polls; the worker logs out and finalizes the record.

## Enabling
```
STEAM_INTEGRATION_MODE=official
STEAM_OFFICIAL_LINKING_ENABLED=true
STEAM_REAL_SESSIONS_ENABLED=true
STEAM_SESSION_MAX_MINUTES=720
```
Then: add an account with its real **login + password** (ownership attested), and
start a session with a fresh **Steam Guard code**.

## API
- `POST /api/v1/steam-accounts` — in real mode, requires `username` (Steam login) + `password`.
- `POST /api/v1/sessions` `{ "account_id": N, "steam_guard_code": "XXXXX" }` — enqueues the real worker session. The code is single-use and never stored.
- `POST /api/v1/sessions/{id}/stop` — signals the worker to log out and stop.

## Status / what is verified
- ✅ Gating, enqueue/stop wiring, credential storage, schema, runtime stop-flag,
  the **per-account concurrency lock**, the **refresh-token capture/login + password
  drop**, **reconnect/backoff**, and the **frontend Guard-code modal** are implemented
  and the offline wiring is unit-tested.
- ⚠️ **The live Steam login + idle loop is NOT tested here** (no real account is used).
  Validate login/2FA/idle/reconnect against your own account before relying on it.
  The 2FA field handling (mobile vs email Guard), `login_key`/refresh-token capture,
  and reconnection semantics are version-dependent in ValvePython and may need tuning.

## Hardening implemented
- **Refresh token instead of password:** after the first successful login the worker
  captures a `login_key`/refresh token, stores it Fernet-encrypted, and (when
  `STEAM_DROP_PASSWORD_AFTER_LINK=true`, the default) drops the stored password.
  Later sessions log in with the token — no password, no Guard prompt.
- **Reconnect/backoff:** the idle loop detects a dropped CM connection and reconnects
  with bounded exponential backoff (up to 5 attempts) before failing.
- **Concurrency guard:** an atomic per-account lock (Redis `SADD`) prevents the same
  account from idling on two workers at once.
- **Frontend:** when `/system/mode` reports `real_steam_enabled`, the dashboard start
  button opens an accessible (Radix focus-trapped) Steam Guard modal; the single-use
  code is sent with the start request and never stored.

## TODO (remaining)
- Validate the ValvePython `login_key`/refresh-token + reconnect flow against real
  accounts (the library's auth API changed in 2023; field names may need adjusting).
- Surface "refresh-token saved / re-link required" state in the accounts UI.
