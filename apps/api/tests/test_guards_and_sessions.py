from .conftest import activate_subscription, csrf, login, make_admin_user, register


def _create_online_account_with_game(client):
    create = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Main", "username": "steam-a", "password": "steam-pass", "ownership_attested": True},
        headers={"X-CSRF-Token": csrf(client)},
    )
    account_id = create.json()["id"]
    client.post(f"/api/v1/steam-accounts/{account_id}/login", json={}, headers={"X-CSRF-Token": csrf(client)})
    client.put(f"/api/v1/games/{account_id}", json={"app_ids": [730]}, headers={"X-CSRF-Token": csrf(client)})
    return account_id


def test_admin_guard(client):
    register(client)
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 403

    client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf(client)})
    make_admin_user()
    login(client, "admin", "admin-password")
    allowed = client.get("/api/v1/admin/users")
    assert allowed.status_code == 200


def test_subscription_guard_for_session_start(client):
    register(client)
    account_id = _create_online_account_with_game(client)
    denied = client.post("/api/v1/sessions", json={"account_id": account_id}, headers={"X-CSRF-Token": csrf(client)})
    assert denied.status_code == 402

    activate_subscription()
    allowed = client.post("/api/v1/sessions", json={"account_id": account_id}, headers={"X-CSRF-Token": csrf(client)})
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "running"
