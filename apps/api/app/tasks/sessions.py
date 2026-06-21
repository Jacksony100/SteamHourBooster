import time

from app.core.database import SessionLocal
from app.core.models import SessionStatus
from app.sessions.manager import get_session_manager


def run_activity_session(session_id: int) -> None:
    """Transparent session worker.

    This records visible lifecycle state only. It does not implement stealth,
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
