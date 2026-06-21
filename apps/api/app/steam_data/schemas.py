from datetime import datetime

from pydantic import BaseModel


class SteamProfileResponse(BaseModel):
    account_id: int
    steamid64: str | None = None
    persona_name: str | None = None
    profile_url: str | None = None
    avatar_small: str | None = None
    avatar_medium: str | None = None
    avatar_full: str | None = None
    persona_state: int | None = None
    visibility: str = "unknown"
    fetch_status: str = "ok"
    last_fetched_at: datetime | None = None
    stale: bool = False


class GameAssetsResponse(BaseModel):
    app_id: int
    name: str = ""
    header_image_url: str | None = None
    capsule_image_url: str | None = None
    capsule_small_url: str | None = None
    library_image_url: str | None = None
    library_hero_url: str | None = None
    logo_url: str | None = None
    icon_url: str | None = None
    store_url: str | None = None
    source: str = "steam_cdn"


class OwnedGameResponse(BaseModel):
    app_id: int
    name: str
    playtime_forever: int = 0
    icon_url: str | None = None
    header_image_url: str | None = None
    capsule_image_url: str | None = None
    library_image_url: str | None = None
    store_url: str | None = None


class OwnedGamesResponse(BaseModel):
    account_id: int
    games: list[OwnedGameResponse]
    count: int
    last_fetched_at: datetime | None = None
    stale: bool = False
