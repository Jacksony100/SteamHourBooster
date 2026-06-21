from pydantic import BaseModel, Field


class SteamAccountCreate(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    username: str | None = Field(default=None, min_length=1, max_length=120)
    password: str | None = Field(default=None, min_length=1, max_length=256)
    steam_id: str | None = Field(default=None, max_length=32)
    profile_url: str | None = Field(default=None, max_length=255)
    display_name: str | None = Field(default=None, max_length=120)
    ownership_attested: bool


class SteamGuardRequest(BaseModel):
    steam_guard_code: str | None = Field(default=None, max_length=32)


class SteamAccountResponse(BaseModel):
    id: int
    label: str
    steamid64: str | None
    status: str
    selected_games_count: int


class BanInfoResponse(BaseModel):
    vac_banned: bool = False
    community_banned: bool = False
    economy_ban: str = "none"
    days_since_last_ban: int | None = None
    number_of_vac_bans: int = 0
    cached: bool = False
