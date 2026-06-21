import signal
import sys

from redis import Redis
from rq import Queue, Worker

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.sessions.manager import get_session_manager

shutdown_requested = False


def _handle_shutdown(_signum, _frame):
    global shutdown_requested
    shutdown_requested = True


def _shutdown_sessions() -> None:
    db = SessionLocal()
    try:
        get_session_manager().shutdown_active_sessions(db)
    finally:
        db.close()


def main() -> None:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    queue = Queue("sessions", connection=redis)
    worker = Worker([queue], connection=redis)
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)
    try:
        worker.work(with_scheduler=False)
    finally:
        if shutdown_requested:
            _shutdown_sessions()
            sys.exit(0)


if __name__ == "__main__":
    main()
