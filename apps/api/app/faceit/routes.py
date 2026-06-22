from fastapi import APIRouter, Depends, Query

from app.core.rate_limit import rate_limit
from app.faceit.schemas import FaceitFinderResponse, FaceitStats
from app.faceit.service import find_player

router = APIRouter(prefix="/faceit", tags=["faceit"])


@router.get(
    "/find",
    response_model=FaceitFinderResponse,
    # Public, unauthenticated endpoint -> IP-based rate limit to protect the API quota.
    dependencies=[Depends(rate_limit("faceit_find", 20, 60))],
)
def find(steam: str = Query(..., min_length=2, max_length=200, description="FACEIT nickname, Steam profile URL, or SteamID64")):
    result = find_player(steam)
    stats = result.pop("stats", {}) if isinstance(result.get("stats"), dict) else {}
    return FaceitFinderResponse(**result, stats=FaceitStats(**stats))
