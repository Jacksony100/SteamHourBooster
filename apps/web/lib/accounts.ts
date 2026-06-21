import { api } from "@/lib/api";

export type SteamAccount = {
  id: number;
  label: string;
  steamid64: string | null;
  status: string;
  selected_games_count: number;
};

export type ActivitySession = {
  id: number;
  account_id: number;
  status: string;
  current_games: number[];
  selected_games: number[];
  started_at: string | null;
  stopped_at: string | null;
  last_heartbeat_at: string | null;
  error_message: string | null;
};

export type SessionEvent = {
  id: number | null;
  session_id: number | null;
  account_id: number | null;
  event_type: string | null;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export function listAccounts() {
  return api<SteamAccount[]>("/steam-accounts");
}

export function loginAccount(accountId: number, steamGuardCode?: string) {
  return api<SteamAccount>(`/steam-accounts/${accountId}/login`, {
    method: "POST",
    csrf: true,
    body: JSON.stringify({ steam_guard_code: steamGuardCode ?? null }),
  });
}

export function listSessions() {
  return api<ActivitySession[]>("/sessions");
}

export function startSession(accountId: number) {
  return api<ActivitySession>("/sessions", { method: "POST", csrf: true, body: JSON.stringify({ account_id: accountId }) });
}

export function stopSession(sessionId: number) {
  return api<ActivitySession>(`/sessions/${sessionId}/stop`, { method: "POST", csrf: true });
}

export function sessionEvents(sessionId: number) {
  return api<SessionEvent[]>(`/sessions/${sessionId}/events`);
}
