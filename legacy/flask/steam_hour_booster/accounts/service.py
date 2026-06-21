from flask import current_app

from steam_hour_booster.db import get_db


def _encryption():
    return current_app.extensions["encryption_service"]


def get_account_row(account_id: int, user_id: int) -> dict | None:
    row = get_db().execute(
        "SELECT * FROM accounts WHERE id=? AND user_id=?",
        (account_id, user_id),
    ).fetchone()
    return dict(row) if row else None


def get_accounts_for_user(user_id: int) -> list[dict]:
    from steam_hour_booster.games.service import get_account_games
    from .steam_client_service import is_logged_in

    rows = get_db().execute("SELECT * FROM accounts WHERE user_id=?", (user_id,)).fetchall()
    accounts = []
    for row in rows:
        account = dict(row)
        username = decrypt_account_username(account)
        accounts.append(
            {
                "id": account["id"],
                "username": username,
                "steamid64": account["steamid64"],
                "status": "online" if is_logged_in(username) else "offline",
                "active_games": get_account_games(account["id"]),
            }
        )
    return accounts


def add_account(user_id: int, payload: dict) -> int:
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    # Keep the DB column/API shape for compatibility, but do not collect or store
    # Steam Guard shared secrets.
    shared_secret = ""
    if not username:
        raise ValueError("Username is required")
    if not password:
        raise ValueError("Password is required")

    encryption = _encryption()
    db = get_db()
    cur = db.execute(
        """
        INSERT INTO accounts (username, password, shared_secret, steamid64, user_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            encryption.encrypt(username),
            encryption.encrypt(password),
            encryption.encrypt(shared_secret),
            "",
            user_id,
        ),
    )
    db.commit()
    return cur.lastrowid


def delete_account(account_id: int, user_id: int) -> bool:
    from .steam_client_service import logout_account_session, stop_farming_for_username

    account = get_account_row(account_id, user_id)
    if not account:
        return False

    username = decrypt_account_username(account)
    stop_farming_for_username(username)
    logout_account_session(username)

    db = get_db()
    db.execute("DELETE FROM account_games WHERE account_id=?", (account_id,))
    db.execute("DELETE FROM accounts WHERE id=? AND user_id=?", (account_id, user_id))
    db.commit()
    return True


def update_steamid64(account_id: int, steamid64: str) -> None:
    db = get_db()
    db.execute("UPDATE accounts SET steamid64=? WHERE id=?", (steamid64, account_id))
    db.commit()


def decrypt_account_username(account: dict) -> str:
    return _encryption().decrypt(account["username"])


def decrypt_account_password(account: dict) -> str:
    return _encryption().decrypt(account["password"])
