from steam_hour_booster.db import get_db
from steam_hour_booster.security.password_service import is_password_hash

from .conftest import give_subscription, login, register


def test_registration_hashes_password(app, client):
    response = register(client)

    assert response.status_code == 302
    with app.app_context():
        user = get_db().execute("SELECT password FROM users WHERE username='alice'").fetchone()
        assert user is not None
        assert is_password_hash(user["password"])
        assert "secret-pass" not in user["password"]


def test_login_sets_session(client):
    register(client)

    response = login(client)

    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_subscription_guard_redirects_without_subscription(client):
    register(client)
    login(client)

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/no_subscription"


def test_subscription_guard_allows_active_subscription(app, client):
    register(client)
    give_subscription(app)
    login(client)

    response = client.get("/")

    assert response.status_code == 200
