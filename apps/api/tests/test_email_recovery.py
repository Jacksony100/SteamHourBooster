from app.core.mailer import get_mailer

from .conftest import csrf, register


def test_password_reset_request_sends_email(client):
    register(client, "alice", "secret123")
    # Attach an email via verification request flow.
    client.post(
        "/api/v1/auth/email-verification/request",
        json={"email": "alice@example.com"},
        headers={"X-CSRF-Token": csrf(client)},
    )
    outbox_before = len(get_mailer().outbox)
    resp = client.post("/api/v1/auth/password-reset/request", json={"username": "alice"})
    assert resp.status_code == 200
    outbox = get_mailer().outbox
    assert len(outbox) == outbox_before + 1
    msg = outbox[-1]
    assert msg.to == "alice@example.com"
    assert "reset-password?token=" in msg.text


def test_email_verification_sends_and_confirms(client):
    register(client, "bob", "secret123")
    resp = client.post(
        "/api/v1/auth/email-verification/request",
        json={"email": "bob@example.com"},
        headers={"X-CSRF-Token": csrf(client)},
    )
    assert resp.status_code == 200
    outbox = get_mailer().outbox
    assert outbox and outbox[-1].to == "bob@example.com"
    # Extract the token from the verification link and confirm.
    token = outbox[-1].text.split("verify-email?token=")[1].split()[0].strip()
    confirm = client.post("/api/v1/auth/email-verification/confirm", json={"token": token})
    assert confirm.status_code == 200
    assert confirm.json()["email_verified"] is True


def test_password_reset_request_for_unknown_user_sends_nothing(client):
    register(client, "carol", "secret123")
    before = len(get_mailer().outbox)
    resp = client.post("/api/v1/auth/password-reset/request", json={"username": "ghost"})
    assert resp.status_code == 200  # generic OK (anti-enumeration)
    assert len(get_mailer().outbox) == before
