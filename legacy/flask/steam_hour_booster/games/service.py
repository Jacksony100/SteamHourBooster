import logging

import requests
from flask import current_app

from steam_hour_booster.accounts.service import decrypt_account_username, get_account_row
from steam_hour_booster.accounts.steam_client_service import is_logged_in
from steam_hour_booster.db import get_db

logger = logging.getLogger(__name__)
STEAM_TIMEOUT_SECONDS = 15


def get_account_games(account_id: int) -> list[dict]:
    rows = get_db().execute(
        """
        SELECT g.game_id, g.game_name
        FROM games g
        JOIN account_games ag ON g.id = ag.game_id
        WHERE ag.account_id = ?
        ORDER BY g.game_name
        """,
        (account_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def add_games_for_account(account_id: int, games: list[dict]) -> int:
    db = get_db()
    db.execute("DELETE FROM account_games WHERE account_id=?", (account_id,))
    for game in games:
        app_id = int(game["app_id"])
        name = str(game.get("name") or f"App {app_id}")
        db.execute(
            "INSERT OR IGNORE INTO games (game_id, game_name) VALUES (?, ?)",
            (app_id, name),
        )
        row = db.execute("SELECT id FROM games WHERE game_id=?", (app_id,)).fetchone()
        if row:
            db.execute(
                "INSERT OR IGNORE INTO account_games (account_id, game_id) VALUES (?, ?)",
                (account_id, row["id"]),
            )
    db.commit()
    return len(games)


def update_account_games(user_id: int, account_id: int, games: list[dict]) -> int | None:
    account = get_account_row(account_id, user_id)
    if not account:
        return None
    return add_games_for_account(account["id"], games)


def fetch_owned_games(user_id: int, account_id: int) -> dict:
    account = get_account_row(account_id, user_id)
    if not account:
        return {"success": False, "error": "Account not found"}

    username = decrypt_account_username(account)
    if not is_logged_in(username):
        return {"success": False, "error": "Account not logged in"}
    if not account.get("steamid64"):
        return {"success": False, "error": "SteamID64 not found"}

    params = {
        "key": current_app.config["STEAM_API_KEY"],
        "steamid": account["steamid64"],
        "include_appinfo": 1,
        "include_played_free_games": 1,
        "format": "json",
    }
    try:
        response = requests.get(
            "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/",
            params=params,
            timeout=STEAM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        games = payload.get("response", {}).get("games", [])
        return {
            "success": True,
            "games": [
                {"app_id": game["appid"], "name": game.get("name", f"App {game['appid']}")}
                for game in games
            ],
        }
    except requests.Timeout:
        logger.warning("Steam owned games request timed out for account_id=%s", account_id)
        return {"success": False, "error": "Steam API request timed out. Please try again later."}
    except requests.RequestException:
        logger.exception("Steam owned games request failed for account_id=%s", account_id)
        return {"success": False, "error": "Steam API is unavailable. Please try again later."}
    except ValueError:
        logger.exception("Steam owned games response was invalid for account_id=%s", account_id)
        return {"success": False, "error": "Steam API returned an invalid response."}


def get_ban_info(user_id: int, account_id: int) -> dict:
    account = get_account_row(account_id, user_id)
    if not account:
        return {"success": False, "error": "Account not found"}

    username = decrypt_account_username(account)
    if not is_logged_in(username):
        return {"success": False, "error": "Account not logged in"}
    if not account.get("steamid64"):
        return {"success": False, "error": "SteamID64 not found"}

    params = {
        "key": current_app.config["STEAM_API_KEY"],
        "steamids": account["steamid64"],
    }
    try:
        response = requests.get(
            "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/",
            params=params,
            timeout=STEAM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        players = payload.get("players") or []
        return {"success": True, "bans": players[0] if players else []}
    except requests.Timeout:
        logger.warning("Steam ban info request timed out for account_id=%s", account_id)
        return {"success": False, "error": "Steam API request timed out. Please try again later."}
    except requests.RequestException:
        logger.exception("Steam ban info request failed for account_id=%s", account_id)
        return {"success": False, "error": "Steam API is unavailable. Please try again later."}
    except ValueError:
        logger.exception("Steam ban info response was invalid for account_id=%s", account_id)
        return {"success": False, "error": "Steam API returned an invalid response."}
