from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import current_user, require_csrf
from app.core.models import User
from app.core.rate_limit import rate_limit
from app.faceit.schemas import (
    FaceitCompareResponse,
    FaceitFinderResponse,
    FaceitScoreboard,
    FaceitStats,
    FaceitWatchAddRequest,
    FaceitWatchItem,
    FaceitWatchListResponse,
)
from app.faceit.service import find_many, find_player, match_scoreboard
from app.faceit.snapshots import record_elo_snapshot, snapshot_series
from app.faceit import watchlist as wl

router = APIRouter(prefix="/faceit", tags=["faceit"])


def _enrich_with_snapshots(db: Session, result: dict) -> dict:
    """Record today's ELO snapshot and overlay the real accumulated series when we have
    enough points. Never mutates the (possibly cached) input dict."""
    if not (result.get("found") and result.get("player_id")):
        return result
    record_elo_snapshot(
        db, result["player_id"], result.get("faceit_elo"),
        nickname=result.get("nickname"), skill_level=result.get("skill_level"),
    )
    series = snapshot_series(db, result["player_id"], get_settings().faceit_elo_history_size)
    if len(series) >= 2:
        return {**result, "elo_history": series, "elo_history_approx": False}
    return result


def _to_response(result: dict) -> FaceitFinderResponse:
    # Shallow-copy: find_player caches the exact dict, so we must not pop() from it
    # (a second cache hit — incl. comparing a player against themselves — would lose stats).
    data = dict(result)
    stats = data.pop("stats", {})
    if not isinstance(stats, dict):
        stats = {}
    return FaceitFinderResponse(**data, stats=FaceitStats(**stats))


@router.get(
    "/find",
    response_model=FaceitFinderResponse,
    # Public, unauthenticated endpoint -> IP-based rate limit to protect the API quota.
    dependencies=[Depends(rate_limit("faceit_find", 20, 60))],
)
def find(
    steam: str = Query(..., min_length=2, max_length=200, description="FACEIT nickname, Steam profile URL, or SteamID64"),
    refresh: bool = Query(False, description="Bypass the cache and re-fetch live"),
    db: Session = Depends(get_db),
):
    return _to_response(_enrich_with_snapshots(db, find_player(steam, force=refresh)))


@router.get(
    "/compare",
    response_model=FaceitCompareResponse,
    # Up to 5 lookups per call (cached + parallel) -> tighter IP-based rate limit.
    dependencies=[Depends(rate_limit("faceit_compare", 12, 60))],
)
def compare(
    players: list[str] = Query(..., description="2–5 players: FACEIT nickname, Steam URL, or SteamID64"),
    db: Session = Depends(get_db),
):
    cleaned = [p.strip() for p in players if p and p.strip()]
    if not 2 <= len(cleaned) <= 5:
        raise HTTPException(status_code=422, detail="Provide between 2 and 5 players to compare.")
    if any(not 2 <= len(p) <= 200 for p in cleaned):
        raise HTTPException(status_code=422, detail="Each player query must be 2–200 characters.")
    results = [_enrich_with_snapshots(db, r) for r in find_many(cleaned)]
    return FaceitCompareResponse(players=[_to_response(r) for r in results])


@router.get(
    "/match/{match_id}",
    response_model=FaceitScoreboard,
    dependencies=[Depends(rate_limit("faceit_match", 30, 60))],
)
def match(match_id: str):
    board = match_scoreboard(match_id)
    if not board:
        raise HTTPException(status_code=404, detail="Match not found or has no stats.")
    return FaceitScoreboard(**board)


@router.get("/watchlist", response_model=FaceitWatchListResponse)
def get_watchlist(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return FaceitWatchListResponse(items=[FaceitWatchItem(**w) for w in wl.list_watches(db, user.id)])


@router.post("/watchlist", response_model=FaceitWatchListResponse, dependencies=[Depends(require_csrf)])
def add_watchlist(payload: FaceitWatchAddRequest, user: User = Depends(current_user), db: Session = Depends(get_db)):
    wl.add_watch(db, user.id, payload.player_id, nickname=payload.nickname, country=payload.country)
    return FaceitWatchListResponse(items=[FaceitWatchItem(**w) for w in wl.list_watches(db, user.id)])


@router.delete("/watchlist/{player_id}", response_model=FaceitWatchListResponse, dependencies=[Depends(require_csrf)])
def remove_watchlist(player_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    wl.remove_watch(db, user.id, player_id)
    return FaceitWatchListResponse(items=[FaceitWatchItem(**w) for w in wl.list_watches(db, user.id)])
