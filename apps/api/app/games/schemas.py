from pydantic import BaseModel


class GameResponse(BaseModel):
    app_id: int
    name: str
    selected: bool = False


class SaveGamesRequest(BaseModel):
    app_ids: list[int]
