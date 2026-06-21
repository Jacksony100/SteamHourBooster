# Session Manager

DeckPilot now uses a dedicated session manager instead of request-process globals, gevent greenlets, or hidden in-memory Steam clients.

## Safety Scope

The session manager is only for transparent management of user-owned Steam accounts:

- no platform-rule circumvention;
- no account-risk evasion;
- no Steam Guard circumvention;
- no network-routing evasion;
- no hidden automation;
- no mass abuse workflows.

All lifecycle state is visible through database records and UI events.

## Architecture

```text
FastAPI route
  -> SessionManager
     -> SteamClientAdapter interface
        -> MockSteamClientAdapter in STEAM_INTEGRATION_MODE=demo
        -> Disabled official adapter until official linking is explicitly configured
     -> steam_sessions
     -> session_events
     -> account_status
     -> Redis/RQ worker for background lifecycle
```

## Tables

### `steam_sessions`

Canonical session lifecycle table.

- `id`
- `user_id`
- `account_id`
- `status`: `starting`, `running`, `stopping`, `stopped`, `error`
- `selected_games`: JSON array of app IDs
- `worker_job_id`
- `started_at`
- `stopped_at`
- `last_heartbeat_at`
- `error_message`
- `created_at`
- `updated_at`

### `session_events`

Append-only event log for account/session lifecycle.

Important event types:

- `account_login_requested`
- `steam_guard_required`
- `account_online`
- `games_selected`
- `session_started`
- `session_stopped`
- `session_error`

### `account_status`

Current account state record separate from encrypted credentials.

- `account_id`
- `status`
- `last_event`
- `last_heartbeat_at`
- `error_message`
- `updated_at`

`steam_accounts.status` is still synchronized for compatibility with existing UI/API responses.

## Idempotency

### Start

`POST /api/v1/sessions` is idempotent per active account session:

1. Verify the account belongs to the user.
2. Verify the account is online.
3. Verify games are selected.
4. If an active `starting/running/stopping` session already exists for that account, return it.
5. Otherwise check `active_session_limit`.
6. Create a `steam_sessions` row.
7. Start through `SteamClientAdapter`.

This prevents duplicate starts from double-counting plan limits.

### Stop

`POST /api/v1/sessions/{id}/stop` is idempotent:

- `stopped` and `error` sessions are returned unchanged;
- active sessions transition through `stopping`;
- successful adapter stop writes `session_stopped`.

## Plan Limits

The billing layer counts active rows in `steam_sessions` with status:

- `starting`
- `running`
- `stopping`

Trial users have `active_session_limit = 0`, so they can preview the product and select games but cannot start active sessions.

## Adapter Contract

`SteamClientAdapter` defines:

- `login_account`
- `logout_account`
- `start_session`
- `heartbeat`
- `stop_session`
- `close_all`

`MockSteamClientAdapter` is used in demo mode and can simulate start/stop/Steam Guard failures. The real adapter is intentionally disabled until it can be implemented through official, transparent user-authorized flows without platform-rule circumvention or hidden automation.

`STEAM_INTEGRATION_MODE=official` does not collect Steam passwords. If official linking is not configured, session start fails closed with `Official Steam sessions are not configured yet`.

## Worker Lifecycle

The RQ worker runs `app.tasks.sessions.run_activity_session`:

1. Load `steam_sessions` row.
2. Start through adapter.
3. Mark `running`.
4. Update heartbeat.
5. Respect `stopping/stopped/error`.
6. Stop through adapter.
7. Mark `stopped` or `error`.

## Admin Force Stop

Admin force-stop no longer only flips database state. The API attempts to stop the adapter/runtime first:

1. Load active sessions for the target user.
2. Call `SteamClientAdapter.stop_session`.
3. On success, mark `stopped` and write `session_stopped`.
4. On failure, mark `error` and write `session_error`.
5. Write an `admin.force_logout_sessions` audit event with stopped and failed counts.

For future real worker-owned runtimes, this should evolve into explicit queued stop commands. The current implementation is safe for demo mode because the adapter is simulated and visible.

## Graceful Shutdown

FastAPI lifespan and the worker shutdown path call:

```python
get_session_manager().shutdown_active_sessions(db)
```

This closes active adapter clients, writes `session_stopped` or `session_error`, and marks accounts offline on application shutdown.

## API

- `GET /api/v1/sessions`
- `POST /api/v1/sessions`
- `POST /api/v1/sessions/{session_id}/stop`
- `GET /api/v1/sessions/{session_id}/events`
- `GET /api/v1/sessions/{session_id}/logs` for compatibility

## UI

The dashboard active sessions panel polls every five seconds and shows:

- status badges;
- selected games;
- last heartbeat;
- error message;
- recent events;
- Stop button;
- Retry recovery button for errored sessions.

## Tests

Covered by `apps/api/tests/test_session_manager.py`:

- cannot start session without subscription capacity;
- cannot start session for another user's account;
- cannot exceed plan limits;
- start is idempotent;
- stop is idempotent;
- mock client errors are persisted;
- session events are written.

## Manual QA Checklist

1. Start the stack: `docker compose up --build`.
2. Log in as admin seed or register a user.
3. Grant a paid plan in Admin or use mock billing webhook.
4. Add a Steam account in demo mode without entering a Steam password.
5. Login account and confirm status `online`.
6. Select games and save.
7. Start a session and confirm status `running`.
8. Confirm events show `session_started`.
9. Stop the session twice and confirm both calls are safe.
10. Simulate adapter error in tests and confirm `session_error`.
11. Stop the API/worker and confirm active sessions are closed on shutdown.
