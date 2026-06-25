"""Sign in with Steam — Steam OpenID 2.0 (no API key required).

Flow: build_login_url() redirects the browser to Steam; Steam redirects back to the
callback with openid.* params; verify_steam_response() re-checks them with Steam
(mode=check_authentication) to prevent forgery and returns the SteamID64.
"""

from __future__ import annotations

import re
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from app.core.observability import get_logger

logger = get_logger("app.auth.steam")

OPENID_ENDPOINT = "https://steamcommunity.com/openid/login"
_OPENID_NS = "http://specs.openid.net/auth/2.0"
_IDENTIFIER_SELECT = "http://specs.openid.net/auth/2.0/identifier_select"
_CLAIMED_ID_RE = re.compile(r"^https://steamcommunity\.com/openid/id/(\d{17})$")


def _web_base() -> str:
    return get_settings().web_base_url.rstrip("/")


def return_to_url() -> str:
    # Goes through the web origin (which proxies /api to the API), so the session
    # cookie set on the callback lands on the same origin as the SPA.
    return f"{_web_base()}/api/v1/auth/steam/callback"


def build_login_url() -> str:
    params = {
        "openid.ns": _OPENID_NS,
        "openid.mode": "checkid_setup",
        "openid.return_to": return_to_url(),
        "openid.realm": _web_base(),
        "openid.identity": _IDENTIFIER_SELECT,
        "openid.claimed_id": _IDENTIFIER_SELECT,
    }
    return f"{OPENID_ENDPOINT}?{urlencode(params)}"


def verify_steam_response(params: dict[str, str]) -> str | None:
    """Validate the callback params with Steam and return the SteamID64, or None."""
    if params.get("openid.mode") != "id_res":
        return None
    claimed = params.get("openid.claimed_id", "")
    if not _CLAIMED_ID_RE.match(claimed):
        return None

    # Echo every openid.* field back to Steam with mode=check_authentication.
    payload = {k: v for k, v in params.items() if k.startswith("openid.")}
    payload["openid.mode"] = "check_authentication"
    try:
        resp = httpx.post(OPENID_ENDPOINT, data=payload, timeout=10)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Steam OpenID verification failed: %s", type(exc).__name__)
        return None

    if not re.search(r"is_valid\s*:\s*true", resp.text):
        return None
    return _CLAIMED_ID_RE.match(claimed).group(1)


def fetch_persona(steamid64: str) -> str | None:
    """Best-effort Steam persona name for a friendlier username (needs STEAM_API_KEY)."""
    settings = get_settings()
    if not settings.steam_api_key:
        return None
    try:
        resp = httpx.get(
            "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/",
            params={"key": settings.steam_api_key, "steamids": steamid64},
            timeout=10,
        )
        resp.raise_for_status()
        players = (resp.json().get("response") or {}).get("players") or []
        return players[0].get("personaname") if players else None
    except Exception:  # noqa: BLE001
        return None
