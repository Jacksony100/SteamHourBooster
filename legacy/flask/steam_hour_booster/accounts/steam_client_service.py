import logging
from concurrent.futures import ThreadPoolExecutor

from flask import current_app

logger = logging.getLogger(__name__)

clients = {}
executor = ThreadPoolExecutor(max_workers=5)


def _sleep(seconds: int) -> None:
    try:
        import gevent

        gevent.sleep(seconds)
    except ImportError:
        import time

        time.sleep(seconds)


def _steam_imports():
    try:
        from steam.client import SteamClient
        from steam.enums import EResult
    except ImportError as exc:
        raise RuntimeError("Steam integration dependency is not installed") from exc
    return SteamClient, EResult


def is_logged_in(username: str) -> bool:
    return username in clients


def login_steam(account: dict, steam_guard_code: str | None = None) -> dict:
    from .service import decrypt_account_password, decrypt_account_username, update_steamid64

    try:
        username = decrypt_account_username(account)
        password = decrypt_account_password(account)
    except ValueError:
        return {"success": False, "error": "Ошибка расшифровки"}

    logger.info("Attempting Steam login for account_id=%s", account["id"])
    try:
        SteamClient, EResult = _steam_imports()
        client = SteamClient()
        result = client.login(username=username, password=password, auth_code=steam_guard_code)
        if result == EResult.OK:
            steamid64 = str(client.steam_id.as_64)
            update_steamid64(account["id"], steamid64)
            clients[username] = {
                "client": client,
                "account_id": account["id"],
            }
            executor.submit(client.run_forever)
            logger.info("Steam login succeeded for account_id=%s", account["id"])
            return {"success": True}
        if result in (EResult.AccountLogonDenied, EResult.InvalidLoginAuthCode):
            logger.warning("SteamGuard required for account_id=%s", account["id"])
            return {"success": False, "need_steam_guard": True, "error": "SteamGuard required"}

        logger.error("Steam login failed for account_id=%s result=%s", account["id"], result)
        return {"success": False, "error": f"Login failed ({result})"}
    except Exception as exc:
        logger.exception("Steam login exception for account_id=%s", account["id"])
        if current_app.config.get("TESTING"):
            raise
        return {"success": False, "error": "Steam login failed. Please verify the account state and try again."}


def logout_account_session(username: str) -> bool:
    if username not in clients:
        return False
    stop_farming_for_username(username)
    clients[username]["client"].logout()
    del clients[username]
    logger.info("Steam account session logged out")
    return True


def farm_loop(account_id: int, username: str, client, game_ids: list[int]) -> None:
    minutes_counter = {gid: 0 for gid in game_ids}
    logger.info("Activity loop started for account_id=%s games=%s", account_id, game_ids)
    while True:
        try:
            client.games_played(game_ids)
            for gid in game_ids:
                minutes_counter[gid] += 1
        except Exception:
            logger.exception("Activity loop error for account_id=%s", account_id)
            break
        _sleep(60)
    try:
        client.games_played([])
    except Exception:
        logger.exception("Unable to stop games for account_id=%s", account_id)
    logger.info("Activity loop stopped for account_id=%s", account_id)


def start_farming_for_username(username: str) -> dict:
    from steam_hour_booster.games.service import get_account_games

    if username not in clients:
        return {"success": False, "error": "Account not logged in"}
    client_data = clients[username]
    account_id = client_data["account_id"]
    game_ids = [game["game_id"] for game in get_account_games(account_id)]
    if not game_ids:
        return {"success": False, "error": "No games selected for farming"}
    if "farming_greenlet" in client_data:
        client_data["farming_greenlet"].kill()

    try:
        import gevent
    except ImportError:
        return {"success": False, "error": "Background runtime is not installed"}

    greenlet = gevent.spawn(farm_loop, account_id, username, client_data["client"], game_ids)
    client_data["farming_greenlet"] = greenlet
    return {"success": True, "games": game_ids}


def stop_farming_for_username(username: str) -> dict:
    if username not in clients:
        return {"success": False, "error": "Account not logged in"}
    client_data = clients[username]
    if "farming_greenlet" in client_data:
        client_data["farming_greenlet"].kill()
        del client_data["farming_greenlet"]
        return {"success": True}
    return {"success": False, "error": "Farming not running"}
