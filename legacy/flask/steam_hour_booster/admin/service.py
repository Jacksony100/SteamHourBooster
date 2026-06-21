from datetime import datetime, timedelta

from steam_hour_booster.db import get_db

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def list_users(query: str = "") -> list[dict]:
    db = get_db()
    if query:
        rows = db.execute(
            "SELECT * FROM users WHERE username LIKE ? ORDER BY id DESC",
            (f"%{query}%",),
        ).fetchall()
    else:
        rows = db.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


def update_user_admin_state(payload: dict, actor_user_id: int | None = None) -> None:
    user_id = payload.get("user_id")
    if not user_id:
        raise ValueError("User ID is required")

    subscription_end = _subscription_end(payload.get("subscription_duration"))
    sub_end_str = subscription_end.strftime(DATE_FORMAT) if subscription_end else None
    is_admin = int(payload.get("is_admin", 0) or 0)
    banned = int(payload.get("banned", 0) or 0)

    db = get_db()
    db.execute(
        """
        UPDATE users
        SET subscription_end=?,
            is_admin=?,
            banned=?
        WHERE id=?
        """,
        (sub_end_str, is_admin, banned, user_id),
    )
    db.execute(
        """
        INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, metadata)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            actor_user_id,
            "admin.user_update",
            "user",
            str(user_id),
            f"subscription_duration={payload.get('subscription_duration')}; is_admin={is_admin}; banned={banned}",
        ),
    )
    db.commit()


def _subscription_end(option: str | None):
    if option == "1_week":
        return datetime.now() + timedelta(weeks=1)
    if option == "1_month":
        return datetime.now() + timedelta(days=30)
    if option == "3_months":
        return datetime.now() + timedelta(days=90)
    if option == "6_months":
        return datetime.now() + timedelta(days=180)
    if option == "12_months":
        return datetime.now() + timedelta(days=365)
    if option == "lifetime":
        return datetime(9999, 12, 31, 23, 59, 59)
    return None
