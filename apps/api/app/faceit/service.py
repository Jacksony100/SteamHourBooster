"""FACEIT Finder — resolve a Steam profile to its public FACEIT CS2 stats.

Keyless by default: uses FACEIT's own public web endpoints (api.faceit.com — the
same ones the faceit.com site calls) plus Steam Community profile XML for vanity
resolution, so no API key is required. All data is public; there is no auth bypass
or private-data access. These endpoints are undocumented and may rate-limit or
change — set FACEIT_API_KEY to use the official, more reliable Data API instead.
"""

from __future__ import annotations

import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import httpx

from app.core.config import get_settings
from app.core.observability import get_logger

logger = get_logger("app.faceit")

# How many recent matches to parse in detail is configurable via FACEIT_MATCH_LIMIT.
FACEIT_MATCH_WORKERS = 8  # parallel per-match stat fetches
FACEIT_OPEN_API = "https://open.faceit.com/data/v4"   # official, key required

# Short-lived result cache (a lookup hits the FACEIT API ~20+ times, so cache it).
# TTL is configurable via FACEIT_CACHE_TTL_SECONDS (see core.config). A process-local
# dict is the fast path; Redis (when reachable) shares it across workers and adds
# stale-while-revalidate so a popular lookup never blocks on FACEIT.
_CACHE_MAX = 256
_STALE_FACTOR = 4  # serve stale up to TTL*factor while refreshing in the background
_cache: dict[str, tuple[float, dict]] = {}
_cache_lock = threading.Lock()
_refreshing: set[str] = set()
_refresh_lock = threading.Lock()


def reset_faceit_cache() -> None:
    with _cache_lock:
        _cache.clear()
    with _refresh_lock:
        _refreshing.clear()


def _cache_put(key: str, result: dict) -> None:
    """Thread-safe write + LRU eviction (background refresh threads also write here)."""
    with _cache_lock:
        if key not in _cache and len(_cache) >= _CACHE_MAX:
            try:
                _cache.pop(next(iter(_cache)))
            except StopIteration:
                pass
        _cache[key] = (time.monotonic(), result)
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


def _result(steamid64: str, profile: dict, lifetime, *, maps=None, matches=None, elo_history=None, elo_history_approx=False, teammates=None, recent_form=None, streak=None, smurf=None, steam=None, advanced=None, radar=None, activity=None, best_match=None, worst_match=None, consistency=None, percentile=None, detail_level: str = "basic") -> dict:
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
        "elo_history": elo_history or [],
        "elo_history_approx": elo_history_approx,
        "teammates": teammates or [],
        "recent_form": recent_form,
        "streak": streak,
        "smurf": smurf,
        "steam": steam,
        "advanced": advanced,
        "radar": radar,
        "activity": activity,
        "best_match": best_match,
        "worst_match": worst_match,
        "consistency": consistency,
        "percentile": percentile,
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
    return _result(steamid64, profile, lifetime, elo_history=_elo_history(guid))


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


def _elo_history(guid: str | None, size: int | None = None) -> list:
    """Per-match ELO points (oldest→newest) from FACEIT's public time-stats endpoint.

    ELO is public, so this keyless endpoint is used in both keyless and official modes.
    It can be Cloudflare-challenged server-side; on any failure we return [] and the
    UI simply hides the chart — no hard dependency on it.
    """
    if not guid:
        return []
    n = get_settings().faceit_elo_history_size if size is None else size
    if n <= 0:
        return []
    data = _get_json(f"{FACEIT_WEB_API}/stats/v1/stats/time/users/{guid}/games/cs2", params={"size": n})
    items = data.get("payload", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []

    points = []
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            elo = int(float(item.get("elo")))
        except (TypeError, ValueError):
            continue
        if elo < 0:  # FACEIT ELO is always positive; drop clearly-corrupt points
            continue
        ts = item.get("created_at") or item.get("date")
        try:
            ts = int(ts)
            seconds = ts // 1000 if ts > 1_000_000_000_000 else ts
        except (TypeError, ValueError):
            seconds = None
        points.append({"date": _iso_date(seconds) if seconds else None, "elo": elo})

    # The endpoint returns newest-first; present oldest→newest for a left-to-right chart.
    points.reverse()
    return points[-n:]


# FACEIT awards ~+25 / -25 ELO per matchmaking result for evenly-matched games.
_ELO_STEP = 25
_ELO_FLOOR = 100  # FACEIT's minimum ELO


def _reconstruct_elo_history(current_elo, matches: list) -> list:
    """Approximate ELO trend from current ELO + recent win/loss, when the exact
    per-match ELO endpoint is unavailable (it's keyless-only and often Cloudflare-
    blocked, while the official Data API exposes no per-match ELO at all).

    The latest point is exact (current ELO); earlier points are estimated by undoing
    a flat ±25 per result walking backwards. Shape and endpoint are right; intermediate
    absolute values are approximate — callers should label it as such.
    """
    try:
        elo = int(current_elo)
    except (TypeError, ValueError):
        return []
    if not matches:
        return []

    chrono = list(reversed(matches))  # `matches` is newest-first; walk oldest→newest
    afters = [0] * len(chrono)
    for j in range(len(chrono) - 1, -1, -1):
        afters[j] = elo  # ELO after this match
        result = chrono[j].get("result")
        if result == "win":
            elo = max(_ELO_FLOOR, elo - _ELO_STEP)  # before a win it was lower
        elif result == "loss":
            elo = elo + _ELO_STEP  # before a loss it was higher
        # unknown result -> assume no change (flat step)
    return [{"date": chrono[j].get("date"), "elo": afters[j]} for j in range(len(chrono))]


def _sum_int(*values) -> str | None:
    total = 0
    seen = False
    for v in values:
        try:
            total += int(v)
            seen = True
        except (TypeError, ValueError):
            continue
    return str(total) if seen else None


def _parse_one_match(player_id: str, item: dict) -> tuple[dict, list, dict]:
    """Parse one match for `player_id`. Returns (display_match, teammates, raw_player_stats).
    raw_player_stats is kept out of the response and used only for advanced aggregates."""
    mid = item.get("match_id")
    match = {
        "match_id": mid,
        "date": _iso_date(item.get("started_at") or item.get("finished_at")),
        "faceit_url": (item.get("faceit_url") or "").replace("{lang}", "en") or None,
    }
    teammates: list = []
    raw: dict = {}
    stats = _official_get(f"/matches/{mid}/stats") if mid else None
    rounds = (stats or {}).get("rounds") or []
    if rounds and isinstance(rounds[0], dict):
        rs = rounds[0].get("round_stats") or {}
        match["map"] = rs.get("Map")
        match["score"] = rs.get("Score")
        teams = rounds[0].get("teams") or []
        my_team = None
        for ti, team in enumerate(teams):
            for player in team.get("players") or []:
                if player.get("player_id") == player_id:
                    my_team = ti
                    ps = player.get("player_stats") or {}
                    raw = ps
                    match["kills"] = _opt(ps.get("Kills"))
                    match["deaths"] = _opt(ps.get("Deaths"))
                    match["assists"] = _opt(ps.get("Assists"))
                    match["kd_ratio"] = _opt(ps.get("K/D Ratio"))
                    match["kr_ratio"] = _opt(ps.get("K/R Ratio"))
                    match["adr"] = _opt(ps.get("ADR") or ps.get("Average Damage per Round"))
                    match["headshots"] = _opt(ps.get("Headshots %"))
                    match["mvps"] = _opt(ps.get("MVPs"))
                    match["triple_kills"] = _opt(ps.get("Triple Kills"))
                    match["quadro_kills"] = _opt(ps.get("Quadro Kills"))
                    match["penta_kills"] = _opt(ps.get("Penta Kills"))
                    match["clutches"] = _sum_int(ps.get("1v1Wins"), ps.get("1v2Wins"))
                    match["result"] = "win" if str(ps.get("Result")) == "1" else "loss"
        if my_team is not None:
            for player in teams[my_team].get("players") or []:
                pid = player.get("player_id")
                if pid and pid != player_id:
                    teammates.append({"player_id": pid, "nickname": player.get("nickname")})
    return match, teammates, raw


def match_scoreboard(match_id: str) -> dict | None:
    """Full both-teams scoreboard for one match (lazy drill-down). Public official API."""
    stats = _official_get(f"/matches/{match_id}/stats")
    rounds = (stats or {}).get("rounds") or []
    if not (rounds and isinstance(rounds[0], dict)):
        return None
    rs = rounds[0].get("round_stats") or {}
    teams = []
    for team in rounds[0].get("teams") or []:
        ts = team.get("team_stats") or {}
        players = []
        for p in team.get("players") or []:
            ps = p.get("player_stats") or {}
            players.append({
                "player_id": p.get("player_id"),
                "nickname": p.get("nickname"),
                "kills": _opt(ps.get("Kills")),
                "deaths": _opt(ps.get("Deaths")),
                "assists": _opt(ps.get("Assists")),
                "kd_ratio": _opt(ps.get("K/D Ratio")),
                "adr": _opt(ps.get("ADR") or ps.get("Average Damage per Round")),
                "headshots": _opt(ps.get("Headshots %")),
                "mvps": _opt(ps.get("MVPs")),
            })
        players.sort(key=lambda x: int(x["kills"]) if (x["kills"] or "").isdigit() else 0, reverse=True)
        teams.append({
            "name": team.get("team_id") or ts.get("Team") or "?",
            "win": str(ts.get("Team Win")) == "1",
            "score": _opt(ts.get("Final Score")),
            "players": players,
        })
    return {"match_id": match_id, "map": rs.get("Map"), "score": rs.get("Score"), "teams": teams}


def _fnum(d: dict, *keys: str) -> float:
    for key in keys:
        v = (d or {}).get(key)
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return 0.0


def _advanced_stats(raws: list) -> dict | None:
    """Deep aggregates from recent matches: entry duels, clutches, utility, AWP, multikills."""
    played = [r for r in raws if r]
    n = len(played)
    if not n:
        return None

    def s(*keys: str) -> float:
        return sum(_fnum(r, *keys) for r in played)

    entry_c, entry_w = s("Entry Count"), s("Entry Wins")
    c1, c1w = s("1v1Count"), s("1v1Wins")
    c2, c2w = s("1v2Count"), s("1v2Wins")
    return {
        "entry_per_match": round(entry_c / n, 1),
        "entry_success": round(entry_w / entry_c * 100) if entry_c else None,
        "clutch_1v1": round(c1w / c1 * 100) if c1 else None,
        "clutch_1v2": round(c2w / c2 * 100) if c2 else None,
        "flashes_per_match": round(s("Enemies Flashed", "Flash Count") / n, 1),
        "utility_dmg_per_match": round(s("Utility Damage") / n),
        "sniper_per_match": round(s("Sniper Kills") / n, 1),
        "pistol_total": int(s("Pistol Kills")),
        "aces": int(s("Penta Kills")),
        "quad_kills": int(s("Quadro Kills")),
        "triple_kills": int(s("Triple Kills")),
        "avg_kills": round(s("Kills") / n, 1),
        "avg_deaths": round(s("Deaths") / n, 1),
        "avg_assists": round(s("Assists") / n, 1),
    }


def _consistency(matches: list) -> int | None:
    """0–100 consistency = how steady recent K/D is (low variance -> high score)."""
    vals = [float(m["kd_ratio"]) for m in matches if (m.get("kd_ratio") or "").replace(".", "", 1).isdigit()]
    if len(vals) < 3:
        return None
    mean = sum(vals) / len(vals)
    if mean <= 0:
        return None
    var = sum((v - mean) ** 2 for v in vals) / len(vals)
    cv = (var ** 0.5) / mean  # coefficient of variation
    return round(max(0.0, min(100.0, 100 * (1 - cv))))


def _best_worst(matches: list) -> tuple[dict | None, dict | None]:
    rated = [m for m in matches if (m.get("kills") or "").isdigit()]
    if len(rated) < 2:
        return None, None
    best = max(rated, key=lambda m: int(m["kills"]))
    worst = min(rated, key=lambda m: int(m["kills"]))
    return best, worst


def _activity(matches: list) -> list[int] | None:
    """Recent matches counted per weekday (Mon..Sun)."""
    counts = [0] * 7
    seen = False
    for m in matches:
        d = m.get("date")
        if not d:
            continue
        try:
            counts[datetime.strptime(d, "%Y-%m-%d").weekday()] += 1
            seen = True
        except ValueError:
            continue
    return counts if seen else None


def _percentile(elo) -> int | None:
    """Approximate global ELO percentile rank via a logistic CDF (centred ~1050).
    Rough estimate for context, not an official ranking."""
    try:
        e = float(elo)
    except (TypeError, ValueError):
        return None
    import math

    pct = 100.0 / (1.0 + math.exp(-(e - 1050.0) / 450.0))
    return round(max(1.0, min(99.0, pct)))


def _radar(recent_form: dict | None, advanced: dict | None) -> dict | None:
    """6 skill axes normalised to 0–100 for a radar chart."""
    if not recent_form and not advanced:
        return None
    rf, adv = recent_form or {}, advanced or {}

    def cap(v, hi):
        return None if v is None else round(max(0.0, min(100.0, v / hi * 100)))

    clutch_vals = [v for v in (adv.get("clutch_1v1"), adv.get("clutch_1v2")) if v is not None]
    clutch = sum(clutch_vals) / len(clutch_vals) if clutch_vals else None
    return {
        "Aim": cap(rf.get("kd_ratio"), 2.0),
        "Damage": cap(rf.get("adr"), 110.0),
        "HS%": rf.get("headshots"),
        "Entry": adv.get("entry_success"),
        "Clutch": round(clutch) if clutch is not None else None,
        "Utility": cap(adv.get("utility_dmg_per_match"), 50.0),
    }


def _aggregate_teammates(parsed: list) -> list:
    """Most-frequent same-team teammates across recent matches, with win rate."""
    agg: dict = {}
    for match, mates, _raw in parsed:
        win = match.get("result") == "win"
        for mate in mates:
            pid = mate.get("player_id")
            if not pid:
                continue
            rec = agg.setdefault(pid, {"player_id": pid, "nickname": mate.get("nickname"), "games": 0, "wins": 0})
            rec["games"] += 1
            rec["wins"] += 1 if win else 0
            if mate.get("nickname"):
                rec["nickname"] = mate["nickname"]
    out = [r for r in agg.values() if r["games"] >= 2]
    out.sort(key=lambda r: (r["games"], r["wins"]), reverse=True)
    for r in out:
        r["win_rate"] = str(round(r["wins"] / r["games"] * 100)) if r["games"] else None
    return out[:6]


def _avg(played: list, key: str) -> float | None:
    vals = []
    for m in played:
        try:
            vals.append(float(m.get(key)))
        except (TypeError, ValueError):
            continue
    return round(sum(vals) / len(vals), 2) if vals else None


def _recent_form(matches: list, lifetime: dict) -> dict | None:
    played = [m for m in matches if m.get("result") in ("win", "loss")]
    n = len(played)
    if not n:
        return None
    wins = sum(1 for m in played if m["result"] == "win")
    kd = _avg(played, "kd_ratio")
    adr = _avg(played, "adr")
    hs = _avg(played, "headshots")
    form = {
        "matches": n,
        "wins": wins,
        "win_rate": round(wins / n * 100),
        "kd_ratio": kd,
        "adr": adr,
        "headshots": round(hs) if hs is not None else None,
    }
    try:
        life_kd = float(lifetime.get("Average K/D Ratio"))
        form["kd_delta"] = round(kd - life_kd, 2) if kd is not None else None
    except (TypeError, ValueError):
        form["kd_delta"] = None
    return form


def _streak(matches: list) -> dict | None:
    played = [m for m in matches if m.get("result") in ("win", "loss")]
    if not played:
        return None
    head = played[0]["result"]  # newest match first
    length = 0
    for m in played:
        if m["result"] == head:
            length += 1
        else:
            break
    return {"type": head, "length": length, "tilt": head == "loss" and length >= 3}


def _smurf_heuristic(level, lifetime: dict, recent_form: dict | None) -> dict | None:
    """Heuristic smurf/alt signal — NOT proof. Surfaces unusual skill-for-level patterns."""
    score = 0
    flags: list = []
    try:
        total_matches = int(lifetime.get("Matches"))
    except (TypeError, ValueError):
        total_matches = 0
    try:
        life_kd = float(lifetime.get("Average K/D Ratio"))
    except (TypeError, ValueError):
        life_kd = 0.0
    lvl = level or 0
    form_kd = (recent_form or {}).get("kd_ratio")
    form_hs = (recent_form or {}).get("headshots")
    form_wr = (recent_form or {}).get("win_rate")

    if lvl <= 6 and life_kd >= 1.3:
        score += 40
        flags.append("High K/D for the skill level")
    if form_hs and form_hs >= 55:
        score += 20
        flags.append("Unusually high headshot %")
    if total_matches and total_matches < 150 and form_wr and form_wr >= 70:
        score += 30
        flags.append("High win rate over few matches")
    if form_kd and form_kd >= 1.6:
        score += 20
        flags.append("Dominant recent K/D")

    score = min(100, score)
    return {"score": score, "flags": flags} if score >= 40 else None


def _official_matches(player_id: str) -> tuple[list, list, list]:
    """Parse the last N matches in detail (parallel) + frequent teammates + raw stats."""
    limit = get_settings().faceit_match_limit
    if limit <= 0:
        return [], [], []
    hist = _official_get(f"/players/{player_id}/history", {"game": "cs2", "limit": limit})
    items = ((hist or {}).get("items") or [])[:limit]
    if not items:
        return [], [], []
    with ThreadPoolExecutor(max_workers=FACEIT_MATCH_WORKERS) as pool:
        parsed = list(pool.map(lambda it: _parse_one_match(player_id, it), items))
    matches = [m for m, _, _ in parsed]
    raws = [r for _, _, r in parsed]
    return matches, _aggregate_teammates(parsed), raws


def _resolve_elo_history(player_id, current_elo, matches: list) -> tuple[list, bool]:
    """(points, approx). Exact keyless series when reachable; else reconstructed from W/L.
    Real DB snapshots, if any, are overlaid later in the route layer."""
    exact = _elo_history(player_id)
    if exact:
        return exact, False
    recon = _reconstruct_elo_history(current_elo, matches)
    return recon, bool(recon)


def _steam_enrichment(steamid64) -> dict | None:
    """Cross-source Steam profile data (CS2 hours, Steam level, account age, VAC).

    Requires STEAM_API_KEY; returns None without it (the UI then hides the panel).
    All data is public via the Steam Web API.
    """
    settings = get_settings()
    sid = str(steamid64) if steamid64 else ""
    if not settings.steam_api_key or not _STEAMID64_RE.match(sid):
        return None
    key = settings.steam_api_key
    out: dict = {"steamid64": sid, "profile_url": f"{STEAM_COMMUNITY}/profiles/{sid}"}

    summary = _get_json(f"{STEAM_API}/ISteamUser/GetPlayerSummaries/v2/", params={"key": key, "steamids": sid}, headers={})
    players = ((summary or {}).get("response") or {}).get("players") or []
    if players:
        p = players[0]
        out["persona_name"] = p.get("personaname")
        out["avatar"] = p.get("avatarfull")
        out["profile_url"] = p.get("profileurl") or out["profile_url"]
        out["country"] = p.get("loccountrycode")
        out["visibility"] = "public" if int(p.get("communityvisibilitystate", 1)) == 3 else "private"
        if p.get("timecreated"):
            out["account_created"] = _iso_date(p.get("timecreated"))

    level = _get_json(f"{STEAM_API}/IPlayerService/GetSteamLevel/v1/", params={"key": key, "steamid": sid}, headers={})
    out["steam_level"] = ((level or {}).get("response") or {}).get("player_level")

    games = _get_json(
        f"{STEAM_API}/IPlayerService/GetOwnedGames/v1/",
        params={"key": key, "steamid": sid, "include_played_free_games": 1, "format": "json"},
        headers={},
    )
    glist = ((games or {}).get("response") or {}).get("games") or []
    cs2 = next((g for g in glist if g.get("appid") == 730), None)
    if cs2:
        out["cs2_hours"] = round((cs2.get("playtime_forever") or 0) / 60)

    bans = _get_json(f"{STEAM_API}/ISteamUser/GetPlayerBans/v1/", params={"key": key, "steamids": sid}, headers={})
    blist = (bans or {}).get("players") or []
    if blist:
        out["vac_banned"] = bool(blist[0].get("VACBanned"))
        out["vac_ban_count"] = int(blist[0].get("NumberOfVACBans") or 0)
    return out


def _official_result(player: dict, steamid64: str | None) -> dict:
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
    matches, teammates, raws = _official_matches(player_id) if player_id else ([], [], [])
    recent_form = _recent_form(matches, lifetime)
    streak = _streak(matches)
    smurf = _smurf_heuristic(cs2.get("skill_level"), lifetime, recent_form)
    advanced = _advanced_stats(raws)
    best_match, worst_match = _best_worst(matches)
    extras = {
        "advanced": advanced,
        "radar": _radar(recent_form, advanced),
        "activity": _activity(matches),
        "best_match": best_match,
        "worst_match": worst_match,
        "consistency": _consistency(matches),
        "percentile": _percentile(cs2.get("faceit_elo")),
    }

    sid = steamid64 or cs2.get("game_player_id")
    # ELO history: prefer real snapshots accumulated in our DB, then the exact keyless
    # endpoint, then an approximation from win/loss so the chart always renders.
    elo_history, elo_history_approx = _resolve_elo_history(player_id, cs2.get("faceit_elo"), matches)
    steam = _steam_enrichment(sid)

    return _result(
        sid, profile, lifetime,
        maps=maps, matches=matches, elo_history=elo_history,
        elo_history_approx=elo_history_approx, teammates=teammates,
        recent_form=recent_form, streak=streak, smurf=smurf, steam=steam,
        detail_level="full", **extras,
    )


def _find_via_official(steamid64: str) -> dict | None:
    player = _official_get("/players", {"game": "cs2", "game_player_id": steamid64})
    return _official_result(player, steamid64) if player else None


def _official_by_nickname(nickname: str) -> dict | None:
    player = _official_get("/players", {"nickname": nickname})
    return _official_result(player, None) if player and player.get("player_id") else None


def _keyless_by_nickname(nickname: str) -> dict | None:
    found = _payload(_get_json(f"{FACEIT_WEB_API}/users/v1/nicknames/{nickname}"))
    guid = found.get("id") or found.get("guid")
    sid = (found.get("games") or {}).get("cs2", {}).get("game_player_id") or (found.get("games") or {}).get("csgo", {}).get("game_player_id")
    if sid:
        return _find_via_keyless(sid)
    if not guid:
        return None
    games = found.get("games") or {}
    cs2 = games.get("cs2") or games.get("csgo") or {}
    profile = {
        "player_id": guid,
        "nickname": found.get("nickname") or nickname,
        "avatar": found.get("avatar"),
        "country": found.get("country"),
        "faceit_url": f"https://www.faceit.com/en/players/{found.get('nickname') or nickname}",
        "cs2": {"skill_level": cs2.get("skill_level"), "faceit_elo": cs2.get("faceit_elo"), "region": cs2.get("region")},
        "source": "faceit_web",
    }
    return _result(None, profile, {})


def _by_steamid(steamid64: str) -> dict:
    settings = get_settings()
    data = _find_via_official(steamid64) if settings.faceit_api_key else None
    if data is None:
        data = _find_via_keyless(steamid64)
    if not data:
        return {"found": False, "configured": True, "steamid64": steamid64, "message": "No FACEIT profile found for this Steam account."}
    return data


def _by_nickname(nickname: str) -> dict | None:
    return _official_by_nickname(nickname) if get_settings().faceit_api_key else _keyless_by_nickname(nickname)


def _find_player_uncached(query: str) -> dict:
    text = (query or "").strip()
    sid, vanity = parse_steam_input(text)
    is_steam_url = "steamcommunity.com" in text.lower()

    # A Steam profile URL or a raw SteamID64 -> resolve via Steam, then FACEIT by steamid.
    if sid or is_steam_url:
        steamid64 = sid or (resolve_steamid64(text) if vanity else None)
        if not steamid64:
            return {"found": False, "configured": True, "message": "Could not read a SteamID64 from that Steam link."}
        return _by_steamid(steamid64)

    # A bare token -> try it as a FACEIT nickname first, then as a Steam vanity.
    # `vanity` is only set when parse_steam_input validated the charset, so junk
    # input (e.g. "@@@") yields name=None and never makes a network call.
    name = vanity
    if name:
        data = _by_nickname(name)
        if data:
            return data
        steamid64 = _resolve_vanity_xml(name) or _resolve_vanity_api(name)
        if steamid64:
            return _by_steamid(steamid64)
    return {
        "found": False,
        "configured": True,
        "message": "No FACEIT player or Steam profile found. Try a FACEIT nickname, a steamcommunity.com link, or a SteamID64.",
    }


# Circuit breaker: when Redis is unreachable, stop hammering it (each call would
# otherwise pay the socket timeout) and just use the in-memory cache for a while.
_redis_down_until = 0.0
_REDIS_COOLDOWN = 30.0


def _redis():
    if time.time() < _redis_down_until:
        return None
    try:
        from app.core.rate_limit import redis_client

        return redis_client()
    except Exception:
        return None


def _redis_fail() -> None:
    global _redis_down_until
    _redis_down_until = time.time() + _REDIS_COOLDOWN


def _redis_get(key: str, ttl: int) -> tuple[dict | None, bool]:
    """(result, is_stale). Stale results (older than ttl but within ttl*factor) are
    returned for instant response while a background refresh runs."""
    client = _redis()
    if client is None:
        return None, False
    try:
        raw = client.get(f"faceit:find:{key}")
    except Exception:
        _redis_fail()
        return None, False
    if not raw:
        return None, False
    try:
        payload = json.loads(raw)
        data, ts = payload.get("data"), payload.get("_ts", 0)
    except (ValueError, TypeError):
        return None, False
    if not isinstance(data, dict):
        return None, False
    age = time.time() - ts
    if age < ttl:
        return data, False
    if age < ttl * _STALE_FACTOR:
        return data, True
    return None, False


def _store(key: str, result: dict, ttl: int) -> None:
    _cache_put(key, result)
    client = _redis()
    if client is not None:
        try:
            client.set(f"faceit:find:{key}", json.dumps({"_ts": time.time(), "data": result}), ex=int(ttl * _STALE_FACTOR))
        except Exception:
            _redis_fail()


def _refresh_async(query: str, key: str, ttl: int) -> None:
    with _refresh_lock:
        if key in _refreshing:
            return
        _refreshing.add(key)

    def run():
        try:
            result = _find_player_uncached(query)
            if result.get("found"):
                _store(key, result, ttl)
        finally:
            with _refresh_lock:
                _refreshing.discard(key)

    threading.Thread(target=run, daemon=True).start()


def find_player(query: str, *, force: bool = False) -> dict:
    key = (query or "").strip().lower()
    ttl = get_settings().faceit_cache_ttl_seconds
    if ttl <= 0:
        return _find_player_uncached(query)

    now = time.monotonic()
    if force:  # bypass all cache reads (manual refresh), but still repopulate it
        result = _find_player_uncached(query)
        if result.get("found"):
            _store(key, result, ttl)
        return result

    hit = _cache.get(key)
    if hit and (now - hit[0]) < ttl:
        return hit[1]

    cached, stale = _redis_get(key, ttl)
    if cached is not None:
        _cache_put(key, cached)  # warm the process-local fast path
        if stale:
            _refresh_async(query, key, ttl)
        return cached

    result = _find_player_uncached(query)
    if result.get("found"):
        _store(key, result, ttl)
    return result


def find_many(queries: list[str]) -> list[dict]:
    """Look up several players concurrently for head-to-head comparison."""
    if not queries:
        return []
    with ThreadPoolExecutor(max_workers=min(5, len(queries))) as pool:
        return list(pool.map(find_player, queries))
