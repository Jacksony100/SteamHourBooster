import sqlite3
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

from flask import current_app, g


def _sqlite_path(database_url: str) -> Path:
    if database_url.startswith("sqlite:///"):
        raw_path = database_url[len("sqlite:///") :]
        return Path(raw_path)
    if database_url.startswith("sqlite://"):
        raw_path = database_url[len("sqlite://") :]
        return Path(raw_path)
    return Path(database_url)


def get_database_path() -> Path:
    return _sqlite_path(current_app.config["DATABASE_URL"])


def connect(database_url: str | None = None) -> sqlite3.Connection:
    if database_url is None:
        database_url = current_app.config["DATABASE_URL"]

    database_path = _sqlite_path(database_url)
    if database_path.parent and str(database_path.parent) not in ("", "."):
        database_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(database_path, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = connect()
    return g.db


def close_db(_error=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


@contextmanager
def open_db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def db_connection(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        with open_db() as conn:
            return fn(conn, *args, **kwargs)

    return wrapped


def run_migrations(app) -> None:
    migrations_dir = Path(app.root_path).parent / "migrations"
    with app.app_context():
        with open_db() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            applied = {
                row["version"]
                for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
            }

            for migration in sorted(migrations_dir.glob("*.sql")):
                version = migration.stem
                if version in applied:
                    continue
                conn.executescript(migration.read_text(encoding="utf-8"))
                conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)",
                    (version,),
                )


def init_db(app) -> None:
    app.teardown_appcontext(close_db)
    run_migrations(app)
