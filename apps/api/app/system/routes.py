from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(prefix="/system", tags=["system"])


class SystemModeResponse(BaseModel):
    environment: str
    steam_test_mode: bool
    steam_integration_mode: str
    real_steam_enabled: bool
    official_steam_configured: bool
    password_login_allowed: bool
    billing_provider: str
    demo_mode: bool
    checkout_disabled_reason: str | None = None


@router.get("/mode", response_model=SystemModeResponse)
def mode() -> SystemModeResponse:
    settings = get_settings()
    official_steam_configured = settings.steam_integration_mode == "official" and settings.steam_official_linking_enabled and bool(settings.steam_api_key)
    real_steam_enabled = False
    demo_mode = settings.steam_integration_mode == "demo" or settings.steam_test_mode or not real_steam_enabled
    checkout_disabled_reason = None
    if settings.environment == "production" and demo_mode:
        checkout_disabled_reason = "Paid checkout is disabled for public demo mode."

    return SystemModeResponse(
        environment=settings.environment,
        steam_test_mode=settings.steam_test_mode,
        steam_integration_mode=settings.steam_integration_mode,
        real_steam_enabled=real_steam_enabled,
        official_steam_configured=official_steam_configured,
        password_login_allowed=settings.environment != "production" and settings.steam_integration_mode == "demo",
        billing_provider=settings.billing_provider,
        demo_mode=demo_mode,
        checkout_disabled_reason=checkout_disabled_reason,
    )
