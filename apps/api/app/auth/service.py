from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from typing import Any

from fastapi import HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.audit.service import write_audit
from app.core.mailer import send_email_verification_email, send_password_reset_email
from app.core.models import (
    AccountGame,
    PasswordResetToken,
    Payment,
    SteamAccount,
    SteamSession,
    Subscription,
    User,
    UserSession,
)
from app.core.security import hash_password, hash_token, new_session_id

PASSWORD_RESET_TTL_MINUTES = 30
EMAIL_VERIFICATION_TTL_HOURS = 24


def now_utc() -> datetime:
    return datetime.now(UTC)


def as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def normalize_user_agent(value: str | None) -> str | None:
    if not value:
        return None
    return value[:255]


def request_ip_hash(request: Request | None) -> str | None:
    if not request or not request.client:
        return None
    return hash_token(request.client.host)


def request_user_agent(request: Request | None) -> str | None:
    return normalize_user_agent(request.headers.get("user-agent") if request else None)


def public_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "email_verified": bool(user.email_verified_at),
        "is_admin": user.is_admin,
        "banned": user.banned,
    }


def _unique_username(db: Session, base: str) -> str:
    candidate = base[:60] or "steam_user"
    n = 1
    while db.query(User).filter(User.username == candidate).one_or_none() is not None:
        n += 1
        suffix = f"_{n}"
        candidate = (base[: 60 - len(suffix)] or "steam_user") + suffix
    return candidate


def get_or_create_steam_user(db: Session, steam_id: str, request: Request | None = None, persona: str | None = None) -> User:
    """Find the user linked to this SteamID64, or create a Steam-only account."""
    user = db.query(User).filter(User.steam_id == steam_id).one_or_none()
    if user is None:
        cleaned = "".join(ch for ch in (persona or "") if ch.isprintable()).strip()
        user = User(
            username=_unique_username(db, cleaned or f"steam_{steam_id}"),
            steam_id=steam_id,
            password_hash=hash_password(token_urlsafe(32)),  # Steam-only: no usable password
        )
        db.add(user)
        db.flush()
    user.last_seen_at = now_utc()
    if request is not None and request.client:
        user.last_ip = request.client.host
    db.commit()
    db.refresh(user)
    return user


def create_web_session(db: Session, user: User, request: Request | None = None) -> str:
    session_id = new_session_id()
    entry = UserSession(
        user_id=user.id,
        session_id_hash=hash_token(session_id),
        ip_hash=request_ip_hash(request),
        user_agent=request_user_agent(request),
        last_seen_at=now_utc(),
    )
    db.add(entry)
    db.commit()
    return session_id


def touch_web_session(db: Session, session: UserSession) -> None:
    session.last_seen_at = now_utc()
    db.commit()


def revoke_session_hash(db: Session, user: User, session_id_hash: str) -> None:
    entry = (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id, UserSession.session_id_hash == session_id_hash, UserSession.revoked_at.is_(None))
        .one_or_none()
    )
    if entry:
        entry.revoked_at = now_utc()
        db.commit()


def revoke_session_by_id(db: Session, user: User, session_id: int) -> None:
    entry = (
        db.query(UserSession)
        .filter(UserSession.id == session_id, UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
        .one_or_none()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    entry.revoked_at = now_utc()
    db.commit()
    write_audit(db, "auth.session_revoked", "user_session", entry.id, user)


def revoke_all_user_sessions(db: Session, user: User) -> int:
    sessions = db.query(UserSession).filter(UserSession.user_id == user.id, UserSession.revoked_at.is_(None)).all()
    now = now_utc()
    for entry in sessions:
        entry.revoked_at = now
    db.commit()
    return len(sessions)


def active_user_sessions(db: Session, user: User) -> list[UserSession]:
    return db.query(UserSession).filter(UserSession.user_id == user.id, UserSession.revoked_at.is_(None)).order_by(UserSession.id.desc()).all()


def issue_password_reset_token(db: Session, user: User, request: Request | None = None) -> str:
    raw_token = token_urlsafe(48)
    entry = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=now_utc() + timedelta(minutes=PASSWORD_RESET_TTL_MINUTES),
        request_ip_hash=request_ip_hash(request),
        user_agent=request_user_agent(request),
    )
    db.add(entry)
    db.commit()
    return raw_token


def request_password_reset(db: Session, identifier: str, request: Request | None = None) -> None:
    normalized = identifier.strip().lower()
    user = db.query(User).filter(or_(User.username == identifier, User.email == normalized)).one_or_none()
    if user and not user.banned:
        raw_token = issue_password_reset_token(db, user, request)
        if user.email:
            send_password_reset_email(user.email, raw_token)
        write_audit(db, "auth.password_reset_requested", "user", user.id, None)


def consume_password_reset_token(db: Session, token: str, new_password: str) -> User:
    entry = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == hash_token(token)).one_or_none()
    if not entry or entry.used_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    expires_at = as_aware(entry.expires_at)
    if expires_at and expires_at < now_utc():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
    user = db.get(User, entry.user_id)
    if not user or user.banned:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    entry.used_at = now_utc()
    user.password_hash = hash_password(new_password)
    db.commit()
    revoke_all_user_sessions(db, user)
    write_audit(db, "auth.password_reset_completed", "user", user.id, None)
    db.refresh(user)
    return user


def issue_email_verification_token(db: Session, user: User, email: str | None = None) -> str:
    if email:
        existing = db.query(User).filter(User.email == email, User.id != user.id).one_or_none()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
        if user.email != email:
            user.email = email
            user.email_verified_at = None
    if not user.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required")
    raw_token = token_urlsafe(48)
    user.email_verification_token_hash = hash_token(raw_token)
    user.email_verification_sent_at = now_utc()
    db.commit()
    send_email_verification_email(user.email, raw_token)
    write_audit(db, "auth.email_verification_requested", "user", user.id, user)
    return raw_token


def confirm_email_verification(db: Session, token: str) -> User:
    user = db.query(User).filter(User.email_verification_token_hash == hash_token(token)).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")
    sent_at = as_aware(user.email_verification_sent_at)
    if sent_at and sent_at + timedelta(hours=EMAIL_VERIFICATION_TTL_HOURS) < now_utc():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")
    user.email_verified_at = now_utc()
    user.email_verification_token_hash = None
    db.commit()
    write_audit(db, "auth.email_verified", "user", user.id, user)
    db.refresh(user)
    return user


def user_data_export(db: Session, user: User) -> dict[str, Any]:
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).one_or_none()
    accounts = db.query(SteamAccount).filter(SteamAccount.user_id == user.id).order_by(SteamAccount.id.asc()).all()
    sessions = db.query(SteamSession).filter(SteamSession.user_id == user.id).order_by(SteamSession.id.desc()).limit(100).all()
    payments = db.query(Payment).filter(Payment.user_id == user.id).order_by(Payment.id.desc()).limit(100).all()

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "email_verified": bool(user.email_verified_at),
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "subscription": {
            "status": subscription.status,
            "plan_code": subscription.plan_code,
            "expires_at": subscription.expires_at.isoformat() if subscription and subscription.expires_at else None,
        }
        if subscription
        else None,
        "accounts": [
            {
                "id": account.id,
                "label": account.label,
                "steamid64": account.steamid64,
                "status": account.status,
                "selected_games_count": db.query(AccountGame).filter(AccountGame.account_id == account.id).count(),
                "created_at": account.created_at.isoformat() if account.created_at else None,
            }
            for account in accounts
        ],
        "sessions": [
            {
                "id": session.id,
                "account_id": session.account_id,
                "status": session.status,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "stopped_at": session.stopped_at.isoformat() if session.stopped_at else None,
            }
            for session in sessions
        ],
        "payments": [
            {
                "id": payment.id,
                "provider": payment.provider,
                "status": payment.status,
                "amount_cents": payment.amount_cents,
                "currency": payment.currency,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
            }
            for payment in payments
        ],
    }


def delete_user_account(db: Session, user: User) -> None:
    user_id = user.id
    write_audit(db, "auth.account_deleted", "user", user_id, user)
    db.delete(user)
    db.commit()
