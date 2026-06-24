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


class FaceitEloPoint(BaseModel):
    date: str | None = None
    elo: int


class FaceitMatch(BaseModel):
    match_id: str | None = None
    map: str | None = None
    result: str | None = None  # "win" | "loss"
    score: str | None = None
    kills: str | None = None
    deaths: str | None = None
    assists: str | None = None
    kd_ratio: str | None = None
    kr_ratio: str | None = None
    adr: str | None = None
    headshots: str | None = None
    mvps: str | None = None
    triple_kills: str | None = None
    quadro_kills: str | None = None
    penta_kills: str | None = None
    clutches: str | None = None
    date: str | None = None
    faceit_url: str | None = None


class FaceitTeammate(BaseModel):
    player_id: str
    nickname: str | None = None
    games: int
    wins: int
    win_rate: str | None = None


class FaceitRecentForm(BaseModel):
    matches: int
    wins: int
    win_rate: int
    kd_ratio: float | None = None
    adr: float | None = None
    headshots: int | None = None
    kd_delta: float | None = None


class FaceitStreak(BaseModel):
    type: str  # "win" | "loss"
    length: int
    tilt: bool = False


class FaceitSmurf(BaseModel):
    score: int
    flags: list[str] = []


class FaceitAdvanced(BaseModel):
    entry_per_match: float | None = None
    entry_success: int | None = None
    clutch_1v1: int | None = None
    clutch_1v2: int | None = None
    flashes_per_match: float | None = None
    utility_dmg_per_match: int | None = None
    sniper_per_match: float | None = None
    pistol_total: int | None = None
    aces: int | None = None
    quad_kills: int | None = None
    triple_kills: int | None = None
    avg_kills: float | None = None
    avg_deaths: float | None = None
    avg_assists: float | None = None


class FaceitSteam(BaseModel):
    steamid64: str
    persona_name: str | None = None
    avatar: str | None = None
    profile_url: str | None = None
    country: str | None = None
    visibility: str | None = None
    account_created: str | None = None
    steam_level: int | None = None
    cs2_hours: int | None = None
    vac_banned: bool | None = None
    vac_ban_count: int | None = None


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
    elo_history: list[FaceitEloPoint] = []
    # True when elo_history is reconstructed from win/loss (approximate) rather than exact.
    elo_history_approx: bool = False
    teammates: list[FaceitTeammate] = []
    recent_form: FaceitRecentForm | None = None
    streak: FaceitStreak | None = None
    smurf: FaceitSmurf | None = None
    steam: FaceitSteam | None = None
    advanced: FaceitAdvanced | None = None
    radar: dict[str, int | None] | None = None
    activity: list[int] | None = None
    best_match: FaceitMatch | None = None
    worst_match: FaceitMatch | None = None
    consistency: int | None = None
    percentile: int | None = None
    message: str | None = None
    source: str | None = None
    # "full" = lifetime + maps + match history (official API); "basic" = level/ELO only (keyless)
    detail_level: str = "basic"


class FaceitCompareResponse(BaseModel):
    """2–5 players compared side by side."""
    players: list[FaceitFinderResponse]


class FaceitScorePlayer(BaseModel):
    player_id: str | None = None
    nickname: str | None = None
    kills: str | None = None
    deaths: str | None = None
    assists: str | None = None
    kd_ratio: str | None = None
    adr: str | None = None
    headshots: str | None = None
    mvps: str | None = None


class FaceitScoreTeam(BaseModel):
    name: str
    win: bool = False
    score: str | None = None
    players: list[FaceitScorePlayer] = []


class FaceitScoreboard(BaseModel):
    match_id: str
    map: str | None = None
    score: str | None = None
    teams: list[FaceitScoreTeam] = []


class FaceitWatchItem(BaseModel):
    player_id: str
    nickname: str | None = None
    country: str | None = None


class FaceitWatchListResponse(BaseModel):
    items: list[FaceitWatchItem] = []


class FaceitWatchAddRequest(BaseModel):
    player_id: str
    nickname: str | None = None
    country: str | None = None
