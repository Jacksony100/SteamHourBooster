from sqlalchemy.orm import Session

from app.core.models import SessionEvent, SteamSession, User
from app.sessions.manager import event_metadata, get_session_manager, parse_selected_games


def start_session(db: Session, user: User, account_id: int, steam_guard_code: str | None = None) -> SteamSession:
    return get_session_manager().start_session(db, user, account_id, steam_guard_code)


def stop_session(db: Session, user: User, session_id: int) -> SteamSession:
    return get_session_manager().stop_session(db, user, session_id)


def list_sessions(db: Session, user: User) -> list[SteamSession]:
    return get_session_manager().list_sessions(db, user)


def list_session_events(db: Session, user: User, session_id: int) -> list[SessionEvent]:
    return get_session_manager().list_events(db, user, session_id)


def serialize_session(session: SteamSession) -> dict:
    return {
        "id": session.id,
        "account_id": session.account_id,
        "status": session.status,
        "current_games": parse_selected_games(session),
        "selected_games": parse_selected_games(session),
        "started_at": session.started_at,
        "stopped_at": session.stopped_at,
        "last_heartbeat_at": session.last_heartbeat_at,
        "error_message": session.error_message,
    }


def serialize_event(event: SessionEvent) -> dict:
    return {
        "id": event.id,
        "session_id": event.session_id,
        "account_id": event.account_id,
        "event_type": event.event_type,
        "message": event.message,
        "metadata": event_metadata(event),
        "created_at": event.created_at,
    }
