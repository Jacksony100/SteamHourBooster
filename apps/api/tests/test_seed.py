from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.models import Subscription, User
from app.seed import seed


def test_seed_creates_admin_only_by_default(client):
    db = SessionLocal()
    try:
        seed(db)
        admin = db.query(User).filter(User.username == "admin").one()
        assert admin.is_admin is True
        assert db.query(User).filter(User.username == "demo").one_or_none() is None
    finally:
        db.close()


def test_seed_creates_demo_user_when_enabled(client, monkeypatch):
    settings = get_settings().model_copy(update={"seed_demo_user": True})
    monkeypatch.setattr("app.seed.get_settings", lambda: settings)
    db = SessionLocal()
    try:
        seed(db)
        demo = db.query(User).filter(User.username == "demo").one()
        sub = db.query(Subscription).filter(Subscription.user_id == demo.id).one()
        assert sub.status == "active"
        assert sub.plan_code == "pro"
        assert demo.is_admin is False
    finally:
        db.close()
