from app.auth.service import issue_email_verification_token, issue_password_reset_token
from app.core.database import SessionLocal
from app.core.models import User, UserSession

from .conftest import csrf, login, register


def test_register_and_login_sets_secure_cookies(client):
    response = register(client)

    assert response.status_code == 200
    assert client.cookies.get("deckpilot_session")
    assert client.cookies.get("deckpilot_csrf")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "alice").one()
        assert user.password_hash != "secret123"
    finally:
        db.close()

    login_response = login(client)
    assert login_response.status_code == 200


def test_legacy_cookie_names_are_accepted_during_migration(client):
    register(client)
    legacy_session = client.cookies.get("deckpilot_session")
    legacy_csrf = csrf(client)

    client.cookies.clear()
    client.cookies.set("shb_session", legacy_session)
    client.cookies.set("shb_csrf", legacy_csrf)

    me = client.get("/api/v1/auth/me")
    logout = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": legacy_csrf})

    assert me.status_code == 200
    assert logout.status_code == 200


def test_password_reset_changes_password_and_revokes_sessions(client):
    register(client)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "alice").one()
        token = issue_password_reset_token(db, user)
    finally:
        db.close()

    reset = client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "password": "new-secret-123"})
    revoked_session = client.get("/api/v1/auth/me")
    old_login = login(client)
    new_login = login(client, password="new-secret-123")
    reuse = client.post("/api/v1/auth/password-reset/confirm", json={"token": token, "password": "another-secret-123"})

    assert reset.status_code == 200
    assert revoked_session.status_code == 401
    assert old_login.status_code == 401
    assert new_login.status_code == 200
    assert reuse.status_code == 400


def test_password_reset_request_is_generic_for_unknown_users(client):
    response = client.post("/api/v1/auth/password-reset/request", json={"username": "missing@example.test"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_email_verification_flow(client):
    register(client, "alice", "secret123")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "alice").one()
        token = issue_email_verification_token(db, user, "alice@example.test")
    finally:
        db.close()

    response = client.post("/api/v1/auth/email-verification/confirm", json={"token": token})

    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.test"
    assert response.json()["email_verified"] is True


def test_user_can_revoke_current_session(client):
    register(client)
    sessions = client.get("/api/v1/auth/sessions")
    session_id = sessions.json()[0]["id"]

    response = client.delete(f"/api/v1/auth/sessions/{session_id}", headers={"X-CSRF-Token": csrf(client)})

    assert response.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    db = SessionLocal()
    try:
        session = db.get(UserSession, session_id)
        assert session.revoked_at is not None
    finally:
        db.close()


def test_export_does_not_include_credentials_or_tokens(client):
    register(client)
    created = client.post(
        "/api/v1/steam-accounts",
        json={"label": "Main", "username": "steam-a", "password": "steam-pass", "ownership_attested": True},
        headers={"X-CSRF-Token": csrf(client)},
    )
    response = client.get("/api/v1/auth/export")

    assert created.status_code == 200
    assert response.status_code == 200
    text = response.text.lower()
    assert "steam-pass" not in text
    assert "password_hash" not in text
    assert "password_encrypted" not in text
    assert "token_hash" not in text


def test_user_can_delete_own_account(client):
    register(client)

    response = client.delete("/api/v1/auth/account", headers={"X-CSRF-Token": csrf(client)})

    assert response.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    db = SessionLocal()
    try:
        assert db.query(User).filter(User.username == "alice").one_or_none() is None
    finally:
        db.close()
