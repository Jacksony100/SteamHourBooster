from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import active_subscription, current_user, require_csrf
from app.core.models import User
from app.core.rate_limit import rate_limit
from app.sessions.schemas import ActivitySessionResponse, SessionLogResponse, StartSessionRequest
from app.sessions.service import list_session_events, serialize_event, serialize_session, start_session, stop_session
from app.sessions.service import list_sessions as list_user_sessions

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[ActivitySessionResponse])
def list_sessions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = list_user_sessions(db, user)
    return [ActivitySessionResponse(**serialize_session(row)) for row in rows]


@router.post("", response_model=ActivitySessionResponse, dependencies=[Depends(require_csrf), Depends(rate_limit("session_start", 20, 60))])
def start(payload: StartSessionRequest, user: User = Depends(active_subscription), db: Session = Depends(get_db)):
    return ActivitySessionResponse(**serialize_session(start_session(db, user, payload.account_id)))


@router.post("/{session_id}/stop", response_model=ActivitySessionResponse, dependencies=[Depends(require_csrf), Depends(rate_limit("session_stop", 30, 60))])
def stop(session_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return ActivitySessionResponse(**serialize_session(stop_session(db, user, session_id)))


@router.get("/{session_id}/logs", response_model=list[SessionLogResponse])
def logs(session_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [SessionLogResponse(**serialize_event(row)) for row in list_session_events(db, user, session_id)]


@router.get("/{session_id}/events", response_model=list[SessionLogResponse])
def events(session_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [SessionLogResponse(**serialize_event(row)) for row in list_session_events(db, user, session_id)]
