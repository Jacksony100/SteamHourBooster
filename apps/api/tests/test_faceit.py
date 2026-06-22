from types import SimpleNamespace

import app.faceit.service as faceit_service
from app.faceit.service import find_player, parse_steam_input


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
    monkeypatch.setattr(faceit_service, "get_settings", lambda: SimpleNamespace(faceit_api_key="k", steam_api_key="s"))
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

    monkeypatch.setattr(faceit_service, "get_settings", lambda: SimpleNamespace(faceit_api_key="k", steam_api_key="s"))
    monkeypatch.setattr(faceit_service, "_official_get", fake_official)
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
    monkeypatch.setattr(faceit_service, "get_settings", lambda: SimpleNamespace(faceit_api_key="k", steam_api_key="s"))

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
    result = find_player("76561198000000000")
    assert result["found"] is True
    assert result["detail_level"] == "full"
    assert result["source"] == "faceit_api"
    assert result["stats"]["matches"] == "1500"
    assert result["stats"]["avg_kills"] == "19"
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
