from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import current_user, require_csrf
from app.core.models import User
from app.core.rate_limit import rate_limit
from app.steam_accounts.service import account_for_owner
from app.steam_data.schemas import GameAssetsResponse, OwnedGamesResponse, SteamProfileResponse
from app.steam_data.service import get_game_assets, get_owned_games, get_profile

router = APIRouter(tags=["steam-data"])


@router.get("/accounts/{account_id}/steam-profile", response_model=SteamProfileResponse)
def steam_profile(account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    account = account_for_owner(db, user, account_id)
    return get_profile(db, account, force=False)


@router.post(
    "/accounts/{account_id}/steam-profile/refresh",
    response_model=SteamProfileResponse,
    dependencies=[Depends(require_csrf), Depends(rate_limit("steam_refresh", 12, 60))],
)
def steam_profile_refresh(account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    account = account_for_owner(db, user, account_id)
    return get_profile(db, account, force=True)


@router.get("/accounts/{account_id}/owned-games", response_model=OwnedGamesResponse)
def owned_games(account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    account = account_for_owner(db, user, account_id)
    return get_owned_games(db, account, force=False)


@router.post(
    "/accounts/{account_id}/owned-games/refresh",
    response_model=OwnedGamesResponse,
    dependencies=[Depends(require_csrf), Depends(rate_limit("steam_refresh", 12, 60))],
)
def owned_games_refresh(account_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    account = account_for_owner(db, user, account_id)
    return get_owned_games(db, account, force=True)


@router.get("/games/{app_id}/assets", response_model=GameAssetsResponse)
def game_assets(app_id: int, _user: User = Depends(current_user), db: Session = Depends(get_db)):
    return get_game_assets(db, app_id)
