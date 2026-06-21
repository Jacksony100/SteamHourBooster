from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import current_user, require_csrf
from app.core.models import AccountGame, Game, User
from app.games.schemas import GameResponse, SaveGamesRequest
from app.integrations.steam import steam_integration
from app.sessions.manager import record_account_event
from app.steam_accounts.service import account_for_owner

router = APIRouter(prefix="/games", tags=["games"])


@router.get("/{account_id}", response_model=list[GameResponse])
def list_owned_games(account_id: int, query: str = "", user: User = Depends(current_user), db: Session = Depends(get_db)):
    account = account_for_owner(db, user, account_id)
    settings = get_settings()
    if settings.steam_integration_mode == "official" and not settings.steam_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Official Steam game lookup is not configured yet")
    selected = {link.game.app_id for link in account.selected_games}
    games = steam_integration.fetch_owned_games(account.steamid64)
    if query:
        games = [game for game in games if query.lower() in game["name"].lower()]
    return [GameResponse(app_id=game["app_id"], name=game["name"], selected=game["app_id"] in selected) for game in games]


@router.put("/{account_id}", response_model=list[GameResponse], dependencies=[Depends(require_csrf)])
def save_games(account_id: int, payload: SaveGamesRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    account = account_for_owner(db, user, account_id)
    settings = get_settings()
    if settings.steam_integration_mode == "official" and not settings.steam_api_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Official Steam game lookup is not configured yet")
    db.query(AccountGame).filter(AccountGame.account_id == account.id).delete()
    selected_games = []
    owned = {game["app_id"]: game["name"] for game in steam_integration.fetch_owned_games(account.steamid64)}
    for app_id in payload.app_ids:
        name = owned.get(app_id, f"App {app_id}")
        game = db.query(Game).filter(Game.app_id == app_id).one_or_none()
        if not game:
            game = Game(app_id=app_id, name=name)
            db.add(game)
            db.flush()
        db.add(AccountGame(account_id=account.id, game_id=game.id))
        selected_games.append(GameResponse(app_id=game.app_id, name=game.name, selected=True))
    record_account_event(
        db,
        user,
        account,
        event_type="games_selected",
        message="Selected games were updated",
        metadata={"app_ids": payload.app_ids},
        commit=False,
    )
    db.commit()
    return selected_games
