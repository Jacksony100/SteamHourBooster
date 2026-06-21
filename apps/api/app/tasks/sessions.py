import time

from app.core.database import SessionLocal
from app.core.models import AccountStatus, SessionStatus
from app.sessions.manager import get_session_manager


def run_activity_session(session_id: int) -> None:
    """Demo/mock transparent session worker (legacy demo path).

    Records visible lifecycle state only. It does not implement stealth,
    platform-risk evasion, Steam Guard circumvention, network-routing evasion, or hidden automation.
    """

    db = SessionLocal()
    manager = get_session_manager()
    try:
        session = manager.worker_start(db, session_id)
        if not session or session.status != SessionStatus.running.value:
            return

        for _tick in range(3):
            time.sleep(5)
            session = manager.heartbeat(db, session_id)
            if not session or session.status in {SessionStatus.stopping.value, SessionStatus.stopped.value, SessionStatus.error.value}:
                break

        manager.worker_finish(db, session_id)
    finally:
        db.close()


def run_real_activity_session(session_id: int, steam_guard_code: str | None = None) -> None:
    """REAL owner-operated idle session (worker-only).

    Logs into an account the user owns, using the owner's credentials and the
    Steam Guard code they supplied at start time, and reports games as being
    played so playtime accrues. It is fully transparent: every step writes a
    session event, the session is stoppable on demand, and the connection is
    closed on stop / timeout. It deliberately implements NO Steam Guard bypass,
    anti-detect, proxy rotation, ban evasion, or hidden behavior.

    The Steam protocol library is imported lazily so the API image never depends
    on it; only the worker image installs it.
    """

    from app.core.config import get_settings
    from app.core.models import DEMO_NO_PASSWORD_MARKER, SteamSession, User
    from app.core.security import encryption_service
    from app.sessions.manager import now_utc, parse_selected_games, update_account_status, write_session_event
    from app.sessions.runtime import get_runtime_store

    db = SessionLocal()
    runtime = get_runtime_store()
    settings = get_settings()

    def event(session: "SteamSession", user_id: int, event_type: str, message: str) -> None:
        write_session_event(db, event_type=event_type, user_id=user_id, account_id=session.account_id, session_id=session.id, message=message)

    def fail(session: "SteamSession", message: str) -> None:
        session.status = SessionStatus.error.value
        session.error_message = message
        session.stopped_at = session.stopped_at or now_utc()
        session.updated_at = now_utc()
        update_account_status(db, session.account, status_value=AccountStatus.error.value, event_type="session_error", error_message=message)
        event(session, session.user_id, "session_error", message)
        db.commit()

    client = None
    account_id_locked: int | None = None
    try:
        session = db.get(SteamSession, session_id)
        if not session or session.status != SessionStatus.starting.value:
            return
        account = session.account
        user = db.get(User, session.user_id)
        game_ids = parse_selected_games(session)

        # Per-account concurrency guard: one live idle per account across all workers.
        if not runtime.acquire(account.id):
            fail(session, "This account already has a live session on another worker")
            return
        account_id_locked = account.id

        try:
            username = encryption_service.decrypt(account.username_encrypted)
            stored_password = encryption_service.decrypt(account.password_encrypted)
            refresh_token = encryption_service.decrypt(account.steam_refresh_token_encrypted) if account.steam_refresh_token_encrypted else None
        except Exception:
            fail(session, "Could not decrypt stored credentials")
            return
        password = None if (not stored_password or stored_password == DEMO_NO_PASSWORD_MARKER) else stored_password

        try:
            from steam.client import SteamClient
            from steam.enums import EResult
        except ImportError:
            fail(session, "Steam client library is not installed in the worker image")
            return

        client = SteamClient()

        # Prefer the saved refresh token / login_key (revocable, no Guard prompt);
        # fall back to password + the owner-supplied single-use Steam Guard code.
        result = None
        if refresh_token:
            try:
                result = client.login(username=username, login_key=refresh_token)
            except Exception:
                result = None
        if result != EResult.OK:
            if not password:
                fail(session, "No stored credentials to log in — re-link the account with its password")
                return
            result = client.login(username=username, password=password, two_factor_code=steam_guard_code, auth_code=steam_guard_code)

        if result != EResult.OK:
            guard_results = {
                getattr(EResult, "AccountLogonDenied", None),
                getattr(EResult, "AccountLoginDeniedNeedTwoFactor", None),
                getattr(EResult, "TwoFactorCodeMismatch", None),
                getattr(EResult, "InvalidLoginAuthCode", None),
            }
            if result in guard_results:
                fail(session, "Steam Guard code is required or invalid — restart the session with a fresh code")
            else:
                fail(session, f"Steam login failed ({getattr(result, 'name', result)})")
            return

        # Capture a fresh login_key / refresh token so future sessions skip the password.
        try:
            new_key = getattr(client, "login_key", None)
            if not new_key:
                captured = client.wait_event(SteamClient.EVENT_NEW_LOGIN_KEY, timeout=10)
                new_key = getattr(client, "login_key", None) or (captured[0] if captured else None)
            if new_key:
                account.steam_refresh_token_encrypted = encryption_service.encrypt(str(new_key))
                if settings.steam_drop_password_after_link:
                    account.password_encrypted = encryption_service.encrypt(DEMO_NO_PASSWORD_MARKER)
                event(session, session.user_id, "session_token_saved", "Saved a Steam refresh token; password no longer required for this account")
        except Exception:
            pass  # token capture is best-effort; password fallback remains

        # Logged in — mark running and start idling.
        session.steamid64 = str(client.steam_id.as_64)
        account.steamid64 = session.steamid64
        account.last_login_at = now_utc()
        session.status = SessionStatus.running.value
        session.started_at = session.started_at or now_utc()
        session.last_heartbeat_at = now_utc()
        session.error_message = None
        session.updated_at = now_utc()
        update_account_status(db, account, status_value=AccountStatus.online.value, event_type="session_started")
        event(session, user.id if user else session.user_id, "session_started", "Real Steam session is online and idling selected games")
        db.commit()

        client.games_played(game_ids)

        deadline = time.monotonic() + settings.steam_session_max_minutes * 60
        reconnect_failures = 0
        while True:
            client.sleep(30)  # gevent-friendly; keeps the CM connection alive

            # Reconnect with bounded exponential backoff if the connection dropped.
            if not getattr(client, "connected", True):
                backoff = min(60, 5 * (2**reconnect_failures))
                reconnected = False
                try:
                    reconnected = bool(client.reconnect(maxdelay=backoff, retry=1))
                    if reconnected and getattr(client, "relogin_available", False):
                        client.relogin()
                except Exception:
                    reconnected = False
                if not reconnected:
                    reconnect_failures += 1
                    if reconnect_failures >= 5:
                        fail(db.get(SteamSession, session_id) or session, "Lost connection to Steam and could not reconnect")
                        break
                    continue
                reconnect_failures = 0
                client.games_played(game_ids)
                event(db.get(SteamSession, session_id) or session, session.user_id, "session_reconnected", "Reconnected to Steam and resumed idling")

            db.expire(session)
            current = db.get(SteamSession, session_id)
            if not current or current.status in {SessionStatus.stopping.value, SessionStatus.stopped.value, SessionStatus.error.value}:
                break
            if runtime.is_stop_requested(session_id):
                break
            if time.monotonic() >= deadline:
                event(current, current.user_id, "session_timeout", "Reached max session duration; stopping")
                break
            client.games_played(game_ids)  # re-assert presence
            current.last_heartbeat_at = now_utc()
            current.updated_at = now_utc()
            update_account_status(db, current.account, status_value=AccountStatus.online.value, event_type="session_heartbeat")
            db.commit()

        # Graceful stop.
        try:
            client.games_played([])
            client.logout()
        except Exception:
            pass
        final = db.get(SteamSession, session_id)
        if final and final.status not in {SessionStatus.error.value, SessionStatus.stopped.value}:
            final.status = SessionStatus.stopped.value
            final.stopped_at = now_utc()
            final.updated_at = now_utc()
            update_account_status(db, final.account, status_value=AccountStatus.offline.value, event_type="session_stopped")
            event(final, final.user_id, "session_stopped", "Real Steam session stopped and logged out")
            db.commit()
    except Exception as exc:  # never leak credentials in the message
        try:
            session = db.get(SteamSession, session_id)
            if session:
                fail(session, f"Session worker error: {type(exc).__name__}")
        except Exception:
            pass
    finally:
        if client is not None:
            try:
                client.logout()
            except Exception:
                pass
        runtime.clear_stop(session_id)
        if account_id_locked is not None:
            runtime.release(account_id_locked)
        db.close()
