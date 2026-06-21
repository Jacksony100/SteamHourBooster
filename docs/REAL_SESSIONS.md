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
- ✅ Gating, enqueue/stop wiring, credential storage, schema, and the runtime
  stop-flag are implemented and unit-tested (offline).
- ⚠️ **The live Steam login + idle loop is NOT tested here** (no real account is used).
  Validate the login/2FA/idle behavior against your own account before relying on it.
  The 2FA field handling (mobile vs email Guard) and reconnection may need tuning for
  your accounts.

## TODO (hardening)
- Replace stored passwords with Steam refresh tokens (`login_key`) after first login.
- Reconnect/backoff handling for dropped CM connections.
- Per-account concurrency safety if the same account is started from two sessions.
- Frontend: collect the Steam Guard code in the start modal when real mode is on.
