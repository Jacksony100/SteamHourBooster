"""Deterministic Steam public-CDN URL builders.

Steam game artwork lives at well-known, hash-free CDN paths keyed by ``appid``.
These are public marketing assets served by Valve's official CDN — no API key,
no credentials, no scraping of third-party/pirated sources. Callers must provide
a frontend fallback for the cases where a specific asset 404s (older apps lack
some sizes).
"""

from __future__ import annotations

# Official Valve CDN host for app artwork.
STEAM_CDN = "https://cdn.cloudflare.steamstatic.com/steam/apps"
# Official Valve community host for hash-addressed game icons.
STEAM_MEDIA = "https://media.steampowered.com/steamcommunity/public/images/apps"
STORE_BASE = "https://store.steampowered.com/app"

# Stable Steam-hosted default avatar (used for demo accounts so the frontend
# only ever loads images from approved Steam CDN domains).
DEFAULT_AVATAR_HASH = "fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb"
AVATAR_CDN = "https://avatars.cloudflare.steamstatic.com"

# Allowed image hosts — mirror this list in apps/web/next.config.mjs.
ALLOWED_IMAGE_HOSTS = (
    "cdn.cloudflare.steamstatic.com",
    "media.steampowered.com",
    "avatars.cloudflare.steamstatic.com",
    "shared.cloudflare.steamstatic.com",
)


def header_image(app_id: int) -> str:
    return f"{STEAM_CDN}/{app_id}/header.jpg"


def capsule_image(app_id: int) -> str:
    return f"{STEAM_CDN}/{app_id}/capsule_616x353.jpg"


def capsule_small(app_id: int) -> str:
    return f"{STEAM_CDN}/{app_id}/capsule_231x87.jpg"


def library_image(app_id: int) -> str:
    return f"{STEAM_CDN}/{app_id}/library_600x900.jpg"


def library_hero(app_id: int) -> str:
    return f"{STEAM_CDN}/{app_id}/library_hero.jpg"


def logo_image(app_id: int) -> str:
    return f"{STEAM_CDN}/{app_id}/logo.png"


def icon_image(app_id: int, img_icon_hash: str | None) -> str | None:
    """Game icon URL. Requires the per-app ``img_icon_url`` hash from
    GetOwnedGames; returns ``None`` when unavailable so the UI falls back."""

    if not img_icon_hash:
        return None
    return f"{STEAM_MEDIA}/{app_id}/{img_icon_hash}.jpg"


def store_url(app_id: int) -> str:
    return f"{STORE_BASE}/{app_id}/"


def default_avatar(size: str = "full") -> str:
    suffix = {"small": "", "medium": "_medium", "full": "_full"}.get(size, "_full")
    return f"{AVATAR_CDN}/{DEFAULT_AVATAR_HASH}{suffix}.jpg"


def game_assets(app_id: int, name: str = "", img_icon_hash: str | None = None) -> dict:
    """Full asset bundle for one app id (frontend-ready, with a fallback gradient seed)."""

    return {
        "app_id": app_id,
        "name": name,
        "header_image_url": header_image(app_id),
        "capsule_image_url": capsule_image(app_id),
        "capsule_small_url": capsule_small(app_id),
        "library_image_url": library_image(app_id),
        "library_hero_url": library_hero(app_id),
        "logo_url": logo_image(app_id),
        "icon_url": icon_image(app_id, img_icon_hash),
        "store_url": store_url(app_id),
        "source": "steam_cdn",
    }
