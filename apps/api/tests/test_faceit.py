from types import SimpleNamespace

import app.faceit.service as faceit_service
from app.faceit.service import find_player, parse_steam_input

from .conftest import csrf, register


def _settings(**overrides):
    """Fake settings with all FACEIT-relevant fields, overridable per test."""
    base = {
        "faceit_api_key": "",
        "steam_api_key": "",
        "faceit_cache_ttl_seconds": 120,
        "faceit_match_limit": 20,
        "faceit_elo_history_size": 30,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_parse_steam_input_variants():
    assert parse_steam_input("https://steamcommunity.com/profiles/76561198000000000") == ("76561198000000000", None)
    assert parse_steam_input("https://steamcommunity.com/id/s1mple") == (None, "s1mple")
    assert parse_steam_input("76561198000000000") == ("76561198000000000", None)
    assert parse_steam_input("s1mple") == (None, "s1mple")
    assert parse_steam_input("") == (None, None)


def test_find_bad_input_no_network(client):
    # '@@@' parses to nothing -> short-circuits before any HTTP call.
    resp = client.get("/api/v1/faceit/find", params={"steam": "@@@"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["found"] is False
    assert body["message"]


def test_find_by_faceit_nickname_official(monkeypatch):
    monkeypatch.setattr(faceit_service, "get_settings", lambda: _settings(faceit_api_key="k", steam_api_key="s"))
    player = {"player_id": "PID", "nickname": "donk666", "games": {"cs2": {"skill_level": 10, "faceit_elo": 5000, "game_player_id": "765611980"}}}

    def fake_official(path, params=None):
        if path == "/players" and params and params.get("nickname") == "donk666":
            return player
        if path.endswith("/stats/cs2"):
            return {"lifetime": {"Matches": "7000", "Average K/D Ratio": "1.4"}, "segments": []}
        if path.endswith("/history"):
            return {"items": []}
        return None

    monkeypatch.setattr(faceit_service, "_official_get", fake_official)
    monkeypatch.setattr(faceit_service, "_get_json", lambda *a, **k: None)
    result = find_player("donk666")  # a bare FACEIT nickname, not a Steam link
    assert result["found"] is True
    assert result["nickname"] == "donk666"
    assert result["faceit_elo"] == 5000
    assert result["stats"]["kd_ratio"] == "1.4"


def test_result_cache_returns_same_object(monkeypatch):
    calls = {"n": 0}

    def fake_official(path, params=None):
        if path == "/players":
            calls["n"] += 1
            return {"player_id": "P", "nickname": "x", "games": {"cs2": {"skill_level": 5, "faceit_elo": 1500, "game_player_id": "765"}}}
        return {"lifetime": {}, "segments": [], "items": []} if path.endswith(("stats/cs2", "history")) else None

    monkeypatch.setattr(faceit_service, "get_settings", lambda: _settings(faceit_api_key="k", steam_api_key="s"))
    monkeypatch.setattr(faceit_service, "_official_get", fake_official)
    monkeypatch.setattr(faceit_service, "_get_json", lambda *a, **k: None)
    faceit_service.reset_faceit_cache()
    find_player("CachedNick")
    find_player("cachednick")  # case-insensitive cache key
    assert calls["n"] == 1  # second lookup served from cache


def test_find_player_keyless_mapping(monkeypatch):
    cs2 = {"cs2": {"skill_level": 10, "faceit_elo": 2450, "region": "EU"}}
    profile = {"nickname": "ProPlayer", "avatar": "https://cdn/a.jpg", "country": "ua", "games": cs2}
    # Keyless stats use FACEIT's coded keys (m1=matches, m2=wins, k5=K/D, k8=HS%, s0=recent).
    lifetime = {"m1": "1200", "m2": "696", "k5": "1.15", "k8": "49", "s0": ["1", "1", "0", "1", "1"], "s1": "2", "s7": "5"}

    def fake_get(url, params=None, headers=None):
        if "/users/v1/users/" in url:  # profile by guid
            return {"payload": profile}
        if url.endswith("/users/v1/users"):  # steamid -> guid
            return {"payload": {"id": "guid-1"}}
        if "/stats/v1/stats/users/" in url:
            return {"lifetime": lifetime}
        return None

    monkeypatch.setattr(faceit_service, "_get_json", fake_get)
    result = find_player("https://steamcommunity.com/profiles/76561198000000000")
    assert result["found"] is True
    assert result["source"] == "faceit_web"
    assert result["nickname"] == "ProPlayer"
    assert result["skill_level"] == 10
    assert result["faceit_elo"] == 2450
    assert result["faceit_url"] == "https://www.faceit.com/en/players/ProPlayer"
    assert result["stats"]["matches"] == "1200"
    assert result["stats"]["kd_ratio"] == "1.15"
    assert result["stats"]["headshots"] == "49"
    assert result["stats"]["win_rate"] == "58"  # round(696/1200*100)
    assert result["stats"]["recent_results"] == ["1", "1", "0", "1", "1"]


def test_find_player_official_full_parse(monkeypatch):
    # With a key set, find_player uses the official API and parses lifetime + maps + last matches.
    monkeypatch.setattr(faceit_service, "get_settings", lambda: _settings(faceit_api_key="k", steam_api_key="s"))

    player = {
        "player_id": "PID",
        "nickname": "Pro",
        "avatar": "https://faceit/a.jpg",
        "country": "ua",
        "faceit_url": "https://faceit.com/{lang}/players/Pro",
        "games": {"cs2": {"skill_level": 10, "faceit_elo": 2500, "region": "EU"}},
    }
    life = {"Matches": "1500", "Win Rate %": "57", "Average K/D Ratio": "1.20", "Average Headshots %": "52", "Average Kills": "19"}
    life["Recent Results"] = ["1", "1", "0", "1", "1"]
    stats = {
        "lifetime": life,
        "segments": [
            {"type": "Map", "label": "de_mirage", "stats": {"Matches": "300", "Win Rate %": "60", "Average K/D Ratio": "1.25"}},
            {"type": "Map", "label": "de_inferno", "stats": {"Matches": "120", "Win Rate %": "50", "Average K/D Ratio": "1.10"}},
        ],
    }
    history = {"items": [{"match_id": "M1", "started_at": 1700000000, "faceit_url": "https://faceit.com/{lang}/cs2/room/M1"}]}
    pstats = {"Kills": "24", "Deaths": "16", "K/D Ratio": "1.50", "Headshots %": "55", "Result": "1"}
    match_stats = {"rounds": [{"round_stats": {"Map": "de_mirage", "Score": "13 / 9"}, "teams": [{"players": [{"player_id": "PID", "player_stats": pstats}]}]}]}

    def fake_official(path, params=None):
        if path == "/players":
            return player
        if path.endswith("/stats/cs2"):
            return stats
        if path.endswith("/history"):
            return history
        if path.startswith("/matches/"):
            return match_stats
        return None

    monkeypatch.setattr(faceit_service, "_official_get", fake_official)
    monkeypatch.setattr(faceit_service, "_get_json", lambda *a, **k: None)  # keyless ELO blocked -> reconstruct
    result = find_player("76561198000000000")
    assert result["found"] is True
    assert result["detail_level"] == "full"
    assert result["source"] == "faceit_api"
    assert result["stats"]["matches"] == "1500"
    assert result["stats"]["avg_kills"] == "19"
    # keyless ELO history blocked -> reconstructed from the single (won) match, ending at current ELO
    assert result["elo_history_approx"] is True
    assert result["elo_history"][-1]["elo"] == 2500
    # maps sorted by matches desc, named
    assert result["maps"][0]["name"] == "de_mirage"
    assert result["maps"][0]["win_rate"] == "60"
    # last match parsed with per-match K/D + result
    m0 = result["matches"][0]
    assert m0["map"] == "de_mirage"
    assert m0["kd_ratio"] == "1.50"
    assert m0["result"] == "win"
    assert m0["score"] == "13 / 9"
    assert m0["date"] == "2023-11-14"


def test_elo_history_parse_orders_oldest_first(monkeypatch):
    # FACEIT's time endpoint returns newest-first with ms timestamps; we flip to oldest→newest.
    series = [
        {"elo": "2450", "created_at": 1700200000000},
        {"elo": "2475", "created_at": 1700100000000},
        {"elo": "bad", "created_at": 1700050000000},  # unparseable elo -> skipped
        {"elo": "2430", "created_at": 1700000000000},
    ]

    def fake_get(url, params=None, headers=None):
        return series if "/stats/v1/stats/time/users/" in url else None

    monkeypatch.setattr(faceit_service, "get_settings", lambda: _settings(faceit_elo_history_size=30))
    monkeypatch.setattr(faceit_service, "_get_json", fake_get)
    history = faceit_service._elo_history("guid-1")
    assert [p["elo"] for p in history] == [2430, 2475, 2450]  # oldest -> newest, "bad" dropped
    assert history[0]["date"] == "2023-11-14"


def test_elo_history_in_keyless_find(monkeypatch):
    profile = {"nickname": "P", "games": {"cs2": {"skill_level": 8, "faceit_elo": 2000}}}

    def fake_get(url, params=None, headers=None):
        if "/users/v1/users/" in url:
            return {"payload": profile}
        if url.endswith("/users/v1/users"):
            return {"payload": {"id": "g"}}
        if "/stats/v1/stats/time/users/" in url:
            return [{"elo": "2000", "created_at": 1700100000000}, {"elo": "1980", "created_at": 1700000000000}]
        return None

    monkeypatch.setattr(faceit_service, "_get_json", fake_get)
    result = find_player("76561198000000000")
    assert [p["elo"] for p in result["elo_history"]] == [1980, 2000]


def test_reconstruct_elo_history_walks_back_from_current():
    # matches are newest-first; reconstruction ends exactly at current ELO.
    matches = [{"result": "win", "date": "d3"}, {"result": "loss", "date": "d2"}, {"result": "win", "date": "d1"}]
    pts = faceit_service._reconstruct_elo_history(1000, matches)
    assert [p["elo"] for p in pts] == [1000, 975, 1000]  # oldest->newest
    assert [p["date"] for p in pts] == ["d1", "d2", "d3"]
    assert pts[-1]["elo"] == 1000  # newest point == current ELO (exact)


def test_reconstruct_elo_history_floor_and_empty():
    assert faceit_service._reconstruct_elo_history(1000, []) == []
    assert faceit_service._reconstruct_elo_history(None, [{"result": "win"}]) == []
    # never drops below the FACEIT floor of 100
    pts = faceit_service._reconstruct_elo_history(120, [{"result": "win"}] * 5)
    assert min(p["elo"] for p in pts) >= 100


def test_compare_route_returns_both(client, monkeypatch):
    def fake_find(query):
        return {
            "found": True, "configured": True, "nickname": query, "skill_level": 7,
            "faceit_elo": 1500, "stats": {"kd_ratio": "1.1"}, "elo_history": [], "detail_level": "full",
        }

    monkeypatch.setattr(faceit_service, "find_player", fake_find)
    resp = client.get("/api/v1/faceit/compare?players=alpha&players=bravo&players=charlie")
    assert resp.status_code == 200
    body = resp.json()
    nicks = [p["nickname"] for p in body["players"]]
    assert nicks == ["alpha", "bravo", "charlie"]
    assert body["players"][0]["stats"]["kd_ratio"] == "1.1"


def test_compare_route_rejects_too_few(client):
    resp = client.get("/api/v1/faceit/compare?players=alpha")
    assert resp.status_code == 422


def test_cached_lookup_keeps_stats_across_requests(client, monkeypatch):
    # Regression: the route must not pop "stats" off the cached dict, or a second
    # cache hit (incl. comparing a player against themselves) loses all stats.
    monkeypatch.setattr(faceit_service, "get_settings", lambda: _settings(faceit_api_key="k", steam_api_key="s"))

    def fake_official(path, params=None):
        if path == "/players":
            return {"player_id": "PID", "nickname": "Same", "games": {"cs2": {"skill_level": 9, "faceit_elo": 2200, "game_player_id": "765"}}}
        if path.endswith("/stats/cs2"):
            return {"lifetime": {"Matches": "900", "Average K/D Ratio": "1.3"}, "segments": []}
        return {"items": []} if path.endswith("/history") else None

    monkeypatch.setattr(faceit_service, "_official_get", fake_official)
    monkeypatch.setattr(faceit_service, "_get_json", lambda *a, **k: None)
    faceit_service.reset_faceit_cache()

    first = client.get("/api/v1/faceit/find", params={"steam": "Same"}).json()
    second = client.get("/api/v1/faceit/find", params={"steam": "Same"}).json()  # cache hit
    assert first["stats"]["kd_ratio"] == "1.3"
    assert second["stats"]["kd_ratio"] == "1.3"  # would be None if the cached dict were mutated

    # Comparing a player to themselves: both sides keep full stats.
    cmp = client.get("/api/v1/faceit/compare?players=Same&players=Same").json()
    assert cmp["players"][0]["stats"]["matches"] == "900"
    assert cmp["players"][1]["stats"]["matches"] == "900"


def test_find_player_not_found(monkeypatch):
    monkeypatch.setattr(faceit_service, "_get_json", lambda url, params=None, headers=None: None)
    result = find_player("76561198000000000")
    assert result["found"] is False
    assert "No FACEIT profile" in result["message"]


def test_find_player_route_keyless(client, monkeypatch):
    def fake_get(url, params=None, headers=None):
        if "/users/v1/users/" in url:
            return {"payload": {"nickname": "x", "games": {"cs2": {"skill_level": 7, "faceit_elo": 1500}}}}
        if url.endswith("/users/v1/users"):
            return {"payload": {"id": "g"}}
        return None

    monkeypatch.setattr(faceit_service, "_get_json", fake_get)
    resp = client.get("/api/v1/faceit/find", params={"steam": "76561198000000000"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["found"] is True
    assert body["skill_level"] == 7
    assert body["source"] == "faceit_web"


# ---------------------------------------------------------------------------
# Enrichment: teammates, recent form, streak, smurf heuristic
# ---------------------------------------------------------------------------

def test_aggregate_teammates_counts_and_winrate():
    parsed = [
        ({"result": "win"}, [{"player_id": "T1", "nickname": "Duo"}, {"player_id": "T2", "nickname": "X"}], {}),
        ({"result": "loss"}, [{"player_id": "T1", "nickname": "Duo"}], {}),
        ({"result": "win"}, [{"player_id": "T1", "nickname": "Duo"}], {}),
    ]
    out = faceit_service._aggregate_teammates(parsed)
    duo = next(t for t in out if t["player_id"] == "T1")
    assert duo["games"] == 3 and duo["wins"] == 2 and duo["win_rate"] == "67"
    assert all(t["games"] >= 2 for t in out)  # one-off teammates dropped


def test_recent_form_streak_and_smurf():
    matches = [
        {"result": "loss", "kd_ratio": "0.9", "adr": "70", "headshots": "60"},
        {"result": "loss", "kd_ratio": "1.0", "adr": "75", "headshots": "58"},
        {"result": "loss", "kd_ratio": "1.1", "adr": "80", "headshots": "62"},
        {"result": "win", "kd_ratio": "2.0", "adr": "110", "headshots": "70"},
    ]
    form = faceit_service._recent_form(matches, {"Average K/D Ratio": "1.0"})
    assert form["matches"] == 4 and form["wins"] == 1 and form["win_rate"] == 25
    streak = faceit_service._streak(matches)
    assert streak == {"type": "loss", "length": 3, "tilt": True}
    smurf = faceit_service._smurf_heuristic(3, {"Matches": "50", "Average K/D Ratio": "1.4"}, form)
    assert smurf and smurf["score"] >= 40 and smurf["flags"]


# ---------------------------------------------------------------------------
# Match scoreboard drill-down
# ---------------------------------------------------------------------------

def test_match_scoreboard(client, monkeypatch):
    board = {
        "rounds": [{
            "round_stats": {"Map": "de_nuke", "Score": "13 / 7"},
            "teams": [
                {"team_id": "A", "team_stats": {"Team Win": "1", "Final Score": "13"},
                 "players": [{"player_id": "p1", "nickname": "Ace", "player_stats": {"Kills": "30", "Deaths": "10", "K/D Ratio": "3.0", "ADR": "120"}}]},
                {"team_id": "B", "team_stats": {"Team Win": "0", "Final Score": "7"},
                 "players": [{"player_id": "p2", "nickname": "Bob", "player_stats": {"Kills": "12", "Deaths": "18", "K/D Ratio": "0.67"}}]},
            ],
        }]
    }
    monkeypatch.setattr(faceit_service, "_official_get", lambda path, params=None: board)
    resp = client.get("/api/v1/faceit/match/M123")
    assert resp.status_code == 200
    body = resp.json()
    assert body["map"] == "de_nuke"
    assert body["teams"][0]["win"] is True
    assert body["teams"][0]["players"][0]["nickname"] == "Ace"


def test_match_scoreboard_404(client, monkeypatch):
    monkeypatch.setattr(faceit_service, "_official_get", lambda path, params=None: None)
    assert client.get("/api/v1/faceit/match/none").status_code == 404


# ---------------------------------------------------------------------------
# ELO snapshots: real series overlays the reconstruction once 2+ days exist
# ---------------------------------------------------------------------------

def test_snapshot_series_and_route_overlay(client, monkeypatch):
    from app.core.database import SessionLocal
    from app.core.models import FaceitEloSnapshot
    from app.faceit.snapshots import snapshot_series

    db = SessionLocal()
    try:
        db.add(FaceitEloSnapshot(player_id="PID", elo=1000, captured_on="2020-01-01"))
        db.add(FaceitEloSnapshot(player_id="PID", elo=1020, captured_on="2020-01-02"))
        db.commit()
        assert [p["elo"] for p in snapshot_series(db, "PID")] == [1000, 1020]
    finally:
        db.close()

    monkeypatch.setattr(faceit_service, "get_settings", lambda: _settings(faceit_api_key="k", steam_api_key="s"))
    monkeypatch.setattr(faceit_service, "_get_json", lambda *a, **k: None)

    def fake_official(path, params=None):
        if path == "/players":
            return {"player_id": "PID", "nickname": "Snap", "games": {"cs2": {"skill_level": 8, "faceit_elo": 1030, "game_player_id": "765"}}}
        return {"items": []} if path.endswith("/history") else {"lifetime": {}, "segments": []}

    monkeypatch.setattr(faceit_service, "_official_get", fake_official)
    faceit_service.reset_faceit_cache()
    body = client.get("/api/v1/faceit/find", params={"steam": "76561198000000000"}).json()
    assert body["elo_history_approx"] is False  # real snapshots overlaid the reconstruction
    assert body["elo_history"][0]["elo"] == 1000


def test_snapshot_dedupes_per_day():
    from app.core.database import SessionLocal
    from app.faceit.snapshots import record_elo_snapshot, snapshot_series

    db = SessionLocal()
    try:
        record_elo_snapshot(db, "DEDUP", 1500, nickname="d")
        record_elo_snapshot(db, "DEDUP", 1525, nickname="d")  # same day -> updates, not appends
        series = snapshot_series(db, "DEDUP")
        assert len(series) == 1 and series[0]["elo"] == 1525
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Watchlist (authenticated)
# ---------------------------------------------------------------------------

def test_watchlist_add_list_remove(client):
    register(client, "watcher", "secret123")
    headers = {"X-CSRF-Token": csrf(client)}

    add = client.post("/api/v1/faceit/watchlist", json={"player_id": "PID1", "nickname": "donk", "country": "ru"}, headers=headers)
    assert add.status_code == 200
    assert any(w["player_id"] == "PID1" for w in add.json()["items"])

    listed = client.get("/api/v1/faceit/watchlist")
    assert listed.status_code == 200 and len(listed.json()["items"]) == 1

    removed = client.delete("/api/v1/faceit/watchlist/PID1", headers=headers)
    assert removed.status_code == 200 and removed.json()["items"] == []


def test_watchlist_requires_auth(client):
    assert client.get("/api/v1/faceit/watchlist").status_code == 401


# ---------------------------------------------------------------------------
# Advanced aggregates: deep stats, consistency, percentile, activity, radar
# ---------------------------------------------------------------------------

def test_advanced_stats_from_raw():
    raws = [
        {"Entry Count": "4", "Entry Wins": "2", "1v1Count": "2", "1v1Wins": "1", "1v2Count": "1", "1v2Wins": "1",
         "Enemies Flashed": "6", "Utility Damage": "120", "Sniper Kills": "3", "Pistol Kills": "5",
         "Penta Kills": "1", "Quadro Kills": "0", "Triple Kills": "2", "Kills": "24", "Deaths": "16", "Assists": "5"},
        {"Entry Count": "2", "Entry Wins": "1", "1v1Count": "0", "1v1Wins": "0", "1v2Count": "1", "1v2Wins": "0",
         "Enemies Flashed": "4", "Utility Damage": "80", "Sniper Kills": "1", "Pistol Kills": "3",
         "Penta Kills": "0", "Quadro Kills": "1", "Triple Kills": "1", "Kills": "18", "Deaths": "20", "Assists": "7"},
    ]
    adv = faceit_service._advanced_stats(raws)
    assert adv["entry_success"] == 50  # (2+1)/(4+2)=50%
    assert adv["clutch_1v1"] == 50     # 1/2
    assert adv["aces"] == 1 and adv["quad_kills"] == 1 and adv["triple_kills"] == 3
    assert adv["pistol_total"] == 8
    assert adv["avg_kills"] == 21.0
    assert faceit_service._advanced_stats([]) is None


def test_consistency_percentile_activity():
    steady = [{"kd_ratio": "1.10"}, {"kd_ratio": "1.12"}, {"kd_ratio": "1.08"}]
    swingy = [{"kd_ratio": "0.4"}, {"kd_ratio": "2.2"}, {"kd_ratio": "0.6"}]
    assert faceit_service._consistency(steady) > faceit_service._consistency(swingy)
    assert faceit_service._consistency([{"kd_ratio": "1.0"}]) is None  # needs >=3
    p_low = faceit_service._percentile(500)
    p_high = faceit_service._percentile(3000)
    assert 1 <= p_low < p_high <= 99
    act = faceit_service._activity([{"date": "2024-01-01"}, {"date": "2024-01-01"}, {"date": "bad"}])
    assert sum(act) == 2 and len(act) == 7


def test_best_worst_and_refresh(monkeypatch):
    best, worst = faceit_service._best_worst([{"kills": "30"}, {"kills": "5"}, {"kills": "18"}])
    assert best["kills"] == "30" and worst["kills"] == "5"
    assert faceit_service._best_worst([{"kills": "1"}]) == (None, None)

    # force=True bypasses the cache (re-fetches every call)
    calls = {"n": 0}
    def fake_uncached(q):
        calls["n"] += 1
        return {"found": True, "player_id": "P", "faceit_elo": 1, "stats": {}}
    monkeypatch.setattr(faceit_service, "_find_player_uncached", fake_uncached)
    monkeypatch.setattr(faceit_service, "get_settings", lambda: _settings(faceit_cache_ttl_seconds=120))
    faceit_service.reset_faceit_cache()
    faceit_service.find_player("X")
    faceit_service.find_player("X", force=True)
    assert calls["n"] == 2  # force re-fetched instead of serving cache
