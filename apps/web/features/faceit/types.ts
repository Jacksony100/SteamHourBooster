export type FaceitStats = {
  matches: string | null;
  win_rate: string | null;
  kd_ratio: string | null;
  headshots: string | null;
  avg_kills: string | null;
  mvps: string | null;
  current_win_streak: string | null;
  longest_win_streak: string | null;
  recent_results: string[];
};

export type FaceitMap = {
  name: string;
  matches: string | null;
  win_rate: string | null;
  kd_ratio: string | null;
};

export type FaceitMatch = {
  match_id: string | null;
  map: string | null;
  result: string | null;
  score: string | null;
  kills: string | null;
  deaths: string | null;
  assists: string | null;
  kd_ratio: string | null;
  kr_ratio: string | null;
  adr: string | null;
  headshots: string | null;
  mvps: string | null;
  triple_kills: string | null;
  quadro_kills: string | null;
  penta_kills: string | null;
  clutches: string | null;
  date: string | null;
  faceit_url: string | null;
};

export type EloPoint = { date: string | null; elo: number };

export type FaceitTeammate = {
  player_id: string;
  nickname: string | null;
  games: number;
  wins: number;
  win_rate: string | null;
};

export type FaceitRecentForm = {
  matches: number;
  wins: number;
  win_rate: number;
  kd_ratio: number | null;
  adr: number | null;
  headshots: number | null;
  kd_delta: number | null;
};

export type FaceitStreak = { type: string; length: number; tilt: boolean };

export type FaceitSmurf = { score: number; flags: string[] };

export type FaceitAdvanced = {
  entry_per_match: number | null;
  entry_success: number | null;
  clutch_1v1: number | null;
  clutch_1v2: number | null;
  flashes_per_match: number | null;
  utility_dmg_per_match: number | null;
  sniper_per_match: number | null;
  pistol_total: number | null;
  aces: number | null;
  quad_kills: number | null;
  triple_kills: number | null;
  avg_kills: number | null;
  avg_deaths: number | null;
  avg_assists: number | null;
};

export type FaceitSteam = {
  steamid64: string;
  persona_name: string | null;
  avatar: string | null;
  profile_url: string | null;
  country: string | null;
  visibility: string | null;
  account_created: string | null;
  steam_level: number | null;
  cs2_hours: number | null;
  vac_banned: boolean | null;
  vac_ban_count: number | null;
};

export type FaceitResult = {
  found: boolean;
  configured: boolean;
  steamid64: string | null;
  player_id: string | null;
  nickname: string | null;
  avatar: string | null;
  country: string | null;
  faceit_url: string | null;
  skill_level: number | null;
  faceit_elo: number | null;
  region: string | null;
  stats: FaceitStats;
  maps: FaceitMap[];
  matches: FaceitMatch[];
  elo_history: EloPoint[];
  elo_history_approx: boolean;
  teammates: FaceitTeammate[];
  recent_form: FaceitRecentForm | null;
  streak: FaceitStreak | null;
  smurf: FaceitSmurf | null;
  steam: FaceitSteam | null;
  advanced: FaceitAdvanced | null;
  radar: Record<string, number | null> | null;
  activity: number[] | null;
  best_match: FaceitMatch | null;
  worst_match: FaceitMatch | null;
  consistency: number | null;
  percentile: number | null;
  message: string | null;
  source: string | null;
  detail_level: string;
};

export type FaceitCompare = { players: FaceitResult[] };

export type FaceitScorePlayer = {
  player_id: string | null;
  nickname: string | null;
  kills: string | null;
  deaths: string | null;
  assists: string | null;
  kd_ratio: string | null;
  adr: string | null;
  headshots: string | null;
  mvps: string | null;
};

export type FaceitScoreTeam = { name: string; win: boolean; score: string | null; players: FaceitScorePlayer[] };

export type FaceitScoreboard = {
  match_id: string;
  map: string | null;
  score: string | null;
  teams: FaceitScoreTeam[];
};

export type WatchItem = { player_id: string; nickname: string | null; country: string | null };
