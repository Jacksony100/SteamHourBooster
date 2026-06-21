import { api } from "@/lib/api";

export type SteamProfile = {
  account_id: number;
  steamid64: string | null;
  persona_name: string | null;
  profile_url: string | null;
  avatar_small: string | null;
  avatar_medium: string | null;
  avatar_full: string | null;
  persona_state: number | null;
  visibility: string;
  fetch_status: string;
  last_fetched_at: string | null;
  stale: boolean;
};

export type OwnedGame = {
  app_id: number;
  name: string;
  playtime_forever: number;
  icon_url: string | null;
  header_image_url: string | null;
  capsule_image_url: string | null;
  library_image_url: string | null;
  store_url: string | null;
};

export type OwnedGames = {
  account_id: number;
  games: OwnedGame[];
  count: number;
  last_fetched_at: string | null;
  stale: boolean;
};

export type GameAssets = {
  app_id: number;
  name: string;
  header_image_url: string | null;
  capsule_image_url: string | null;
  capsule_small_url: string | null;
  library_image_url: string | null;
  library_hero_url: string | null;
  logo_url: string | null;
  icon_url: string | null;
  store_url: string | null;
  source: string;
};

export function getSteamProfile(accountId: number) {
  return api<SteamProfile>(`/accounts/${accountId}/steam-profile`);
}

export function refreshSteamProfile(accountId: number) {
  return api<SteamProfile>(`/accounts/${accountId}/steam-profile/refresh`, { method: "POST", csrf: true });
}

export function getOwnedGames(accountId: number) {
  return api<OwnedGames>(`/accounts/${accountId}/owned-games`);
}

export function refreshOwnedGames(accountId: number) {
  return api<OwnedGames>(`/accounts/${accountId}/owned-games/refresh`, { method: "POST", csrf: true });
}

export function getGameAssets(appId: number) {
  return api<GameAssets>(`/games/${appId}/assets`);
}
