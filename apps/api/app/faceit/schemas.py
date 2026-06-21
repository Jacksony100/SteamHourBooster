from pydantic import BaseModel


class FaceitStats(BaseModel):
    matches: str | None = None
    win_rate: str | None = None
    kd_ratio: str | None = None
    headshots: str | None = None
    current_win_streak: str | None = None
    longest_win_streak: str | None = None
    recent_results: list[str] = []


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
    message: str | None = None
