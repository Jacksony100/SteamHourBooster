import json
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.audit.service import write_audit
from app.billing.service import assert_account_limit
from app.core.config import get_settings
from app.core.models import AccountStatus, BanCache, SteamAccount, User
from app.core.security import encryption_service
from app.integrations.steam import steam_integration
from app.sessions.adapters import get_steam_client_adapter
from app.sessions.manager import record_account_event, update_account_status
from app.steam_accounts.schemas import BanInfoResponse, SteamAccountCreate

DEMO_PASSWORD_MARKER = "[deckpilot-demo-no-password-collected]"


def _display_identifier(payload: SteamAccountCreate) -> str:
    return payload.display_name or payload.username or payload.steam_id or payload.profile_url or payload.label


def _steamid_from_payload(payload: SteamAccountCreate) -> str | None:
    if payload.steam_id:
        return payload.steam_id
    return None


def account_for_owner(db: Session, user: User, account_id: int) -> SteamAccount:
    account = db.query(SteamAccount).filter(SteamAccount.id == account_id, SteamAccount.user_id == user.id).one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


def list_accounts(db: Session, user: User) -> list[SteamAccount]:
    return db.query(SteamAccount).filter(SteamAccount.user_id == user.id).order_by(SteamAccount.id.desc()).all()


def create_account(db: Session, user: User, payload: SteamAccountCreate) -> SteamAccount:
    if not payload.ownership_attested:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ownership attestation is required")
    settings = get_settings()
    if payload.password and (settings.environment == "production" or settings.steam_integration_mode == "official"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password-based Steam linking is disabled in this environment")
    if settings.steam_integration_mode == "official" and not settings.steam_official_linking_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Official Steam linking is not configured yet")

    assert_account_limit(db, user)
    identifier = _display_identifier(payload)
    password_marker = payload.password if payload.password and settings.steam_integration_mode == "demo" else DEMO_PASSWORD_MARKER
    account = SteamAccount(
        user_id=user.id,
        label=payload.label,
        username_encrypted=encryption_service.encrypt(identifier),
        password_encrypted=encryption_service.encrypt(password_marker),
        steamid64=_steamid_from_payload(payload),
        status=AccountStatus.offline.value,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    write_audit(db, "steam_account.create", "steam_account", account.id, user, {"steam_integration_mode": settings.steam_integration_mode})
    return account


def delete_account(db: Session, user: User, account_id: int) -> None:
    account = account_for_owner(db, user, account_id)
    db.delete(account)
    db.commit()
    write_audit(db, "steam_account.delete", "steam_account", account_id, user)


def login_account(db: Session, user: User, account_id: int, steam_guard_code: str | None) -> SteamAccount:
    account = account_for_owner(db, user, account_id)
    settings = get_settings()
    if settings.steam_integration_mode == "official" and not settings.steam_official_linking_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Official Steam linking is not configured yet")
    if settings.steam_integration_mode == "official":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Official Steam session control is not enabled in this build")

    username = encryption_service.decrypt(account.username_encrypted)
    password = "" if settings.steam_integration_mode == "demo" else encryption_service.decrypt(account.password_encrypted)
    record_account_event(
        db,
        user,
        account,
        event_type="account_login_requested",
        message="Steam account login requested by owner",
        commit=False,
    )
    result = get_steam_client_adapter().login_account(username, password, steam_guard_code)
    if result.steam_guard_required:
        update_account_status(db, account, status_value=AccountStatus.offline.value, event_type="steam_guard_required")
        record_account_event(
            db,
            user,
            account,
            event_type="steam_guard_required",
            message="Steam Guard code is required to continue login",
            commit=False,
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Steam Guard code required")
    if not result.ok:
        account.status = AccountStatus.error.value
        update_account_status(db, account, status_value=AccountStatus.error.value, event_type="account_login_error", error_message=result.error)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.error or "Steam login failed")
    account.status = AccountStatus.online.value
    account.steamid64 = result.steamid64
    account.last_login_at = datetime.now(UTC)
    update_account_status(db, account, status_value=AccountStatus.online.value, event_type="account_online")
    record_account_event(
        db,
        user,
        account,
        event_type="account_online",
        message="Steam account is online",
        commit=False,
    )
    db.commit()
    db.refresh(account)
    write_audit(db, "steam_account.login", "steam_account", account.id, user)
    return account


def logout_account(db: Session, user: User, account_id: int) -> SteamAccount:
    account = account_for_owner(db, user, account_id)
    get_steam_client_adapter().logout_account(account)
    account.status = AccountStatus.offline.value
    update_account_status(db, account, status_value=AccountStatus.offline.value, event_type="account_offline")
    db.commit()
    db.refresh(account)
    write_audit(db, "steam_account.logout", "steam_account", account.id, user)
    return account


def selected_games_count(account: SteamAccount) -> int:
    return len(account.selected_games or [])


def get_ban_info(db: Session, user: User, account_id: int) -> BanInfoResponse:
    account = account_for_owner(db, user, account_id)
    settings = get_settings()
    if settings.steam_integration_mode == "official" and not settings.steam_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Official Steam ban lookup is not configured yet")
    cached = db.query(BanCache).filter(BanCache.account_id == account.id).one_or_none()
    if cached:
        payload = json.loads(cached.payload)
        payload["cached"] = True
        return BanInfoResponse(**payload)
    payload = steam_integration.fetch_ban_info(account.steamid64)
    db.add(BanCache(account_id=account.id, payload=json.dumps(payload)))
    db.commit()
    write_audit(db, "steam_account.ban_info", "steam_account", account.id, user)
    return BanInfoResponse(**payload)
