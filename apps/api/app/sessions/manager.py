import json
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit.service import write_audit
from app.billing.service import assert_active_session_limit
from app.core.config import get_settings
from app.core.models import AccountStatus, AccountStatusRecord, SessionEvent, SessionStatus, SteamAccount, SteamSession, User
from app.sessions.adapters import SteamClientAdapter, get_steam_client_adapter

ACTIVE_SESSION_STATUSES = {SessionStatus.starting.value, SessionStatus.running.value, SessionStatus.stopping.value}
TERMINAL_SESSION_STATUSES = {SessionStatus.stopped.value, SessionStatus.error.value}


def now_utc() -> datetime:
    return datetime.now(UTC)


def selected_game_ids(account: SteamAccount) -> list[int]:
    return [link.game.app_id for link in account.selected_games]


def parse_selected_games(session: SteamSession) -> list[int]:
    try:
        return list(json.loads(session.selected_games or "[]"))
    except json.JSONDecodeError:
        return []


def event_metadata(event: SessionEvent) -> dict:
    try:
        return dict(json.loads(event.metadata_json or "{}"))
    except json.JSONDecodeError:
        return {}


def write_session_event(
    db: Session,
    *,
    event_type: str,
    user_id: int,
    account_id: int | None = None,
    session_id: int | None = None,
    message: str,
    metadata: dict | None = None,
) -> SessionEvent:
    event = SessionEvent(
        session_id=session_id,
        user_id=user_id,
        account_id=account_id,
        event_type=event_type,
        message=message,
        metadata_json=json.dumps(metadata or {}),
    )
    db.add(event)
    return event


def update_account_status(
    db: Session,
    account: SteamAccount,
    *,
    status_value: str,
    event_type: str,
    error_message: str | None = None,
) -> AccountStatusRecord:
    now = now_utc()
    record = db.query(AccountStatusRecord).filter(AccountStatusRecord.account_id == account.id).one_or_none()
    if not record:
        record = AccountStatusRecord(account_id=account.id)
        db.add(record)
    record.status = status_value
    record.last_event = event_type
    record.error_message = error_message
    record.updated_at = now
    if status_value == AccountStatus.online.value:
        record.last_heartbeat_at = now
    account.status = status_value
    return record


def record_account_event(
    db: Session,
    user: User,
    account: SteamAccount,
    *,
    event_type: str,
    message: str,
    metadata: dict | None = None,
    commit: bool = True,
) -> SessionEvent:
    event = write_session_event(
        db,
        event_type=event_type,
        user_id=user.id,
        account_id=account.id,
        message=message,
        metadata=metadata,
    )
    if commit:
        db.commit()
        db.refresh(event)
    return event


class SessionManager:
    def __init__(self, adapter: SteamClientAdapter | None = None) -> None:
        self.adapter = adapter or get_steam_client_adapter()

    def list_sessions(self, db: Session, user: User) -> list[SteamSession]:
        return db.query(SteamSession).filter(SteamSession.user_id == user.id).order_by(SteamSession.id.desc()).limit(30).all()

    def list_events(self, db: Session, user: User, session_id: int) -> list[SessionEvent]:
        session = self.session_for_owner(db, user, session_id)
        return db.query(SessionEvent).filter(SessionEvent.session_id == session.id).order_by(SessionEvent.id.desc()).limit(100).all()

    def session_for_owner(self, db: Session, user: User, session_id: int) -> SteamSession:
        session = db.query(SteamSession).filter(SteamSession.id == session_id, SteamSession.user_id == user.id).one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return session

    def start_session(self, db: Session, user: User, account_id: int) -> SteamSession:
        settings = get_settings()
        if settings.steam_integration_mode != "demo":
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Official Steam sessions are not configured yet")
        account = db.query(SteamAccount).filter(SteamAccount.id == account_id, SteamAccount.user_id == user.id).one_or_none()
        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        if account.status != AccountStatus.online.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account must be online")

        game_ids = selected_game_ids(account)
        if not game_ids:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select at least one game")

        existing = (
            db.query(SteamSession)
            .filter(
                SteamSession.user_id == user.id,
                SteamSession.account_id == account.id,
                SteamSession.status.in_(list(ACTIVE_SESSION_STATUSES)),
            )
            .order_by(SteamSession.id.desc())
            .first()
        )
        if existing:
            return existing

        assert_active_session_limit(db, user)
        now = now_utc()
        session = SteamSession(
            user_id=user.id,
            account_id=account.id,
            status=SessionStatus.starting.value,
            selected_games=json.dumps(game_ids),
            updated_at=now,
        )
        db.add(session)
        db.flush()

        # Demo mode runs the transparent session lifecycle synchronously and persists
        # all state to the DB (steam_sessions / session_events / account_status). The
        # RQ worker (app/tasks/sessions.py) is reserved for a future official-linking
        # mode and is intentionally NOT engaged here, so a session never sits in a
        # phantom "queued" state with no worker to process it.
        self._activate_session(db, session, account, game_ids, raise_on_error=True)

        db.refresh(session)
        write_audit(db, "session.start", "steam_session", session.id, user, {"account_id": account.id})
        return session

    def stop_session(self, db: Session, user: User, session_id: int) -> SteamSession:
        session = self.session_for_owner(db, user, session_id)
        if session.status in TERMINAL_SESSION_STATUSES:
            return session

        account = session.account
        game_ids = parse_selected_games(session)
        if session.status == SessionStatus.stopping.value and not get_settings().steam_test_mode:
            return session

        session.status = SessionStatus.stopping.value
        session.updated_at = now_utc()
        db.flush()

        result = self.adapter.stop_session(account, game_ids)
        if not result.ok:
            self._mark_error(db, session, account, result.error or "Steam client failed to stop session")
            db.commit()
            db.refresh(session)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=session.error_message)

        self._mark_stopped(db, session, account, "Transparent session stopped")
        db.commit()
        db.refresh(session)
        write_audit(db, "session.stop", "steam_session", session.id, user, {"account_id": account.id})
        return session

    def worker_start(self, db: Session, session_id: int) -> SteamSession | None:
        session = db.get(SteamSession, session_id)
        if not session or session.status != SessionStatus.starting.value:
            return session
        self._activate_session(db, session, session.account, parse_selected_games(session), raise_on_error=False)
        db.commit()
        db.refresh(session)
        return session

    def heartbeat(self, db: Session, session_id: int) -> SteamSession | None:
        session = db.get(SteamSession, session_id)
        if not session or session.status != SessionStatus.running.value:
            return session
        game_ids = parse_selected_games(session)
        result = self.adapter.heartbeat(session.account, game_ids)
        if not result.ok:
            self._mark_error(db, session, session.account, result.error or "Steam client heartbeat failed")
        else:
            now = now_utc()
            session.last_heartbeat_at = now
            session.updated_at = now
            status_record = update_account_status(
                db,
                session.account,
                status_value=AccountStatus.online.value,
                event_type="session_heartbeat",
            )
            status_record.last_heartbeat_at = now
        db.commit()
        db.refresh(session)
        return session

    def worker_finish(self, db: Session, session_id: int) -> SteamSession | None:
        session = db.get(SteamSession, session_id)
        if not session or session.status in TERMINAL_SESSION_STATUSES:
            return session
        result = self.adapter.stop_session(session.account, parse_selected_games(session))
        if not result.ok:
            self._mark_error(db, session, session.account, result.error or "Steam client failed to stop session")
        else:
            self._mark_stopped(db, session, session.account, "Transparent worker completed session lifecycle")
        db.commit()
        db.refresh(session)
        return session

    def shutdown_active_sessions(self, db: Session) -> None:
        sessions = db.query(SteamSession).filter(SteamSession.status.in_(list(ACTIVE_SESSION_STATUSES))).all()
        for session in sessions:
            result = self.adapter.stop_session(session.account, parse_selected_games(session))
            if result.ok:
                self._mark_stopped(db, session, session.account, "Application shutdown closed Steam client")
                update_account_status(db, session.account, status_value=AccountStatus.offline.value, event_type="app_shutdown")
            else:
                self._mark_error(db, session, session.account, result.error or "Application shutdown failed to close Steam client")
        self.adapter.close_all()
        db.commit()

    def _activate_session(
        self,
        db: Session,
        session: SteamSession,
        account: SteamAccount,
        game_ids: list[int],
        *,
        raise_on_error: bool,
    ) -> None:
        result = self.adapter.start_session(account, game_ids)
        if not result.ok:
            self._mark_error(db, session, account, result.error or "Steam client failed to start session")
            db.commit()
            if raise_on_error:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=session.error_message)
            return

        now = now_utc()
        session.status = SessionStatus.running.value
        session.started_at = session.started_at or now
        session.last_heartbeat_at = now
        session.error_message = None
        session.updated_at = now
        update_account_status(db, account, status_value=AccountStatus.online.value, event_type="session_started")
        write_session_event(
            db,
            event_type="session_started",
            user_id=session.user_id,
            account_id=account.id,
            session_id=session.id,
            message="Transparent session started",
            metadata={"selected_games": game_ids},
        )
        db.commit()

    def _mark_stopped(self, db: Session, session: SteamSession, account: SteamAccount, message: str) -> None:
        now = now_utc()
        session.status = SessionStatus.stopped.value
        session.stopped_at = session.stopped_at or now
        session.updated_at = now
        update_account_status(db, account, status_value=AccountStatus.online.value, event_type="session_stopped")
        write_session_event(
            db,
            event_type="session_stopped",
            user_id=session.user_id,
            account_id=account.id,
            session_id=session.id,
            message=message,
            metadata={"selected_games": parse_selected_games(session)},
        )

    def _mark_error(self, db: Session, session: SteamSession, account: SteamAccount, error_message: str) -> None:
        now = now_utc()
        session.status = SessionStatus.error.value
        session.error_message = error_message
        session.stopped_at = session.stopped_at or now
        session.updated_at = now
        update_account_status(db, account, status_value=AccountStatus.error.value, event_type="session_error", error_message=error_message)
        write_session_event(
            db,
            event_type="session_error",
            user_id=session.user_id,
            account_id=account.id,
            session_id=session.id,
            message=error_message,
            metadata={"selected_games": parse_selected_games(session)},
        )


def get_session_manager() -> SessionManager:
    return SessionManager()
