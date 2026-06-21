from types import SimpleNamespace

import app.faceit.service as faceit_service
from app.faceit.service import find_player, parse_steam_input


def test_parse_steam_input_variants():
    assert parse_steam_input("https://steamcommunity.com/profiles/76561198000000000") == ("76561198000000000", None)
    assert parse_steam_input("https://steamcommunity.com/id/s1mple") == (None, "s1mple")
    assert parse_steam_input("76561198000000000") == ("76561198000000000", None)
    assert parse_steam_input("s1mple") == (None, "s1mple")
    assert parse_steam_input("") == (None, None)


def test_find_returns_not_configured_without_key(client):
    resp = client.get("/api/v1/faceit/find", params={"steam": "76561198000000000"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["found"] is False
    assert body["configured"] is False


def test_find_player_maps_faceit_payload(monkeypatch):
    monkeypatch.setattr(faceit_service, "get_settings", lambda: SimpleNamespace(faceit_api_key="k", steam_api_key="s"))

    player = {
        "player_id": "abc-123",
        "nickname": "ProPlayer",
        "avatar": "https://faceit-cdn/avatar.jpg",
        "country": "ua",
        "faceit_url": "https://faceit.com/{lang}/players/ProPlayer",
        "games": {"cs2": {"skill_level": 10, "faceit_elo": 2450, "region": "EU"}},
    }
    lifetime = {"Matches": "1200", "Win Rate %": "58", "Average K/D Ratio": "1.15", "Average Headshots %": "49", "Recent Results": ["1", "1", "0", "1", "1"]}
    stats = {"lifetime": lifetime}

    def fake_get(path, params=None):
        if path == "/players":
            assert params["game"] == "cs2"
            return player
        return stats

    monkeypatch.setattr(faceit_service, "_faceit_get", fake_get)
    result = find_player("https://steamcommunity.com/profiles/76561198000000000")
    assert result["found"] is True
    assert result["nickname"] == "ProPlayer"
    assert result["skill_level"] == 10
    assert result["faceit_elo"] == 2450
    assert result["faceit_url"] == "https://faceit.com/en/players/ProPlayer"
    assert result["stats"]["matches"] == "1200"
    assert result["stats"]["kd_ratio"] == "1.15"


def test_find_player_not_found(monkeypatch):
    monkeypatch.setattr(faceit_service, "get_settings", lambda: SimpleNamespace(faceit_api_key="k", steam_api_key="s"))
    monkeypatch.setattr(faceit_service, "_faceit_get", lambda path, params=None: None)
    result = find_player("76561198000000000")
    assert result["found"] is False
    assert "No FACEIT profile" in result["message"]
