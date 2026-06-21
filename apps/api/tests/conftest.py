import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough")
os.environ.setdefault("ENCRYPTION_KEY", "0J4FyJwHnYmeFz7r5Zk8F0KJxl-2mFY9hqqIetQxZj0=")
os.environ.setdefault("STEAM_TEST_MODE", "true")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "admin-password")

import pytest
from app.billing.service import sync_default_plans
from app.core.database import Base, engine
from app.core.models import Plan, Subscription, User
from app.core.rate_limit import reset_rate_limits
from app.core.security import hash_password
from app.main import app
from app.sessions.adapters import set_steam_client_adapter
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_db():
    reset_rate_limits()
    set_steam_client_adapter(None)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    set_steam_client_adapter(None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def register(client: TestClient, username: str = "alice", password: str = "secret123"):
    return client.post("/api/v1/auth/register", json={"username": username, "password": password, "accepted_terms": True})


def login(client: TestClient, username: str = "alice", password: str = "secret123"):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


def csrf(client: TestClient) -> str:
    return client.cookies.get("deckpilot_csrf")


def make_admin_user():
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        sync_default_plans(db)
        plan = db.query(Plan).filter(Plan.code == "lifetime").one()
        admin = User(username="admin", password_hash=hash_password("admin-password"), is_admin=True)
        db.add(admin)
        db.flush()
        db.add(Subscription(user_id=admin.id, plan_id=plan.id, plan_code=plan.code, status="active", manual_override=True))
        db.commit()
    finally:
        db.close()


def activate_subscription(username: str = "alice", plan_code: str = "pro"):
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        sync_default_plans(db)
        user = db.query(User).filter(User.username == username).one()
        sub = db.query(Subscription).filter(Subscription.user_id == user.id).one()
        plan = db.query(Plan).filter(Plan.code == plan_code).one()
        sub.status = "active"
        sub.plan_id = plan.id
        sub.plan_code = plan.code
        sub.expires_at = None
        sub.ends_at = None
        db.commit()
    finally:
        db.close()
