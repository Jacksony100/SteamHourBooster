import hmac
from hashlib import sha256

import pytest
from cryptography.fernet import Fernet

from steam_hour_booster import create_app
from steam_hour_booster.auth.service import verify_user
from steam_hour_booster.db import get_db
from steam_hour_booster.security.logging import REDACTED, redact_mapping
from steam_hour_booster.security.password_service import is_password_hash


def test_app_requires_env_secret_key_outside_tests(tmp_path):
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(
            SECRET_KEY=None,
            ENCRYPTION_KEY=Fernet.generate_key().decode("utf-8"),
            DATABASE_URL=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
            TESTING=False,
        )


def test_app_requires_env_encryption_key_outside_tests(tmp_path):
    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
        create_app(
            SECRET_KEY="x" * 40,
            ENCRYPTION_KEY=None,
            DATABASE_URL=f"sqlite:///{(tmp_path / 'app.db').as_posix()}",
            TESTING=False,
        )


def test_csrf_rejects_missing_token(tmp_path):
    app = create_app(
        SECRET_KEY="x" * 40,
        ENCRYPTION_KEY=Fernet.generate_key().decode("utf-8"),
        DATABASE_URL=f"sqlite:///{(tmp_path / 'csrf.db').as_posix()}",
        TESTING=True,
        CSRF_ENABLED=True,
        RATE_LIMIT_ENABLED=False,
    )
    client = app.test_client()

    response = client.post("/register", data={"username": "csrf-user", "password": "secret-pass"})

    assert response.status_code == 400


def test_csrf_accepts_valid_token(tmp_path):
    app = create_app(
        SECRET_KEY="x" * 40,
        ENCRYPTION_KEY=Fernet.generate_key().decode("utf-8"),
        DATABASE_URL=f"sqlite:///{(tmp_path / 'csrf-ok.db').as_posix()}",
        TESTING=True,
        CSRF_ENABLED=True,
        RATE_LIMIT_ENABLED=False,
    )
    client = app.test_client()

    with client.session_transaction() as session:
        session["_csrf_token"] = "known-token"

    response = client.post(
        "/register",
        data={"username": "csrf-ok", "password": "secret-pass", "csrf_token": "known-token"},
        follow_redirects=False,
    )

    assert response.status_code == 302


def test_session_cookie_security_flags(tmp_path):
    app = create_app(
        SECRET_KEY="x" * 40,
        ENCRYPTION_KEY=Fernet.generate_key().decode("utf-8"),
        DATABASE_URL=f"sqlite:///{(tmp_path / 'cookie.db').as_posix()}",
        TESTING=True,
        CSRF_ENABLED=False,
        RATE_LIMIT_ENABLED=False,
        SESSION_COOKIE_SECURE=True,
    )
    client = app.test_client()
    client.post("/register", data={"username": "cookie-user", "password": "secret-pass"})

    response = client.post("/login", data={"username": "cookie-user", "password": "secret-pass"})
    cookie = response.headers["Set-Cookie"]

    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Secure" in cookie


def test_legacy_fernet_password_is_migrated_to_hash(app):
    with app.app_context():
        encrypted_password = app.extensions["encryption_service"].encrypt("legacy-pass")
        db = get_db()
        db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("legacy-user", encrypted_password),
        )
        db.commit()

        assert verify_user("legacy-user", "legacy-pass") is not None
        migrated = db.execute("SELECT password FROM users WHERE username=?", ("legacy-user",)).fetchone()
        assert is_password_hash(migrated["password"])


def test_redaction_helper_masks_sensitive_values():
    payload = {
        "username": "visible",
        "password": "secret",
        "nested": {"shared_secret": "secret"},
        "items": [{"steam_guard_code": "12345"}],
    }

    redacted = redact_mapping(payload)

    assert redacted["username"] == "visible"
    assert redacted["password"] == REDACTED
    assert redacted["nested"]["shared_secret"] == REDACTED
    assert redacted["items"][0]["steam_guard_code"] == REDACTED


def test_coinbase_webhook_requires_valid_signature(tmp_path):
    secret = "webhook-secret"
    app = create_app(
        SECRET_KEY="x" * 40,
        ENCRYPTION_KEY=Fernet.generate_key().decode("utf-8"),
        DATABASE_URL=f"sqlite:///{(tmp_path / 'webhook.db').as_posix()}",
        TESTING=True,
        CSRF_ENABLED=True,
        RATE_LIMIT_ENABLED=False,
        COINBASE_WEBHOOK_SECRET=secret,
    )
    client = app.test_client()
    body = b'{"event":{"type":"charge:confirmed"}}'
    signature = hmac.new(secret.encode("utf-8"), body, sha256).hexdigest()

    invalid = client.post("/coinbase/webhook", data=body, headers={"X-CC-Webhook-Signature": "bad"})
    valid = client.post("/coinbase/webhook", data=body, headers={"X-CC-Webhook-Signature": signature})

    assert invalid.status_code == 400
    assert valid.status_code == 200
    assert valid.get_json()["received"] is True
