import app.integrations.steam as steam_module
from app.integrations.steam import SteamIntegration


def test_official_owned_games_mapping(monkeypatch):
    integration = SteamIntegration()
    monkeypatch.setattr(integration, "_demo", lambda: False)
    monkeypatch.setattr(integration, "_official_key", lambda: "fake-key")

    def fake_get(path, params):
        assert path == "/IPlayerService/GetOwnedGames/v1/"
        assert params["key"] == "fake-key"
        return {"response": {"games": [{"appid": 730, "name": "Counter-Strike 2", "playtime_forever": 1234, "img_icon_url": "abc123"}]}}

    monkeypatch.setattr(integration, "_get", fake_get)
    games = integration.fetch_owned_games("76561198000000000")
    assert games == [{"app_id": 730, "name": "Counter-Strike 2", "playtime_forever": 1234, "img_icon_hash": "abc123"}]


def test_official_profile_private_visibility(monkeypatch):
    integration = SteamIntegration()
    monkeypatch.setattr(integration, "_demo", lambda: False)
    monkeypatch.setattr(integration, "_official_key", lambda: "fake-key")
    player = {"steamid": "76561198000000000", "personaname": "X", "communityvisibilitystate": 1, "personastate": 0}
    monkeypatch.setattr(integration, "_get", lambda path, params: {"response": {"players": [player]}})
    summary = integration.fetch_profile_summary("76561198000000000")
    assert summary["visibility"] == "private"
    assert summary["persona_name"] == "X"


def test_official_owned_games_without_key_returns_empty(monkeypatch):
    integration = SteamIntegration()
    monkeypatch.setattr(integration, "_demo", lambda: False)
    monkeypatch.setattr(integration, "_official_key", lambda: None)
    # Must not perform any HTTP call without a key.
    monkeypatch.setattr(steam_module.httpx, "get", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no HTTP without key")))
    assert integration.fetch_owned_games("76561198000000000") == []
