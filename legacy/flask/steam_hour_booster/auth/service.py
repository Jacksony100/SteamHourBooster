from datetime import datetime

from flask import current_app

from steam_hour_booster.db import get_db
from steam_hour_booster.security.password_service import (
    hash_password,
    is_password_hash,
    verify_password,
)


DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def register_user(username: str, password: str) -> bool:
    username = (username or "").strip()
    if not username:
        raise ValueError("Username is required")

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
    if existing:
        return False

    db.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        (username, hash_password(password)),
    )
    db.commit()
    return True


def verify_user(username: str, password: str) -> dict | None:
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", ((username or "").strip(),)).fetchone()
    if not user or user["banned"] == 1:
        return None

    stored_password = user["password"]
    if verify_password(stored_password, password):
        return dict(user)

    if not is_password_hash(stored_password) and _verify_legacy_fernet_password(stored_password, password):
        db.execute(
            "UPDATE users SET password=? WHERE id=?",
            (hash_password(password), user["id"]),
        )
        db.commit()
        refreshed = db.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone()
        return dict(refreshed)

    return None


def _verify_legacy_fernet_password(stored_password: str, candidate_password: str) -> bool:
    try:
        encryption = current_app.extensions["encryption_service"]
        return encryption.decrypt(stored_password) == candidate_password
    except Exception:
        return False


def get_user(user_id: int) -> dict | None:
    row = get_db().execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return dict(row) if row else None


def touch_last_seen(user_id: int) -> None:
    now = datetime.now().strftime(DATE_FORMAT)
    db = get_db()
    db.execute("UPDATE users SET last_seen=? WHERE id=?", (now, user_id))
    db.commit()


def record_login(user_id: int, ip_address: str) -> None:
    db = get_db()
    db.execute("UPDATE users SET last_ip=? WHERE id=?", (ip_address, user_id))
    db.commit()


def has_active_subscription(user: dict | None) -> bool:
    if not user or not user.get("subscription_end"):
        return False
    try:
        return datetime.strptime(user["subscription_end"], DATE_FORMAT) >= datetime.now()
    except ValueError:
        return False


def is_admin(user: dict | None) -> bool:
    return bool(user and user.get("is_admin") == 1)
