from types import SimpleNamespace

import app.steam_accounts.service as steam_account_service

from .conftest import csrf, register


def test_account_owner_only_access(client):
    register(client, "alice", "secret123")
    headers = {"X-CSRF-Token": csrf(client)}
    create = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Main", "username": "steam-a", "password": "steam-pass", "ownership_attested": True},
        headers=headers,
    )
    assert create.status_code == 200
    account_id = create.json()["id"]

    client.post("/api/v1/auth/logout", headers=headers)
    register(client, "bob", "secret123")
    delete = client.delete(f"/api/v1/steam-accounts/{account_id}", headers={"X-CSRF-Token": csrf(client)})

    assert delete.status_code == 404


def test_add_account_requires_ownership_attestation(client):
    register(client)
    response = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Main", "username": "steam-a", "password": "steam-pass", "ownership_attested": False},
        headers={"X-CSRF-Token": csrf(client)},
    )
    assert response.status_code == 400


def test_demo_account_does_not_require_password(client):
    register(client)
    create = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Demo", "display_name": "Demo Steam profile", "ownership_attested": True},
        headers={"X-CSRF-Token": csrf(client)},
    )

    assert create.status_code == 200
    assert create.json()["label"] == "Demo"

    login = client.post(f"/api/v1/steam-accounts/{create.json()['id']}/login", json={}, headers={"X-CSRF-Token": csrf(client)})
    assert login.status_code == 200
    assert login.json()["status"] == "online"


def test_production_rejects_password_based_steam_account_submission(client, monkeypatch):
    monkeypatch.setattr(
        steam_account_service,
        "get_settings",
        lambda: SimpleNamespace(environment="production", steam_integration_mode="demo", steam_official_linking_enabled=False, steam_api_key=""),
    )
    register(client)

    response = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Main", "username": "steam-a", "password": "steam-pass", "ownership_attested": True},
        headers={"X-CSRF-Token": csrf(client)},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Password-based Steam linking is disabled in this environment"


def test_official_mode_without_config_returns_controlled_error(client, monkeypatch):
    monkeypatch.setattr(
        steam_account_service,
        "get_settings",
        lambda: SimpleNamespace(environment="development", steam_integration_mode="official", steam_official_linking_enabled=False, steam_api_key=""),
    )
    register(client)

    response = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Official", "steam_id": "76561198000000000", "ownership_attested": True},
        headers={"X-CSRF-Token": csrf(client)},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Official Steam linking is not configured yet"


def test_account_responses_do_not_include_raw_credentials(client):
    register(client)
    response = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Main", "username": "steam-a", "password": "steam-pass", "ownership_attested": True},
        headers={"X-CSRF-Token": csrf(client)},
    )

    assert response.status_code == 200
    assert "steam-pass" not in response.text
    assert "password" not in response.text.lower()
