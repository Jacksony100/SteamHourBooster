from app.core.config import get_settings


class SteamIntegration:
    """Steam API/login abstraction.

    Test mode intentionally avoids real Steam login. It exists so the product can
    be developed and reviewed without adding stealth or evasion behavior.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def login_account(self, username: str, password: str, steam_guard_code: str | None = None) -> dict:
        if self.settings.steam_integration_mode == "demo" or self.settings.steam_test_mode:
            return {"ok": True, "steamid64": f"test-{abs(hash(username)) % 10_000_000}"}
        return {"ok": False, "error": "Official Steam linking is not configured yet"}

    def logout_account(self, steamid64: str | None) -> dict:
        return {"ok": True}

    def fetch_owned_games(self, steamid64: str | None) -> list[dict]:
        if self.settings.steam_integration_mode == "demo" or self.settings.steam_test_mode:
            return [
                {"app_id": 730, "name": "Counter-Strike 2"},
                {"app_id": 570, "name": "Dota 2"},
                {"app_id": 440, "name": "Team Fortress 2"},
                {"app_id": 1172470, "name": "Apex Legends"},
            ]
        return []

    def fetch_ban_info(self, steamid64: str | None) -> dict:
        if self.settings.steam_integration_mode == "demo" or self.settings.steam_test_mode:
            return {
                "vac_banned": False,
                "community_banned": False,
                "economy_ban": "none",
                "days_since_last_ban": None,
                "number_of_vac_bans": 0,
            }
        return {
            "vac_banned": False,
            "community_banned": False,
            "economy_ban": "unknown",
            "days_since_last_ban": None,
            "number_of_vac_bans": 0,
        }


steam_integration = SteamIntegration()
