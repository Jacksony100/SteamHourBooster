"""FACEIT Finder — resolve a Steam profile to its public FACEIT CS2 stats.

Uses only official public APIs: Steam's ResolveVanityURL (for vanity links) and the
FACEIT Data API. Both keys stay server-side. No login required to use the lookup.
"""

from __future__ import annotations

import re

import httpx

from app.core.config import get_settings
from app.core.observability import get_logger

logger = get_logger("app.faceit")

FACEIT_API = "https://open.faceit.com/data/v4"
STEAM_API = "https://api.steampowered.com"

_PROFILES_RE = re.compile(r"steamcommunity\.com/profiles/(\d{17})")
_VANITY_RE = re.compile(r"steamcommunity\.com/id/([^/?#]+)")
_STEAMID64_RE = re.compile(r"^\d{17}$")


def parse_steam_input(value: str) -> tuple[str | None, str | None]:
    """Return (steamid64, vanity). Exactly one is set when parseable."""

    text = (value or "").strip()
    if not text:
        return None, None
    m = _PROFILES_RE.search(text)
    if m:
        return m.group(1), None
    m = _VANITY_RE.search(text)
    if m:
        return None, m.group(1)
    if _STEAMID64_RE.match(text):
        return text, None
    # Bare vanity name (no URL).
    if re.match(r"^[A-Za-z0-9_.-]{2,64}$", text):
        return None, text
    return None, None


def resolve_vanity(vanity: str) -> str | None:
    settings = get_settings()
    if not settings.steam_api_key:
        return None
    try:
        resp = httpx.get(
            f"{STEAM_API}/ISteamUser/ResolveVanityURL/v1/",
            params={"key": settings.steam_api_key, "vanityurl": vanity},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("response", {})
        return data.get("steamid") if data.get("success") == 1 else None
    except Exception as exc:
        logger.warning("Vanity resolve failed: %s", type(exc).__name__)
        return None


def _faceit_get(path: str, params: dict | None = None) -> dict | None:
    settings = get_settings()
    try:
        resp = httpx.get(
            f"{FACEIT_API}{path}",
            params=params or {},
            headers={"Authorization": f"Bearer {settings.faceit_api_key}"},
            timeout=10,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return None
        logger.warning("FACEIT API error: %s", exc.response.status_code)
        return None
    except Exception as exc:
        logger.warning("FACEIT API call failed: %s", type(exc).__name__)
        return None


def find_player(steam_input: str) -> dict:
    settings = get_settings()
    if not settings.faceit_api_key:
        return {"found": False, "configured": False, "message": "FACEIT lookup is not configured on this server."}

    steamid64, vanity = parse_steam_input(steam_input)
    if not steamid64 and vanity:
        steamid64 = resolve_vanity(vanity)
    if not steamid64:
        return {
            "found": False,
            "configured": True,
            "message": "Could not read a SteamID64 from that input. Paste a steamcommunity.com profile link or a 17-digit SteamID64.",
        }

    player = _faceit_get("/players", {"game": "cs2", "game_player_id": steamid64})
    if not player:
        return {"found": False, "configured": True, "steamid64": steamid64, "message": "No FACEIT profile found for this Steam account."}

    cs2 = (player.get("games") or {}).get("cs2") or {}
    player_id = player.get("player_id")
    stats_raw = _faceit_get(f"/players/{player_id}/stats/cs2") if player_id else None
    lifetime = (stats_raw or {}).get("lifetime") or {}

    def num(*keys: str):
        for key in keys:
            if key in lifetime:
                return lifetime[key]
        return None

    recent = lifetime.get("Recent Results") or []
    return {
        "found": True,
        "configured": True,
        "steamid64": steamid64,
        "player_id": player_id,
        "nickname": player.get("nickname"),
        "avatar": player.get("avatar") or None,
        "country": player.get("country"),
        "faceit_url": (player.get("faceit_url") or "").replace("{lang}", "en") or None,
        "skill_level": cs2.get("skill_level"),
        "faceit_elo": cs2.get("faceit_elo"),
        "region": cs2.get("region"),
        "stats": {
            "matches": num("Matches"),
            "win_rate": num("Win Rate %"),
            "kd_ratio": num("Average K/D Ratio", "K/D Ratio"),
            "headshots": num("Average Headshots %", "Total Headshots %"),
            "current_win_streak": num("Current Win Streak"),
            "longest_win_streak": num("Longest Win Streak"),
            "recent_results": [str(r) for r in recent][-5:],
        },
        "message": None,
    }
