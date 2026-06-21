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
    assert "Could not read" in body["message"]


def test_find_player_keyless_mapping(monkeypatch):
    cs2 = {"cs2": {"skill_level": 10, "faceit_elo": 2450, "region": "EU"}}
    profile = {"nickname": "ProPlayer", "avatar": "https://cdn/a.jpg", "country": "ua", "games": cs2}
    # Keyless stats use FACEIT's coded keys (m1=matches, m2=wins, k5=K/D, m7=HS%, s0=recent).
    lifetime = {"m1": "1200", "m2": "696", "k5": "1.15", "m7": "49", "s0": ["1", "1", "0", "1", "1"], "s1": "2", "s7": "5"}

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
    assert result["stats"]["win_rate"] == "58"  # round(696/1200*100)
    assert result["stats"]["recent_results"] == ["1", "1", "0", "1", "1"]


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
