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
                {"app_id": 730, "name": "Counter-Strike 2", "playtime_forever": 4210, "img_icon_hash": None},
                {"app_id": 570, "name": "Dota 2", "playtime_forever": 8930, "img_icon_hash": None},
                {"app_id": 440, "name": "Team Fortress 2", "playtime_forever": 1290, "img_icon_hash": None},
                {"app_id": 1172470, "name": "Apex Legends", "playtime_forever": 760, "img_icon_hash": None},
                {"app_id": 252490, "name": "Rust", "playtime_forever": 2050, "img_icon_hash": None},
                {"app_id": 578080, "name": "PUBG: BATTLEGROUNDS", "playtime_forever": 540, "img_icon_hash": None},
            ]
        # Official mode without a configured key returns nothing rather than guessing.
        return []

    def fetch_profile_summary(self, steamid64: str | None, *, persona_hint: str | None = None) -> dict:
        """Public profile summary. Demo mode synthesizes stable, clearly-demo data."""

        from app.steam_data.cdn import default_avatar

        if self.settings.steam_integration_mode == "demo" or self.settings.steam_test_mode:
            sid = steamid64 or "0"
            return {
                "steamid64": steamid64,
                "persona_name": persona_hint or f"DemoPlayer-{sid[-4:]}",
                "profile_url": f"https://steamcommunity.com/profiles/{sid}" if steamid64 else None,
                "avatar_small": default_avatar("small"),
                "avatar_medium": default_avatar("medium"),
                "avatar_full": default_avatar("full"),
                "persona_state": 1,
                "visibility": "public",
            }
        # Official mode without a configured key: signal unavailable, never invent data.
        return {
            "steamid64": steamid64,
            "persona_name": None,
            "profile_url": None,
            "avatar_small": None,
            "avatar_medium": None,
            "avatar_full": None,
            "persona_state": None,
            "visibility": "unavailable",
        }

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
