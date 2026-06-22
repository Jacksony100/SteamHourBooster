"""FACEIT Finder — resolve a Steam profile to its public FACEIT CS2 stats.

Keyless by default: uses FACEIT's own public web endpoints (api.faceit.com — the
same ones the faceit.com site calls) plus Steam Community profile XML for vanity
resolution, so no API key is required. All data is public; there is no auth bypass
or private-data access. These endpoints are undocumented and may rate-limit or
change — set FACEIT_API_KEY to use the official, more reliable Data API instead.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

import httpx

from app.core.config import get_settings
from app.core.observability import get_logger

logger = get_logger("app.faceit")

FACEIT_MATCH_LIMIT = 10  # how many recent matches to parse in detail (official API)
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


def _result(steamid64: str, profile: dict, lifetime, *, maps=None, matches=None, detail_level: str = "basic") -> dict:
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
            "avg_kills": num("Average Kills"),
            "mvps": num("Average MVPs", "Total MVPs"),
            "current_win_streak": num("Current Win Streak"),
            "longest_win_streak": num("Longest Win Streak"),
            "recent_results": [str(r) for r in recent][-5:],
        },
        "maps": maps or [],
        "matches": matches or [],
        "message": None,
        "source": profile.get("source"),
        "detail_level": detail_level,
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

    # Coded keys (empirically): m1=matches, m2=wins, k5=avg K/D, k8=avg HS%,
    # m7=avg kills (NOT headshots), s0=recent results, s1/s7=streaks.
    out: dict = {}
    if g("m1") is not None:
        out["Matches"] = g("m1")
    if g("k5") is not None:
        out["Average K/D Ratio"] = g("k5")
    if g("k8") is not None:
        out["Average Headshots %"] = g("k8")
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


def _official_get(path: str, params: dict | None = None) -> dict | None:
    settings = get_settings()
    return _get_json(f"{FACEIT_OPEN_API}{path}", params=params, headers={"Authorization": f"Bearer {settings.faceit_api_key}"})


def _opt(value) -> str | None:
    return str(value) if value not in (None, "") else None


def _segments_to_maps(segments) -> list:
    maps = []
    for seg in segments or []:
        if not isinstance(seg, dict) or seg.get("type") != "Map":
            continue
        st = seg.get("stats") or {}
        maps.append(
            {
                "name": seg.get("label") or "?",
                "matches": _opt(st.get("Matches")),
                "win_rate": _opt(st.get("Win Rate %")),
                "kd_ratio": _opt(st.get("Average K/D Ratio")),
            }
        )

    def _count(m) -> int:
        try:
            return int(m["matches"])
        except (TypeError, ValueError):
            return 0

    maps.sort(key=_count, reverse=True)
    return maps[:8]


def _iso_date(ts) -> str | None:
    try:
        return datetime.fromtimestamp(int(ts), tz=UTC).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return None


def _official_matches(player_id: str) -> list:
    """Parse the last N matches in detail: per-match map, score, K/D, HS%, result."""
    hist = _official_get(f"/players/{player_id}/history", {"game": "cs2", "limit": FACEIT_MATCH_LIMIT})
    items = (hist or {}).get("items") or []
    out: list[dict] = []
    for item in items[:FACEIT_MATCH_LIMIT]:
        mid = item.get("match_id")
        match = {
            "match_id": mid,
            "date": _iso_date(item.get("started_at") or item.get("finished_at")),
            "faceit_url": (item.get("faceit_url") or "").replace("{lang}", "en") or None,
        }
        stats = _official_get(f"/matches/{mid}/stats") if mid else None
        rounds = (stats or {}).get("rounds") or []
        if rounds and isinstance(rounds[0], dict):
            rs = rounds[0].get("round_stats") or {}
            match["map"] = rs.get("Map")
            match["score"] = rs.get("Score")
            for team in rounds[0].get("teams") or []:
                for player in team.get("players") or []:
                    if player.get("player_id") == player_id:
                        ps = player.get("player_stats") or {}
                        match["kills"] = _opt(ps.get("Kills"))
                        match["deaths"] = _opt(ps.get("Deaths"))
                        match["kd_ratio"] = _opt(ps.get("K/D Ratio"))
                        match["headshots"] = _opt(ps.get("Headshots %"))
                        match["result"] = "win" if str(ps.get("Result")) == "1" else "loss"
        out.append(match)
    return out


def _find_via_official(steamid64: str) -> dict | None:
    player = _official_get("/players", {"game": "cs2", "game_player_id": steamid64})
    if not player:
        return None
    cs2 = (player.get("games") or {}).get("cs2") or {}
    player_id = player.get("player_id")
    profile = {
        "player_id": player_id,
        "nickname": player.get("nickname"),
        "avatar": player.get("avatar"),
        "country": player.get("country"),
        "faceit_url": (player.get("faceit_url") or "").replace("{lang}", "en") or None,
        "cs2": {"skill_level": cs2.get("skill_level"), "faceit_elo": cs2.get("faceit_elo"), "region": cs2.get("region")},
        "source": "faceit_api",
    }
    stats_raw = _official_get(f"/players/{player_id}/stats/cs2") if player_id else None
    lifetime = (stats_raw or {}).get("lifetime") or {}
    maps = _segments_to_maps((stats_raw or {}).get("segments"))
    matches = _official_matches(player_id) if player_id else []
    return _result(steamid64, profile, lifetime, maps=maps, matches=matches, detail_level="full")


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
