from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.billing.service import entitlement
from app.core.database import get_db
from app.core.deps import current_user
from app.core.models import AccountGame, AuditLog, SessionStatus, SteamAccount, SteamSession, User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def overview(user: User = Depends(current_user), db: Session = Depends(get_db)):
    accounts_count = db.query(SteamAccount).filter(SteamAccount.user_id == user.id).count()
    online_sessions = db.query(SteamSession).filter(SteamSession.user_id == user.id, SteamSession.status == SessionStatus.running.value).count()
    active_games = db.query(AccountGame).join(SteamAccount, SteamAccount.id == AccountGame.account_id).filter(SteamAccount.user_id == user.id).count()
    subscription = entitlement(db, user)
    plan = subscription["plan"]
    recent_activity = db.query(AuditLog).filter(AuditLog.actor_user_id == user.id).order_by(AuditLog.id.desc()).limit(8).all()
    return {
        "accounts_count": accounts_count,
        "online_sessions": online_sessions,
        "active_games": active_games,
        "subscription_status": subscription["status"],
        "subscription_plan": plan.code if plan else "free",
        "subscription_expires_at": subscription["expires_at"],
        "account_limit": subscription["account_limit"],
        "active_session_limit": subscription["active_session_limit"],
        "recent_activity": [
            {"action": item.action, "target_type": item.target_type, "target_id": item.target_id, "created_at": item.created_at} for item in recent_activity
        ],
    }
