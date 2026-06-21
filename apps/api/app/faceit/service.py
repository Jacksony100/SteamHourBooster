"""FACEIT Finder — resolve a Steam profile to its public FACEIT CS2 stats.

Keyless by default: uses FACEIT's own public web endpoints (api.faceit.com — the
same ones the faceit.com site calls) plus Steam Community profile XML for vanity
resolution, so no API key is required. All data is public; there is no auth bypass
or private-data access. These endpoints are undocumented and may rate-limit or
change — set FACEIT_API_KEY to use the official, more reliable Data API instead.
"""

from __future__ import annotations

import re

import httpx

from app.core.config import get_settings
from app.core.observability import get_logger

logger = get_logger("app.faceit")

FACEIT_OPEN_API = "https://open.faceit.com/data/v4"   # official, key required
FACEIT_WEB_API = "https://api.faceit.com"             # public web endpoints, keyless
STEAM_API = "https://api.steampowered.com"
STEAM_COMMUNITY = "https://steamcommunity.com"

# Mimic the faceit.com frontend's own XHR calls to reduce Cloudflare friction on the
# keyless endpoints. (Stats are sometimes still bot-challenged; set FACEIT_API_KEY for
# reliable full stats.)
_KEYLESS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.faceit.com/",
    "Origin": "https://www.faceit.com",
}

_PROFILES_RE = re.compile(r"steamcommunity\.com/profiles/(\d{17})")
_VANITY_RE = re.compile(r"steamcommunity\.com/id/([^/?#]+)")
_STEAMID64_RE = re.compile(r"^\d{17}$")
_XML_STEAMID_RE = re.compile(r"<steamID64>(\d{17})</steamID64>")


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
    if re.match(r"^[A-Za-z0-9_.-]{2,64}$", text):
        return None, text
    return None, None


def _get_json(url: str, *, params: dict | None = None, headers: dict | None = None) -> dict | None:
    try:
        resp = httpx.get(url, params=params or {}, headers=headers or _KEYLESS_HEADERS, timeout=10, follow_redirects=True)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("FACEIT/Steam fetch failed (%s): %s", url.split("?")[0], type(exc).__name__)
        return None


def _resolve_vanity_xml(vanity: str) -> str | None:
    """Resolve a Steam vanity name to a SteamID64 via the public profile XML (no key)."""

    try:
        resp = httpx.get(f"{STEAM_COMMUNITY}/id/{vanity}/", params={"xml": 1}, headers=_KEYLESS_HEADERS, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        m = _XML_STEAMID_RE.search(resp.text)
        return m.group(1) if m else None
    except Exception as exc:
        logger.warning("Vanity XML resolve failed: %s", type(exc).__name__)
        return None


def _resolve_vanity_api(vanity: str) -> str | None:
    settings = get_settings()
    if not settings.steam_api_key:
        return None
    data = _get_json(f"{STEAM_API}/ISteamUser/ResolveVanityURL/v1/", params={"key": settings.steam_api_key, "vanityurl": vanity})
    response = (data or {}).get("response", {})
    return response.get("steamid") if response.get("success") == 1 else None


def resolve_steamid64(steam_input: str) -> str | None:
    steamid64, vanity = parse_steam_input(steam_input)
    if steamid64:
        return steamid64
    if vanity:
        return _resolve_vanity_xml(vanity) or _resolve_vanity_api(vanity)
    return None


def _payload(data) -> dict:
    """Extract a dict payload from a keyless FACEIT response (handles dict/list/None)."""
    if isinstance(data, dict):
        inner = data.get("payload", data)
        if isinstance(inner, list):
            return inner[0] if inner and isinstance(inner[0], dict) else {}
        return inner if isinstance(inner, dict) else {}
    if isinstance(data, list):
        return data[0] if data and isinstance(data[0], dict) else {}
    return {}


def _result(steamid64: str, profile: dict, lifetime) -> dict:
    if not isinstance(lifetime, dict):
        lifetime = {}
    cs2 = profile.get("cs2") or {}

    def num(*keys: str):
        for key in keys:
            if key in lifetime and lifetime[key] not in (None, ""):
                return str(lifetime[key])
        return None

    recent = lifetime.get("Recent Results") or lifetime.get("recentResults") or []
    return {
        "found": True,
        "configured": True,
        "steamid64": steamid64,
        "player_id": profile.get("player_id"),
        "nickname": profile.get("nickname"),
        "avatar": profile.get("avatar") or None,
        "country": profile.get("country"),
        "faceit_url": profile.get("faceit_url"),
        "skill_level": cs2.get("skill_level"),
        "faceit_elo": cs2.get("faceit_elo"),
        "region": cs2.get("region"),
        "stats": {
            "matches": num("Matches", "m1", "Total Matches"),
            "win_rate": num("Win Rate %", "Win Rate"),
            "kd_ratio": num("Average K/D Ratio", "K/D Ratio"),
            "headshots": num("Average Headshots %", "Total Headshots %"),
            "current_win_streak": num("Current Win Streak"),
            "longest_win_streak": num("Longest Win Streak"),
            "recent_results": [str(r) for r in recent][-5:],
        },
        "message": None,
        "source": profile.get("source"),
    }


def _find_via_keyless(steamid64: str) -> dict | None:
    # 1. SteamID64 -> FACEIT player GUID (try cs2 then csgo).
    payload = _payload(_get_json(f"{FACEIT_WEB_API}/users/v1/users", params={"game": "cs2", "game_id": steamid64}))
    if not payload:
        payload = _payload(_get_json(f"{FACEIT_WEB_API}/users/v1/users", params={"game": "csgo", "game_id": steamid64}))
    guid = payload.get("id") or payload.get("guid")
    if not guid:
        return None

    # 2. Full profile by GUID.
    p = _payload(_get_json(f"{FACEIT_WEB_API}/users/v1/users/{guid}")) or payload
    games = p.get("games") or {}
    cs2 = games.get("cs2") or games.get("csgo") or {}
    nickname = p.get("nickname")
    profile = {
        "player_id": guid,
        "nickname": nickname,
        "avatar": p.get("avatar"),
        "country": p.get("country"),
        "faceit_url": f"https://www.faceit.com/en/players/{nickname}" if nickname else None,
        "cs2": {
            "skill_level": cs2.get("skill_level"),
            "faceit_elo": cs2.get("faceit_elo"),
            "region": cs2.get("region"),
        },
        "source": "faceit_web",
    }

    # 3. Lifetime stats. The keyless endpoint returns FACEIT's internal coded keys
    # (m1, k5, s0, ...) rather than human names; translate the reliable ones.
    stats_raw = _get_json(f"{FACEIT_WEB_API}/stats/v1/stats/users/{guid}/games/cs2")
    raw_life = stats_raw.get("lifetime") if isinstance(stats_raw, dict) else {}
    lifetime = _decode_keyless_lifetime(raw_life if isinstance(raw_life, dict) else {})
    return _result(steamid64, profile, lifetime)


def _decode_keyless_lifetime(life: dict) -> dict:
    """Map FACEIT's coded keyless lifetime keys to the human keys _result expects.

    Best-effort: the level/ELO headline comes from the profile and is reliable; this
    decoding of the undocumented coded stats may need tuning if FACEIT changes them.
    """

    def g(key: str):
        value = life.get(key)
        return None if value in (None, "") else value

    out: dict = {}
    if g("m1") is not None:
        out["Matches"] = g("m1")
    if g("k5") is not None:
        out["Average K/D Ratio"] = g("k5")
    if g("m7") is not None:
        out["Average Headshots %"] = g("m7")
    if g("s1") is not None:
        out["Current Win Streak"] = g("s1")
    if g("s7") is not None:
        out["Longest Win Streak"] = g("s7")
    if isinstance(life.get("s0"), list):
        out["Recent Results"] = life["s0"]
    try:
        matches, wins = int(life.get("m1")), int(life.get("m2"))
        if matches > 0:
            out["Win Rate %"] = str(round(wins / matches * 100))
    except (TypeError, ValueError):
        pass
    return out


def _find_via_official(steamid64: str) -> dict | None:
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.faceit_api_key}"}
    player = _get_json(f"{FACEIT_OPEN_API}/players", params={"game": "cs2", "game_player_id": steamid64}, headers=headers)
    if not player:
        return None
    cs2 = (player.get("games") or {}).get("cs2") or {}
    player_id = player.get("player_id")
    stats_raw = _get_json(f"{FACEIT_OPEN_API}/players/{player_id}/stats/cs2", headers=headers) if player_id else None
    lifetime = (stats_raw or {}).get("lifetime") or {}
    profile = {
        "player_id": player_id,
        "nickname": player.get("nickname"),
        "avatar": player.get("avatar"),
        "country": player.get("country"),
        "faceit_url": (player.get("faceit_url") or "").replace("{lang}", "en") or None,
        "cs2": {"skill_level": cs2.get("skill_level"), "faceit_elo": cs2.get("faceit_elo"), "region": cs2.get("region")},
        "source": "faceit_api",
    }
    return _result(steamid64, profile, lifetime)


def find_player(steam_input: str) -> dict:
    steamid64 = resolve_steamid64(steam_input)
    if not steamid64:
        return {
            "found": False,
            "configured": True,
            "message": "Could not read a SteamID64 from that input. Paste a steamcommunity.com profile link or a 17-digit SteamID64.",
        }

    settings = get_settings()
    data = _find_via_official(steamid64) if settings.faceit_api_key else None
    if data is None:
        data = _find_via_keyless(steamid64)
    if not data:
        return {"found": False, "configured": True, "steamid64": steamid64, "message": "No FACEIT profile found for this Steam account."}
    return data
