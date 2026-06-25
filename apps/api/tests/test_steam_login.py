from app.auth import steam_openid
from app.core.database import SessionLocal
from app.core.models import User


def test_steam_login_redirects_to_steam(client):
    resp = client.get("/api/v1/auth/steam/login", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"].startswith("https://steamcommunity.com/openid/login")
    assert "checkid_setup" in resp.headers["location"]


def test_steam_callback_creates_user_and_session(client, monkeypatch):
    monkeypatch.setattr(steam_openid, "verify_steam_response", lambda params: "76561198000000001")
    monkeypatch.setattr(steam_openid, "fetch_persona", lambda sid: "s1mple")

    resp = client.get("/api/v1/auth/steam/callback", params={"openid.mode": "id_res"}, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"].endswith("/dashboard")
    # session cookie was set
    assert any("deckpilot_session" in v for v in resp.headers.get_list("set-cookie"))

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.steam_id == "76561198000000001").one()
        assert user.username == "s1mple"
    finally:
        db.close()

    # /me now works with the issued session cookie
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "s1mple"


def test_steam_callback_invalid_redirects_to_login(client, monkeypatch):
    monkeypatch.setattr(steam_openid, "verify_steam_response", lambda params: None)
    resp = client.get("/api/v1/auth/steam/callback", params={"openid.mode": "id_res"}, follow_redirects=False)
    assert resp.status_code == 302
    assert "error=steam" in resp.headers["location"]


def test_get_or_create_steam_user_idempotent_and_unique_username(client, monkeypatch):
    from app.auth.service import get_or_create_steam_user

    db = SessionLocal()
    try:
        # Occupy the persona name so the second Steam user gets a unique suffix.
        db.add(User(username="taken", password_hash="x"))
        db.commit()
        u1 = get_or_create_steam_user(db, "76561198000000002", None, persona="taken")
        u2 = get_or_create_steam_user(db, "76561198000000002", None, persona="taken")
        assert u1.id == u2.id  # idempotent on steam_id
        assert u1.username != "taken"  # username collision avoided
        assert u1.steam_id == "76561198000000002"
    finally:
        db.close()
