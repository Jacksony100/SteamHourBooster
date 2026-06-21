from sqlalchemy.orm import Session

from app.billing.service import sync_default_plans
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.models import Plan, Subscription, User
from app.core.security import hash_password


def seed(db: Session) -> None:
    settings = get_settings()
    sync_default_plans(db)
    lifetime = db.query(Plan).filter(Plan.code == "lifetime").one()
    admin = db.query(User).filter(User.username == settings.admin_username).one_or_none()
    if not admin:
        admin = User(
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
            is_admin=True,
        )
        db.add(admin)
        db.flush()
        db.add(
            Subscription(
                user_id=admin.id,
                plan_id=lifetime.id,
                plan_code=lifetime.code,
                status="active",
                manual_override=True,
            )
        )
    db.commit()


if __name__ == "__main__":
    session = SessionLocal()
    try:
        seed(session)
    finally:
        session.close()
