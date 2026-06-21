# Steam Public Data Integration

Adds Steam **profile/avatar** and **game artwork** to the product. Sources only
official Steam endpoints/CDN. No credentials are needed for this public data; the
Steam Web API key (used only in a future `official` mode) stays server-side and is
**never** returned to the frontend.

## Backend (`apps/api/app/steam_data/`)
| File | Role |
|---|---|
| `cdn.py` | Deterministic Steam CDN URL builders (header/capsule/library/logo/icon/store) + `ALLOWED_IMAGE_HOSTS`. Pure functions, no secrets, no DB. |
| `service.py` | Profile + owned-games fetch with DB caching (TTL) and a `stale` flag; asset upsert. |
| `schemas.py` | Response models. |
| `routes.py` | Endpoints (ownership-checked, CSRF + rate-limited on refresh). |

### Endpoints
| Method | Path | Notes |
|---|---|---|
| GET | `/api/v1/accounts/{id}/steam-profile` | Owner-only; cached |
| POST | `/api/v1/accounts/{id}/steam-profile/refresh` | CSRF + rate-limited (`steam_refresh`, 12/min) |
| GET | `/api/v1/accounts/{id}/owned-games` | Owner-only; cached |
| POST | `/api/v1/accounts/{id}/owned-games/refresh` | CSRF + rate-limited |
| GET | `/api/v1/games/{app_id}/assets` | Auth-only; CDN URLs by app id |

### Caching (TTL)
- Profile cache TTL: **1h** (`steam_profile_cache`).
- Owned games TTL: **6h** (`steam_owned_games_cache`).
- Asset cache: `steam_game_assets` (upserted per app id).
- Tables + indexes added in migration `006_steam_data`.

### Modes
- **demo / test:** deterministic, clearly-labeled demo data (default avatar from
  Steam's own CDN, a fixed owned-games list). Fully exercisable offline.
- **official:** reserved for a configured `STEAM_API_KEY`; profile/games fetch via
  the Steam Web API (`GetPlayerSummaries`, `GetOwnedGames` with `include_appinfo=1`).
  Until configured, returns `visibility="unavailable"` rather than inventing data.

## Frontend
- `lib/steam.ts` — typed fetchers.
- `components/ui-kit/game-image.tsx` (`GameImage`) — Steam artwork with a **branded
  gradient fallback** on 404/missing (older apps lack some sizes).
- `components/ui-kit/steam-avatar.tsx` (`SteamAvatar`) — avatar with initials
  fallback for private/unavailable profiles + optional presence dot.
- `next.config.mjs` `images.remotePatterns` + CSP `img-src` allow only the approved
  Steam CDN hosts (mirrors `cdn.ALLOWED_IMAGE_HOSTS`).

## Security
- Account-ownership check on every account-scoped endpoint (`account_for_owner`).
- Steam API key never sent to the browser.
- Refresh endpoints are CSRF-protected and rate-limited.
- Private/unavailable profiles handled gracefully (no broken UI, no leaked errors).

## Tests
`apps/api/tests/test_steam_data.py`: avatar from Steam CDN, owned-games artwork URL
shape, asset URL builder, refresh-requires-CSRF, owner-only (cross-user 404),
requires-auth.

## TODO (official mode)
- Implement live `GetPlayerSummaries` / `GetOwnedGames` httpx calls behind the key.
- Persist `img_icon_url` hash for real game icons.
- Background refresh job (currently on-demand only).
