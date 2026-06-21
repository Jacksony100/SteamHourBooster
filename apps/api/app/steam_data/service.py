"""Steam public profile + game artwork service.

Sources only official Steam endpoints/CDN. No credentials are required for this
data; the Steam Web API key (when configured for official mode) stays server-side
and is never returned to the frontend. Demo/test mode returns deterministic,
clearly-labeled demo data so the UI is fully exercisable without live Steam.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.models import SteamAccount, SteamGameAsset, SteamOwnedGameCache, SteamProfileCache
from app.integrations.steam import steam_integration
from app.steam_data import cdn
from app.steam_data.schemas import (
    GameAssetsResponse,
    OwnedGameResponse,
    OwnedGamesResponse,
    SteamProfileResponse,
)

PROFILE_TTL = timedelta(hours=1)
GAMES_TTL = timedelta(hours=6)


def _now() -> datetime:
    return datetime.now(UTC)


def _as_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _is_stale(last_fetched_at: datetime | None, ttl: timedelta) -> bool:
    aware = _as_aware(last_fetched_at)
    return aware is None or (_now() - aware) > ttl


def get_profile(db: Session, account: SteamAccount, *, force: bool = False) -> SteamProfileResponse:
    cache = db.query(SteamProfileCache).filter(SteamProfileCache.account_id == account.id).one_or_none()
    if cache and not force and not _is_stale(cache.last_fetched_at, PROFILE_TTL):
        return _profile_response(account.id, cache, stale=False)

    summary = steam_integration.fetch_profile_summary(account.steamid64, persona_hint=account.label)
    if not cache:
        cache = SteamProfileCache(account_id=account.id)
        db.add(cache)
    cache.steamid64 = summary.get("steamid64") or account.steamid64
    cache.persona_name = summary.get("persona_name")
    cache.profile_url = summary.get("profile_url")
    cache.avatar_small = summary.get("avatar_small")
    cache.avatar_medium = summary.get("avatar_medium")
    cache.avatar_full = summary.get("avatar_full")
    cache.persona_state = summary.get("persona_state")
    cache.visibility = summary.get("visibility") or "unknown"
    cache.fetch_status = "unavailable" if cache.visibility == "unavailable" else "ok"
    cache.error_message = None
    cache.last_fetched_at = _now()
    db.commit()
    db.refresh(cache)
    return _profile_response(account.id, cache, stale=False)


def _profile_response(account_id: int, cache: SteamProfileCache, *, stale: bool) -> SteamProfileResponse:
    return SteamProfileResponse(
        account_id=account_id,
        steamid64=cache.steamid64,
        persona_name=cache.persona_name,
        profile_url=cache.profile_url,
        avatar_small=cache.avatar_small,
        avatar_medium=cache.avatar_medium,
        avatar_full=cache.avatar_full,
        persona_state=cache.persona_state,
        visibility=cache.visibility,
        fetch_status=cache.fetch_status,
        last_fetched_at=cache.last_fetched_at,
        stale=stale,
    )


def get_owned_games(db: Session, account: SteamAccount, *, force: bool = False) -> OwnedGamesResponse:
    rows = db.query(SteamOwnedGameCache).filter(SteamOwnedGameCache.account_id == account.id).all()
    newest = max((_as_aware(r.last_fetched_at) for r in rows), default=None) if rows else None
    if rows and not force and not _is_stale(newest, GAMES_TTL):
        return _games_response(account.id, rows, stale=False)

    fetched = steam_integration.fetch_owned_games(account.steamid64)
    existing = {row.app_id: row for row in rows}
    seen: set[int] = set()
    for game in fetched:
        app_id = int(game["app_id"])
        seen.add(app_id)
        row = existing.get(app_id) or SteamOwnedGameCache(account_id=account.id, app_id=app_id)
        if app_id not in existing:
            db.add(row)
        row.name = game.get("name")
        row.playtime_forever = int(game.get("playtime_forever") or 0)
        row.img_icon_hash = game.get("img_icon_hash")
        row.last_fetched_at = _now()
    # Drop games no longer owned (only when the source actually returned data).
    if fetched:
        for app_id, row in existing.items():
            if app_id not in seen:
                db.delete(row)
    db.commit()
    rows = db.query(SteamOwnedGameCache).filter(SteamOwnedGameCache.account_id == account.id).all()
    return _games_response(account.id, rows, stale=False)


def _games_response(account_id: int, rows: list[SteamOwnedGameCache], *, stale: bool) -> OwnedGamesResponse:
    games = []
    for row in sorted(rows, key=lambda r: r.playtime_forever or 0, reverse=True):
        assets = cdn.game_assets(row.app_id, row.name or "", row.img_icon_hash)
        games.append(
            OwnedGameResponse(
                app_id=row.app_id,
                name=row.name or f"App {row.app_id}",
                playtime_forever=row.playtime_forever or 0,
                icon_url=assets["icon_url"],
                header_image_url=assets["header_image_url"],
                capsule_image_url=assets["capsule_image_url"],
                library_image_url=assets["library_image_url"],
                store_url=assets["store_url"],
            )
        )
    newest = max((_as_aware(r.last_fetched_at) for r in rows), default=None) if rows else None
    return OwnedGamesResponse(account_id=account_id, games=games, count=len(games), last_fetched_at=newest, stale=stale)


def get_game_assets(db: Session, app_id: int, *, name: str = "") -> GameAssetsResponse:
    cache = db.query(SteamGameAsset).filter(SteamGameAsset.app_id == app_id).one_or_none()
    assets = cdn.game_assets(app_id, name)
    if not cache:
        cache = SteamGameAsset(app_id=app_id)
        db.add(cache)
    cache.name = name or cache.name
    cache.header_image_url = assets["header_image_url"]
    cache.capsule_image_url = assets["capsule_image_url"]
    cache.library_image_url = assets["library_image_url"]
    cache.icon_url = assets["icon_url"]
    cache.store_url = assets["store_url"]
    cache.source = assets["source"]
    cache.last_fetched_at = _now()
    db.commit()
    return GameAssetsResponse(**assets)
