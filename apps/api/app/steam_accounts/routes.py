from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user, require_csrf
from app.core.models import User
from app.steam_accounts.schemas import BanInfoResponse, SteamAccountCreate, SteamAccountResponse, SteamGuardRequest
from app.steam_accounts.service import (
    create_account,
    delete_account,
    get_ban_info,
    list_accounts,
    login_account,
    logout_account,
    selected_games_count,
)

router = APIRouter(prefix="/steam-accounts", tags=["steam accounts"])


def serialize_account(account) -> SteamAccountResponse:
    return SteamAccountResponse(
        id=account.id,
        label=account.label,
        steamid64=account.steamid64,
        status=account.status,
        selected_games_count=selected_games_count(account),
    )


@router.get("", response_model=list[SteamAccountResponse])
def index(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [serialize_account(account) for account in list_accounts(db, user)]


@router.post("", response_model=SteamAccountResponse, dependencies=[Depends(require_csrf)])
def create(payload: SteamAccountCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return serialize_account(create_account(db, user, payload))


@router.post("/{account_id}/login", response_model=SteamAccountResponse, dependencies=[Depends(require_csrf)])
def login(account_id: int, payload: SteamGuardRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return serialize_account(login_account(db, user, account_id, payload.steam_guard_code))


@router.post("/{account_id}/logout", response_model=SteamAccountResponse, dependencies=[Depends(require_csrf)])
def logout(account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return serialize_account(logout_account(db, user, account_id))


@router.delete("/{account_id}", dependencies=[Depends(require_csrf)])
def delete(account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    delete_account(db, user, account_id)
    return {"ok": True}


@router.get("/{account_id}/ban-info", response_model=BanInfoResponse)
def ban_info(account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return get_ban_info(db, user, account_id)
