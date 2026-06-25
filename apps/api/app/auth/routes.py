from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.audit.service import write_audit
from app.auth import steam_openid
from app.auth.schemas import (
    AuthResponse,
    EmailVerificationConfirmRequest,
    EmailVerificationRequest,
    GenericOkResponse,
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RegisterRequest,
    UserResponse,
    UserSessionResponse,
)
from app.auth.service import (
    active_user_sessions,
    confirm_email_verification,
    consume_password_reset_token,
    create_web_session,
    delete_user_account,
    get_or_create_steam_user,
    issue_email_verification_token,
    public_user,
    request_password_reset,
    revoke_session_by_id,
    revoke_session_hash,
    user_data_export,
)
from app.billing.service import ensure_trial_subscription
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import clear_auth_cookies, current_user, require_csrf, set_auth_cookies
from app.core.models import User
from app.core.rate_limit import rate_limit
from app.core.security import create_session_token, hash_password, new_csrf_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_response(user: User) -> UserResponse:
    return UserResponse(**public_user(user))


def _auth_response(response: Response, user: User, db: Session, request: Request) -> AuthResponse:
    csrf_token = new_csrf_token()
    session_id = create_web_session(db, user, request)
    set_auth_cookies(response, create_session_token(user.id, session_id), csrf_token)
    return AuthResponse(
        user=_user_response(user),
        csrf_token=csrf_token,
    )


@router.post("/register", response_model=AuthResponse, dependencies=[Depends(rate_limit("register", 8, 60))])
def register(payload: RegisterRequest, response: Response, request: Request, db: Session = Depends(get_db)) -> AuthResponse:
    if not payload.accepted_terms:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Terms must be accepted")
    existing = db.query(User).filter(User.username == payload.username).one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    if payload.email:
        existing_email = db.query(User).filter(User.email == payload.email).one_or_none()
        if existing_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    user = User(username=payload.username, email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    ensure_trial_subscription(db, user)
    db.refresh(user)
    write_audit(db, "auth.register", "user", user.id, user)
    return _auth_response(response, user, db, request)


@router.post("/login", response_model=AuthResponse, dependencies=[Depends(rate_limit("login", 20, 60))])
def login(payload: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.username == payload.username).one_or_none()
    if not user or not verify_password(payload.password, user.password_hash) or user.banned:
        write_audit(
            db,
            "auth.login_failed",
            "user",
            user.id if user else payload.username,
            None,
            {"username": payload.username, "ip": request.client.host if request.client else None},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user.last_seen_at = datetime.now(UTC)
    user.last_ip = request.client.host if request.client else None
    db.commit()
    db.refresh(user)
    write_audit(db, "auth.login", "user", user.id, user)
    return _auth_response(response, user, db, request)


@router.get("/steam/login", dependencies=[Depends(rate_limit("steam_login", 30, 60))])
def steam_login_redirect():
    if not get_settings().steam_login_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Steam login disabled")
    return RedirectResponse(steam_openid.build_login_url(), status_code=302)


@router.get("/steam/callback")
def steam_callback(request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    web = settings.web_base_url.rstrip("/")
    if not settings.steam_login_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Steam login disabled")

    steam_id = steam_openid.verify_steam_response(dict(request.query_params))
    if not steam_id:
        return RedirectResponse(f"{web}/login?error=steam", status_code=302)

    user = get_or_create_steam_user(db, steam_id, request, persona=steam_openid.fetch_persona(steam_id))
    if user.banned:
        return RedirectResponse(f"{web}/login?error=banned", status_code=302)
    ensure_trial_subscription(db, user)

    redirect = RedirectResponse(f"{web}/dashboard", status_code=302)
    csrf_token = new_csrf_token()
    session_id = create_web_session(db, user, request)
    set_auth_cookies(redirect, create_session_token(user.id, session_id), csrf_token)
    write_audit(db, "auth.steam_login", "user", user.id, user)
    return redirect


@router.post("/logout", dependencies=[Depends(require_csrf)])
def logout(request: Request, response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    session_id_hash = getattr(request.state, "session_id_hash", None)
    if session_id_hash:
        revoke_session_hash(db, user, session_id_hash)
    clear_auth_cookies(response)
    write_audit(db, "auth.logout", "user", user.id, user)
    return {"ok": True}


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(current_user)) -> UserResponse:
    return _user_response(user)


@router.get("/csrf")
def csrf() -> dict:
    return {"csrf_required": True, "header": "X-CSRF-Token"}


@router.post(
    "/password-reset/request",
    response_model=GenericOkResponse,
    dependencies=[Depends(rate_limit("password_reset_request", 5, 60 * 60))],
)
def password_reset_request(payload: PasswordResetRequest, request: Request, db: Session = Depends(get_db)) -> GenericOkResponse:
    request_password_reset(db, payload.username, request)
    return GenericOkResponse()


@router.post(
    "/password-reset/confirm",
    response_model=GenericOkResponse,
    dependencies=[Depends(rate_limit("password_reset_confirm", 10, 60 * 60))],
)
def password_reset_confirm(payload: PasswordResetConfirmRequest, db: Session = Depends(get_db)) -> GenericOkResponse:
    consume_password_reset_token(db, payload.token, payload.password)
    return GenericOkResponse()


@router.post("/email-verification/request", response_model=GenericOkResponse, dependencies=[Depends(require_csrf)])
def email_verification_request(
    payload: EmailVerificationRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> GenericOkResponse:
    issue_email_verification_token(db, user, payload.email)
    return GenericOkResponse()


@router.post("/email-verification/confirm", response_model=UserResponse)
def email_verification_confirm(payload: EmailVerificationConfirmRequest, db: Session = Depends(get_db)) -> UserResponse:
    user = confirm_email_verification(db, payload.token)
    return _user_response(user)


@router.get("/sessions", response_model=list[UserSessionResponse])
def sessions(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[UserSessionResponse]:
    current_hash = getattr(request.state, "session_id_hash", None)
    return [
        UserSessionResponse(
            id=session.id,
            created_at=session.created_at,
            last_seen_at=session.last_seen_at,
            revoked_at=session.revoked_at,
            current=session.session_id_hash == current_hash,
            user_agent=session.user_agent,
        )
        for session in active_user_sessions(db, user)
    ]


@router.delete("/sessions/{session_id}", response_model=GenericOkResponse, dependencies=[Depends(require_csrf)])
def revoke_session(session_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)) -> GenericOkResponse:
    revoke_session_by_id(db, user, session_id)
    return GenericOkResponse()


@router.get("/export")
def export_data(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return user_data_export(db, user)


@router.delete("/account", response_model=GenericOkResponse, dependencies=[Depends(require_csrf)])
def delete_account(response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)) -> GenericOkResponse:
    delete_user_account(db, user)
    clear_auth_cookies(response)
    return GenericOkResponse()
