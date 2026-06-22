from pydantic import BaseModel


class FaceitStats(BaseModel):
    matches: str | None = None
    win_rate: str | None = None
    kd_ratio: str | None = None
    headshots: str | None = None
    avg_kills: str | None = None
    mvps: str | None = None
    current_win_streak: str | None = None
    longest_win_streak: str | None = None
    recent_results: list[str] = []


class FaceitMap(BaseModel):
    name: str
    matches: str | None = None
    win_rate: str | None = None
    kd_ratio: str | None = None


class FaceitMatch(BaseModel):
    match_id: str | None = None
    map: str | None = None
    result: str | None = None  # "win" | "loss"
    score: str | None = None
    kills: str | None = None
    deaths: str | None = None
    kd_ratio: str | None = None
    headshots: str | None = None
    date: str | None = None
    faceit_url: str | None = None


class FaceitFinderResponse(BaseModel):
    found: bool
    configured: bool = True
    steamid64: str | None = None
    player_id: str | None = None
    nickname: str | None = None
    avatar: str | None = None
    country: str | None = None
    faceit_url: str | None = None
    skill_level: int | None = None
    faceit_elo: int | None = None
    region: str | None = None
    stats: FaceitStats = FaceitStats()
    maps: list[FaceitMap] = []
    matches: list[FaceitMatch] = []
    message: str | None = None
    source: str | None = None
    # "full" = lifetime + maps + match history (official API); "basic" = level/ELO only (keyless)
    detail_level: str = "basic"
