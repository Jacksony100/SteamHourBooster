from steam_hour_booster.db import get_db

from .conftest import login, register


def test_add_account_encrypts_credentials(app, client):
    register(client)
    login(client)

    response = client.post(
        "/add_account",
        json={"username": "steam-user", "password": "steam-pass", "shared_secret": ""},
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True
    with app.app_context():
        account = get_db().execute("SELECT username, password FROM accounts").fetchone()
        assert account is not None
        assert account["username"] != "steam-user"
        assert account["password"] != "steam-pass"


def test_user_cannot_access_another_users_account(client):
    register(client, "alice", "alice-pass")
    login(client, "alice", "alice-pass")
    add_response = client.post(
        "/add_account",
        json={"username": "alice-steam", "password": "steam-pass"},
    )
    account_id = add_response.get_json()["account_id"]
    client.get("/logout")

    register(client, "bob", "bob-pass")
    login(client, "bob", "bob-pass")
    response = client.post("/delete_account", json={"id": account_id})

    assert response.status_code == 404
    assert response.get_json()["code"] == "account_not_found"
