from datetime import datetime

from pydantic import BaseModel, Field


class StartSessionRequest(BaseModel):
    account_id: int
    # Required for REAL (official) sessions: the owner's Steam Guard code for this
    # login. Ignored in demo mode. Single-use; never stored.
    steam_guard_code: str | None = Field(default=None, max_length=16)


class ActivitySessionResponse(BaseModel):
    id: int
    account_id: int
    status: str
    current_games: list[int]
    selected_games: list[int] = Field(default_factory=list)
    started_at: datetime | None
    stopped_at: datetime | None
    last_heartbeat_at: datetime | None = None
    error_message: str | None = None


class SessionLogResponse(BaseModel):
    id: int | None = None
    session_id: int | None = None
    account_id: int | None = None
    event_type: str | None = None
    message: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
