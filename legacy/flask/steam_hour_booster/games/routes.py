from flask import Blueprint, jsonify, request, session

from steam_hour_booster.app import json_error
from steam_hour_booster.auth.decorators import login_required
from steam_hour_booster.security.rate_limit import rate_limit

from .service import fetch_owned_games, get_ban_info, update_account_games


games_bp = Blueprint("games", __name__)


def _json_payload() -> dict:
    return request.get_json(silent=True) or {}


@games_bp.route("/fetch_owned_games", methods=["POST"])
@login_required
@rate_limit("fetch_owned_games", limit=30, seconds=60)
def api_fetch_owned_games():
    payload = _json_payload()
    return jsonify(fetch_owned_games(session["user_id"], payload.get("account_id")))


@games_bp.route("/update_account_games", methods=["POST"])
@login_required
@rate_limit("update_account_games", limit=30, seconds=60)
def api_update_account_games():
    payload = _json_payload()
    account_id = payload.get("account_id")
    games = payload.get("games", [])
    if not account_id:
        return json_error("Account not found", 404, "account_not_found")
    count = update_account_games(session["user_id"], int(account_id), games)
    if count is None:
        return json_error("Account not found", 404, "account_not_found")
    return jsonify({"success": True, "count": count})


@games_bp.route("/ban_info", methods=["POST"])
@login_required
@rate_limit("ban_info", limit=30, seconds=60)
def api_ban_info():
    payload = _json_payload()
    account_id = payload.get("account_id")
    if not account_id:
        return json_error("Account ID not provided", 400, "account_id_required")
    return jsonify(get_ban_info(session["user_id"], int(account_id)))
