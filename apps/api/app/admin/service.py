import json
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.admin.schemas import (
    AdminAccountSummary,
    AdminAuditResponse,
    AdminForceLogoutResponse,
    AdminOverviewResponse,
    AdminPaymentResponse,
    AdminSessionSummary,
    AdminSubscriptionUpdate,
    AdminUserDetailResponse,
    AdminUserFilter,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdate,
)
from app.audit.service import write_audit
from app.billing.service import admin_update_subscription, get_plan
from app.core.models import (
    AuditLog,
    Payment,
    SessionStatus,
    SteamAccount,
    SteamSession,
    Subscription,
    User,
)
from app.sessions.adapters import get_steam_client_adapter
from app.sessions.manager import parse_selected_games, write_session_event

ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing"}
ACTIVE_SESSION_STATUSES = {SessionStatus.starting.value, SessionStatus.running.value, SessionStatus.stopping.value}


def now_utc() -> datetime:
    return datetime.now(UTC)


def json_dict(value: str | None) -> dict[str, Any]:
    try:
        payload = json.loads(value or "{}")
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def is_subscription_expired(subscription: Subscription | None) -> bool:
    if not subscription:
        return False
    expires_at = subscription.expires_at or subscription.ends_at
    if subscription.status == "expired":
        return True
    return bool(expires_at and expires_at < now_utc())


def serialize_user(db: Session, user: User) -> AdminUserResponse:
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).one_or_none()
    plan = subscription.plan if subscription else None
    accounts_count = db.query(SteamAccount).filter(SteamAccount.user_id == user.id).count()
    active_sessions_count = db.query(SteamSession).filter(SteamSession.user_id == user.id, SteamSession.status.in_(list(ACTIVE_SESSION_STATUSES))).count()
    payments_total = db.query(func.coalesce(func.sum(Payment.amount_cents), 0)).filter(Payment.user_id == user.id, Payment.status == "paid").scalar() or 0
    return AdminUserResponse(
        id=user.id,
        username=user.username,
        is_admin=user.is_admin,
        banned=user.banned,
        subscription_status=subscription.status if subscription else None,
        subscription_plan=subscription.plan_code if subscription else None,
        subscription_expires_at=(subscription.expires_at or subscription.ends_at) if subscription else None,
        account_limit=plan.account_limit if plan else None,
        active_session_limit=plan.active_session_limit if plan else None,
        accounts_count=accounts_count,
        active_sessions_count=active_sessions_count,
        payments_total_cents=int(payments_total),
        created_at=user.created_at,
        last_seen_at=user.last_seen_at,
        last_ip=user.last_ip,
    )


def admin_overview(db: Session) -> AdminOverviewResponse:
    total_users = db.query(User).count()
    banned_users = db.query(User).filter(User.banned.is_(True)).count()
    active_subscriptions = db.query(Subscription).filter(Subscription.status.in_(list(ACTIVE_SUBSCRIPTION_STATUSES))).count()
    expired_subscriptions = db.query(Subscription).filter(Subscription.status == "expired").count()
    active_sessions = db.query(SteamSession).filter(SteamSession.status.in_(list(ACTIVE_SESSION_STATUSES))).count()
    failed_logins = db.query(AuditLog).filter(AuditLog.action == "auth.login_failed").count()
    payments_total_cents = db.query(func.coalesce(func.sum(Payment.amount_cents), 0)).filter(Payment.status == "paid").scalar() or 0
    return AdminOverviewResponse(
        total_users=total_users,
        active_subscriptions=active_subscriptions,
        expired_subscriptions=expired_subscriptions,
        banned_users=banned_users,
        active_sessions=active_sessions,
        failed_logins=failed_logins,
        payments_total_cents=int(payments_total_cents),
    )


def list_admin_users(
    db: Session,
    *,
    query: str = "",
    user_filter: AdminUserFilter = "all",
    page: int = 1,
    page_size: int = 25,
) -> AdminUserListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    q = db.query(User).outerjoin(Subscription, Subscription.user_id == User.id)
    if query:
        q = q.filter(User.username.ilike(f"%{query}%"))
    if user_filter == "active":
        q = q.filter(User.banned.is_(False))
    elif user_filter == "banned":
        q = q.filter(User.banned.is_(True))
    elif user_filter == "admin":
        q = q.filter(User.is_admin.is_(True))
    elif user_filter == "subscribed":
        q = q.filter(Subscription.status.in_(list(ACTIVE_SUBSCRIPTION_STATUSES)))
    elif user_filter == "expired":
        q = q.filter(or_(Subscription.status == "expired", Subscription.expires_at < now_utc(), Subscription.ends_at < now_utc()))

    total = q.count()
    rows = q.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return AdminUserListResponse(items=[serialize_user(db, user) for user in rows], total=total, page=page, page_size=page_size)


def serialize_account(account: SteamAccount) -> AdminAccountSummary:
    return AdminAccountSummary(
        id=account.id,
        label=account.label,
        steamid64=account.steamid64,
        status=account.status,
        selected_games_count=len(account.selected_games or []),
        created_at=account.created_at,
        last_login_at=account.last_login_at,
    )


def serialize_session(session: SteamSession) -> AdminSessionSummary:
    return AdminSessionSummary(
        id=session.id,
        account_id=session.account_id,
        status=session.status,
        selected_games=parse_selected_games(session),
        started_at=session.started_at,
        stopped_at=session.stopped_at,
        last_heartbeat_at=session.last_heartbeat_at,
        error_message=session.error_message,
    )


def serialize_payment(payment: Payment) -> AdminPaymentResponse:
    return AdminPaymentResponse(
        id=payment.id,
        user_id=payment.user_id,
        username=payment.user.username if payment.user else None,
        plan_code=payment.plan.code if payment.plan else "unknown",
        provider=payment.provider,
        status=payment.status,
        amount_cents=payment.amount_cents,
        currency=payment.currency,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


def actor_names(db: Session, actor_ids: set[int]) -> dict[int, str]:
    if not actor_ids:
        return {}
    return {user.id: user.username for user in db.query(User).filter(User.id.in_(actor_ids)).all()}


def serialize_audit(row: AuditLog, names: dict[int, str] | None = None) -> AdminAuditResponse:
    names = names or {}
    return AdminAuditResponse(
        id=row.id,
        actor_user_id=row.actor_user_id,
        actor_username=names.get(row.actor_user_id) if row.actor_user_id else None,
        action=row.action,
        target_type=row.target_type,
        target_id=row.target_id,
        metadata=json_dict(row.metadata_json),
        created_at=row.created_at,
    )


def user_detail(db: Session, user_id: int) -> AdminUserDetailResponse:
    user = get_user_or_404(db, user_id)
    accounts = db.query(SteamAccount).filter(SteamAccount.user_id == user.id).order_by(SteamAccount.id.desc()).all()
    sessions = db.query(SteamSession).filter(SteamSession.user_id == user.id).order_by(SteamSession.id.desc()).limit(20).all()
    payments = db.query(Payment).filter(Payment.user_id == user.id).order_by(Payment.id.desc()).limit(20).all()
    audit_rows = (
        db.query(AuditLog).filter(or_(AuditLog.actor_user_id == user.id, AuditLog.target_id == str(user.id))).order_by(AuditLog.id.desc()).limit(50).all()
    )
    names = actor_names(db, {row.actor_user_id for row in audit_rows if row.actor_user_id})
    return AdminUserDetailResponse(
        user=serialize_user(db, user),
        accounts=[serialize_account(account) for account in accounts],
        sessions=[serialize_session(session) for session in sessions],
        payments=[serialize_payment(payment) for payment in payments],
        audit_events=[serialize_audit(row, names) for row in audit_rows],
    )


def update_user(db: Session, *, actor: User, user_id: int, payload: AdminUserUpdate) -> AdminUserResponse:
    user = get_user_or_404(db, user_id)
    metadata = payload.model_dump(exclude_none=True)

    if payload.is_admin is not None:
        if user.id == actor.id and user.is_admin and payload.is_admin is False and not payload.confirm_self_admin_revoke:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Self admin revoke requires explicit confirmation")
        user.is_admin = payload.is_admin
    if payload.banned is not None:
        user.banned = payload.banned

    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).one_or_none()
    if not subscription:
        plan = get_plan(db, "trial")
        subscription = Subscription(user_id=user.id, status="trialing", plan_code=plan.code, plan_id=plan.id)
        db.add(subscription)
    if payload.subscription_status:
        subscription.status = payload.subscription_status
        subscription.manual_override = True
    if payload.plan_code:
        plan = get_plan(db, payload.plan_code)
        subscription.plan_code = plan.code
        subscription.plan_id = plan.id
        subscription.manual_override = True

    db.commit()
    db.refresh(user)
    write_audit(db, "admin.user_update", "user", user.id, actor, metadata)
    return serialize_user(db, user)


def update_subscription(db: Session, *, actor: User, user_id: int, payload: AdminSubscriptionUpdate) -> Subscription:
    user = get_user_or_404(db, user_id)
    return admin_update_subscription(
        db,
        actor,
        user,
        plan_code=payload.plan_code,
        status_value=payload.status,
        extend_days=payload.extend_days,
        expires_at=payload.expires_at,
        reason=payload.reason,
    )


def force_logout_sessions(db: Session, *, actor: User, user_id: int, reason: str | None = None) -> AdminForceLogoutResponse:
    user = get_user_or_404(db, user_id)
    sessions = db.query(SteamSession).filter(SteamSession.user_id == user.id, SteamSession.status.in_(list(ACTIVE_SESSION_STATUSES))).all()
    stopped = 0
    failed = 0
    now = now_utc()
    adapter = get_steam_client_adapter()
    for session in sessions:
        result = adapter.stop_session(session.account, parse_selected_games(session))
        session.updated_at = now
        if result.ok:
            session.status = SessionStatus.stopped.value
            session.stopped_at = session.stopped_at or now
            write_session_event(
                db,
                event_type="session_stopped",
                user_id=user.id,
                account_id=session.account_id,
                session_id=session.id,
                message="Session force-stopped by admin",
                metadata={"actor_user_id": actor.id, "reason": reason},
            )
            stopped += 1
        else:
            session.status = SessionStatus.error.value
            session.error_message = result.error or "Admin force-stop failed to stop session runtime"
            session.stopped_at = session.stopped_at or now
            write_session_event(
                db,
                event_type="session_error",
                user_id=user.id,
                account_id=session.account_id,
                session_id=session.id,
                message=session.error_message,
                metadata={"actor_user_id": actor.id, "reason": reason},
            )
            failed += 1
    db.commit()
    write_audit(db, "admin.force_logout_sessions", "user", user.id, actor, {"stopped_sessions": stopped, "failed_sessions": failed, "reason": reason})
    return AdminForceLogoutResponse(stopped_sessions=stopped)


def list_audit(db: Session, *, query: str = "", page: int = 1, page_size: int = 50) -> list[AdminAuditResponse]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    q = db.query(AuditLog)
    if query:
        pattern = f"%{query}%"
        q = q.filter(or_(AuditLog.action.ilike(pattern), AuditLog.target_type.ilike(pattern), AuditLog.target_id.ilike(pattern)))
    rows = q.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    names = actor_names(db, {row.actor_user_id for row in rows if row.actor_user_id})
    return [serialize_audit(row, names) for row in rows]


def list_payments(db: Session, *, page: int = 1, page_size: int = 50) -> list[AdminPaymentResponse]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    rows = db.query(Payment).order_by(Payment.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [serialize_payment(payment) for payment in rows]


def list_subscription_changes(db: Session, *, page: int = 1, page_size: int = 50) -> list[AdminAuditResponse]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.action.in_(["admin.subscription_update", "billing.subscription_activated", "admin.user_update"]))
        .order_by(AuditLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    names = actor_names(db, {row.actor_user_id for row in rows if row.actor_user_id})
    return [serialize_audit(row, names) for row in rows]
