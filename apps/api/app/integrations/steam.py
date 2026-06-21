import httpx

from app.core.config import get_settings
from app.core.observability import get_logger

logger = get_logger("app.integrations.steam")

STEAM_API = "https://api.steampowered.com"


class SteamIntegration:
    """Steam Web API / login abstraction.

    Demo/test mode intentionally avoids real Steam calls so the product can be
    developed and reviewed without adding stealth or evasion behavior. Official
    mode reads only PUBLIC profile/owned-games/ban data via the official Steam
    Web API using a server-side key; it performs no session automation here.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def _demo(self) -> bool:
        settings = get_settings()
        return settings.steam_integration_mode == "demo" or settings.steam_test_mode

    def _official_key(self) -> str | None:
        settings = get_settings()
        if settings.steam_integration_mode == "official" and settings.steam_api_key:
            return settings.steam_api_key
        return None

    def _get(self, path: str, params: dict) -> dict | None:
        try:
            response = httpx.get(f"{STEAM_API}{path}", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # graceful degradation; never leak the key
            logger.warning("Steam Web API call failed: %s", type(exc).__name__)
            return None

    def login_account(self, username: str, password: str, steam_guard_code: str | None = None) -> dict:
        if self._demo():
            return {"ok": True, "steamid64": f"test-{abs(hash(username)) % 10_000_000}"}
        return {"ok": False, "error": "Official Steam linking is not configured yet"}

    def logout_account(self, steamid64: str | None) -> dict:
        return {"ok": True}

    def fetch_owned_games(self, steamid64: str | None) -> list[dict]:
        if self._demo():
            return [
                {"app_id": 730, "name": "Counter-Strike 2", "playtime_forever": 4210, "img_icon_hash": None},
                {"app_id": 570, "name": "Dota 2", "playtime_forever": 8930, "img_icon_hash": None},
                {"app_id": 440, "name": "Team Fortress 2", "playtime_forever": 1290, "img_icon_hash": None},
                {"app_id": 1172470, "name": "Apex Legends", "playtime_forever": 760, "img_icon_hash": None},
                {"app_id": 252490, "name": "Rust", "playtime_forever": 2050, "img_icon_hash": None},
                {"app_id": 578080, "name": "PUBG: BATTLEGROUNDS", "playtime_forever": 540, "img_icon_hash": None},
            ]
        key = self._official_key()
        if not key or not steamid64:
            return []
        data = self._get(
            "/IPlayerService/GetOwnedGames/v1/",
            {"key": key, "steamid": steamid64, "include_appinfo": 1, "include_played_free_games": 1, "format": "json"},
        )
        games = (data or {}).get("response", {}).get("games", []) if data else []
        return [
            {
                "app_id": int(g["appid"]),
                "name": g.get("name") or f"App {g.get('appid')}",
                "playtime_forever": int(g.get("playtime_forever") or 0),
                "img_icon_hash": g.get("img_icon_url") or None,
            }
            for g in games
        ]

    def fetch_profile_summary(self, steamid64: str | None, *, persona_hint: str | None = None) -> dict:
        from app.steam_data.cdn import default_avatar

        if self._demo():
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
        key = self._official_key()
        if key and steamid64:
            data = self._get("/ISteamUser/GetPlayerSummaries/v2/", {"key": key, "steamids": steamid64})
            players = (data or {}).get("response", {}).get("players", []) if data else []
            if players:
                p = players[0]
                visible = int(p.get("communityvisibilitystate", 1)) == 3
                return {
                    "steamid64": p.get("steamid", steamid64),
                    "persona_name": p.get("personaname"),
                    "profile_url": p.get("profileurl"),
                    "avatar_small": p.get("avatar"),
                    "avatar_medium": p.get("avatarmedium"),
                    "avatar_full": p.get("avatarfull"),
                    "persona_state": int(p.get("personastate", 0)),
                    "visibility": "public" if visible else "private",
                }
        # Official mode but unavailable / private: signal unavailable, never invent data.
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
        if self._demo():
            return {
                "vac_banned": False,
                "community_banned": False,
                "economy_ban": "none",
                "days_since_last_ban": None,
                "number_of_vac_bans": 0,
            }
        key = self._official_key()
        if key and steamid64:
            data = self._get("/ISteamUser/GetPlayerBans/v1/", {"key": key, "steamids": steamid64})
            players = (data or {}).get("players", []) if data else []
            if players:
                p = players[0]
                return {
                    "vac_banned": bool(p.get("VACBanned", False)),
                    "community_banned": bool(p.get("CommunityBanned", False)),
                    "economy_ban": p.get("EconomyBan", "none"),
                    "days_since_last_ban": p.get("DaysSinceLastBan"),
                    "number_of_vac_bans": int(p.get("NumberOfVACBans", 0)),
                }
        return {
            "vac_banned": False,
            "community_banned": False,
            "economy_ban": "unknown",
            "days_since_last_ban": None,
            "number_of_vac_bans": 0,
        }


steam_integration = SteamIntegration()
