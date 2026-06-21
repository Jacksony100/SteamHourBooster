from .conftest import csrf, register


def _create_account(client, label="Main"):
    return client.post(
        "/api/v1/steam-accounts",
        json={"label": label, "display_name": "Demo profile", "ownership_attested": True},
        headers={"X-CSRF-Token": csrf(client)},
    )


def test_steam_profile_returns_avatar_from_steam_cdn(client):
    register(client)
    account_id = _create_account(client).json()["id"]

    resp = client.get(f"/api/v1/accounts/{account_id}/steam-profile")
    assert resp.status_code == 200
    body = resp.json()
    assert body["account_id"] == account_id
    assert body["avatar_full"].startswith("https://avatars.cloudflare.steamstatic.com/")
    assert body["visibility"] == "public"


def test_owned_games_have_steam_cdn_artwork(client):
    register(client)
    account_id = _create_account(client).json()["id"]

    resp = client.get(f"/api/v1/accounts/{account_id}/owned-games")
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] >= 1
    game = body["games"][0]
    assert game["header_image_url"] == f"https://cdn.cloudflare.steamstatic.com/steam/apps/{game['app_id']}/header.jpg"
    assert game["store_url"] == f"https://store.steampowered.com/app/{game['app_id']}/"


def test_game_assets_endpoint_builds_known_cdn_urls(client):
    register(client)
    resp = client.get("/api/v1/games/730/assets")
    assert resp.status_code == 200
    body = resp.json()
    assert body["header_image_url"] == "https://cdn.cloudflare.steamstatic.com/steam/apps/730/header.jpg"
    assert body["library_image_url"] == "https://cdn.cloudflare.steamstatic.com/steam/apps/730/library_600x900.jpg"


def test_owned_games_refresh_requires_csrf(client):
    register(client)
    account_id = _create_account(client).json()["id"]
    # No CSRF header -> rejected.
    resp = client.post(f"/api/v1/accounts/{account_id}/owned-games/refresh", json={})
    assert resp.status_code == 403


def test_steam_profile_owner_only(client):
    register(client, "alice", "secret123")
    account_id = _create_account(client).json()["id"]
    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf(client)})

    register(client, "bob", "secret123")
    resp = client.get(f"/api/v1/accounts/{account_id}/steam-profile")
    assert resp.status_code == 404


def test_steam_profile_requires_auth(client):
    resp = client.get("/api/v1/accounts/1/steam-profile")
    assert resp.status_code == 401
