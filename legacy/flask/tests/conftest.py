from datetime import datetime, timedelta

import pytest
from cryptography.fernet import Fernet

from steam_hour_booster import create_app
from steam_hour_booster.db import get_db


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    app = create_app(
        SECRET_KEY="test-secret",
        DATABASE_URL=f"sqlite:///{db_path.as_posix()}",
        ENCRYPTION_KEY=Fernet.generate_key().decode("utf-8"),
        TESTING=True,
        RATE_LIMIT_ENABLED=False,
        CSRF_ENABLED=False,
    )
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, username="alice", password="secret-pass"):
    return client.post(
        "/register",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def login(client, username="alice", password="secret-pass"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def give_subscription(app, username="alice"):
    subscription_end = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    with app.app_context():
        db = get_db()
        db.execute(
            "UPDATE users SET subscription_end=? WHERE username=?",
            (subscription_end, username),
        )
        db.commit()


def make_admin(app, username="alice"):
    with app.app_context():
        db = get_db()
        db.execute("UPDATE users SET is_admin=1 WHERE username=?", (username,))
        db.commit()
