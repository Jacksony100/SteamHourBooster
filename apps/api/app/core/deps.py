from app.auth.service import touch_web_session
from app.billing.service import require_active_entitlement
from app.core.config import get_settings
from app.core.database import get_db
from app.core.models import User, UserSession
from app.core.security import decode_session_payload, hash_token
from fastapi import Cookie, Depends, Header, HTTPException, Request, Response, status
from sqlalchemy.orm import Session


def current_user(
    request: Request,
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=get_settings().session_cookie_name),
    legacy_session_token: str | None = Cookie(default=None, alias="shb_session"),
) -> User:
    payload = decode_session_payload(session_token or legacy_session_token or "")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required") from None
    session_id = payload.get("sid")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    session_id_hash = hash_token(str(session_id))
    web_session = (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.session_id_hash == session_id_hash, UserSession.revoked_at.is_(None))
        .one_or_none()
    )
    if not web_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user = db.get(User, user_id)
    if not user or user.banned:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    request.state.user = user
    request.state.session_id_hash = session_id_hash
    touch_web_session(db, web_session)
    return user


def require_csrf(
    csrf_cookie: str | None = Cookie(default=None, alias=get_settings().csrf_cookie_name),
    legacy_csrf_cookie: str | None = Cookie(default=None, alias="shb_csrf"),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> None:
    cookie_value = csrf_cookie or legacy_csrf_cookie
    if not cookie_value or cookie_value != csrf_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")


def admin_user(user: User = Depends(current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def active_subscription(user: User = Depends(current_user), db: Session = Depends(get_db)) -> User:
    require_active_entitlement(db, user)
    return user


def set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        session_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        max_age=settings.session_ttl_minutes * 60,
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        max_age=settings.session_ttl_minutes * 60,
    )


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        settings.session_cookie_name,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )
    response.delete_cookie(
        settings.csrf_cookie_name,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )
    response.delete_cookie(
        "shb_session",
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )
    response.delete_cookie(
        "shb_csrf",
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
    )
