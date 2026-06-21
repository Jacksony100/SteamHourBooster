from flask import Blueprint, jsonify, request, session

from steam_hour_booster.app import json_error
from steam_hour_booster.auth.decorators import login_required
from steam_hour_booster.security.rate_limit import rate_limit

from .service import add_account, decrypt_account_username, delete_account, get_account_row, get_accounts_for_user
from .steam_client_service import (
    login_steam,
    logout_account_session,
    start_farming_for_username,
    stop_farming_for_username,
)


accounts_bp = Blueprint("accounts", __name__)


def _json_payload() -> dict:
    return request.get_json(silent=True) or {}


@accounts_bp.route("/get_accounts", methods=["GET"])
@login_required
def api_get_accounts():
    return jsonify(get_accounts_for_user(session["user_id"]))


@accounts_bp.route("/add_account", methods=["POST"])
@login_required
@rate_limit("add_account", limit=20, seconds=60)
def api_add_account():
    payload = _json_payload()
    account_id = add_account(session["user_id"], payload)
    return jsonify({"success": True, "account_id": account_id})


@accounts_bp.route("/delete_account", methods=["POST"])
@login_required
@rate_limit("delete_account", limit=20, seconds=60)
def api_delete_account():
    account_id = _json_payload().get("id")
    if not account_id:
        return json_error("Account ID not provided", 400, "account_id_required")
    if not delete_account(int(account_id), session["user_id"]):
        return json_error("Account not found", 404, "account_not_found")
    return jsonify({"success": True})


@accounts_bp.route("/login_account", methods=["POST"])
@login_required
@rate_limit("login_account", limit=20, seconds=60)
def api_login_account():
    payload = _json_payload()
    account_id = payload.get("id")
    account = get_account_row(account_id, session["user_id"]) if account_id else None
    if not account:
        return json_error("Account not found", 404, "account_not_found")
    return jsonify(login_steam(account, payload.get("steam_guard_code")))


@accounts_bp.route("/logout_account", methods=["POST"])
@login_required
@rate_limit("logout_account", limit=30, seconds=60)
def api_logout_account():
    payload = _json_payload()
    account_id = payload.get("account_id")
    account = get_account_row(account_id, session["user_id"]) if account_id else None
    if not account:
        return json_error("Account not found", 404, "account_not_found")
    username = decrypt_account_username(account)
    if logout_account_session(username):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Account not logged in"})


@accounts_bp.route("/start_farming", methods=["POST"])
@login_required
@rate_limit("start_session", limit=20, seconds=60)
def api_start_farming():
    payload = _json_payload()
    account_id = payload.get("account_id")
    account = get_account_row(account_id, session["user_id"]) if account_id else None
    if not account:
        return json_error("Account not found", 404, "account_not_found")
    username = decrypt_account_username(account)
    return jsonify(start_farming_for_username(username))


@accounts_bp.route("/stop_farming", methods=["POST"])
@login_required
@rate_limit("stop_session", limit=30, seconds=60)
def api_stop_farming():
    payload = _json_payload()
    account_id = payload.get("account_id")
    account = get_account_row(account_id, session["user_id"]) if account_id else None
    if not account:
        return json_error("Account not found", 404, "account_not_found")
    username = decrypt_account_username(account)
    return jsonify(stop_farming_for_username(username))
