"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Activity, AlertTriangle, Clock3, RotateCcw, Square } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

type Overview = {
  accounts_count: number;
  online_sessions: number;
  active_games: number;
  subscription_status: string;
  subscription_plan: string;
  active_session_limit?: number;
  recent_activity: Array<{ action: string; target_type: string; target_id: string; created_at: string }>;
};

type CurrentUser = {
  id: number;
  username: string;
  email: string | null;
  email_verified: boolean;
  is_admin: boolean;
  banned: boolean;
};

type Account = {
  id: number;
  label: string;
  steamid64: string | null;
  status: string;
  selected_games_count: number;
};

type Game = { app_id: number; name: string; selected: boolean };
type Session = {
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
type SessionEvent = {
  id: number;
  session_id: number | null;
  account_id: number | null;
  event_type: string;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

const activeStatuses = new Set(["starting", "running", "stopping"]);

function formatTime(value: string | null) {
  if (!value) return "never";
  return new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date(value));
}

function statusClass(status: string) {
  if (status === "running" || status === "online") return "border-emerald-300/30 text-emerald-200";
  if (status === "starting" || status === "stopping") return "border-sky-300/30 text-sky-200";
  if (status === "error") return "border-rose-300/30 text-rose-200";
  return "border-white/10 text-slate-300";
}

export function DashboardClient() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionEvents, setSessionEvents] = useState<Record<number, SessionEvent[]>>({});
  const [label, setLabel] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [steamId, setSteamId] = useState("");
  const [ownershipAttested, setOwnershipAttested] = useState(false);
  const [games, setGames] = useState<Game[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [gameQuery, setGameQuery] = useState("");
  const [guardAccount, setGuardAccount] = useState<Account | null>(null);
  const [guardCode, setGuardCode] = useState("");
  const [guardSubmitting, setGuardSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function refresh(silent = false) {
    if (!silent) setLoading(true);
    try {
      const [overviewData, accountData, sessionData, me] = await Promise.all([
        api<Overview>("/api/v1/dashboard/overview"),
        api<Account[]>("/api/v1/steam-accounts"),
        api<Session[]>("/api/v1/sessions"),
        api<CurrentUser>("/api/v1/auth/me")
      ]);
      setOverview(overviewData);
      setAccounts(accountData);
      setSessions(sessionData);
      setCurrentUser(me);
      setLoadError(null);

      const eventEntries = await Promise.all(
        sessionData.map(async (session) => {
          const events = await api<SessionEvent[]>(`/api/v1/sessions/${session.id}/events`).catch(() => []);
          return [session.id, events] as const;
        })
      );
      setSessionEvents(Object.fromEntries(eventEntries));
    } catch (error) {
      const message = error instanceof Error ? error.message : "Dashboard failed to load";
      setLoadError(message);
      if (!silent) toast.error(message);
    } finally {
      if (!silent) setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    const timer = window.setInterval(() => refresh(true), 5000);
    return () => window.clearInterval(timer);
  }, []);

  async function addAccount(event: React.FormEvent) {
    event.preventDefault();
    try {
      await api<Account>("/api/v1/steam-accounts", {
        method: "POST",
        csrf: true,
        body: JSON.stringify({ label, display_name: displayName, steam_id: steamId || undefined, ownership_attested: ownershipAttested })
      });
      toast.success("Account added");
      setLabel("");
      setDisplayName("");
      setSteamId("");
      setOwnershipAttested(false);
      await refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to add account");
    }
  }

  async function requestAccountLogin(account: Account, steamGuardCode?: string) {
    return api<Account>(`/api/v1/steam-accounts/${account.id}/login`, {
      method: "POST",
      csrf: true,
      body: JSON.stringify(steamGuardCode ? { steam_guard_code: steamGuardCode } : {})
    });
  }

  async function loginAccount(account: Account) {
    try {
      await requestAccountLogin(account);
      toast.success("Account is online");
      await refresh();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Login failed";
      if (message.toLowerCase().includes("steam guard code required")) {
        setGuardAccount(account);
        setGuardCode("");
        return;
      }
      toast.error(message);
    }
  }

  async function submitSteamGuard(event: React.FormEvent) {
    event.preventDefault();
    if (!guardAccount) return;
    setGuardSubmitting(true);
    try {
      await requestAccountLogin(guardAccount, guardCode);
      toast.success("Account is online");
      setGuardAccount(null);
      setGuardCode("");
      await refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Steam Guard verification failed");
    } finally {
      setGuardSubmitting(false);
    }
  }

  async function openGames(account: Account) {
    setSelectedAccount(account);
    setGames(await api<Game[]>(`/api/v1/games/${account.id}`));
  }

  async function saveGames() {
    if (!selectedAccount) return;
    const app_ids = games.filter((game) => game.selected).map((game) => game.app_id);
    await api<Game[]>(`/api/v1/games/${selectedAccount.id}`, { method: "PUT", csrf: true, body: JSON.stringify({ app_ids }) });
    toast.success("Games saved");
    await refresh();
  }

  async function startSession(account: Account) {
    try {
      await api<Session>("/api/v1/sessions", { method: "POST", csrf: true, body: JSON.stringify({ account_id: account.id }) });
      toast.success("Session requested");
      await refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Session start failed");
    }
  }

  async function stopSession(session: Session) {
    try {
      await api<Session>(`/api/v1/sessions/${session.id}/stop`, { method: "POST", csrf: true });
      toast.success("Session stopped");
      await refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Session stop failed");
    }
  }

  async function recoverSession(session: Session) {
    try {
      const account = accounts.find((item) => item.id === session.account_id);
      if (account && account.status !== "online") {
        await api<Account>(`/api/v1/steam-accounts/${session.account_id}/login`, { method: "POST", csrf: true, body: JSON.stringify({}) });
      }
      await api<Session>("/api/v1/sessions", { method: "POST", csrf: true, body: JSON.stringify({ account_id: session.account_id }) });
      toast.success("Recovery started");
      await refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Recovery failed");
    }
  }

  async function deleteAccount(account: Account) {
    await api(`/api/v1/steam-accounts/${account.id}`, { method: "DELETE", csrf: true });
    toast.success("Account deleted");
    await refresh();
  }

  const filteredGames = useMemo(() => games.filter((game) => game.name.toLowerCase().includes(gameQuery.toLowerCase())), [games, gameQuery]);
  const activeSessions = sessions.filter((session) => activeStatuses.has(session.status));
  const onboardingSteps = [
    { title: "Create workspace", done: Boolean(currentUser), text: "Your DeckPilot account is active." },
    { title: "Verify email", done: Boolean(currentUser?.email_verified), text: currentUser?.email ? "Confirm recovery email." : "Add an email in settings." },
    { title: "Add owned account", done: accounts.length > 0, text: "Link or create a safe demo account record." },
    { title: "Review plan limits", done: Boolean(overview?.subscription_status), text: `${overview?.subscription_plan || "trial"} plan is visible.` },
    { title: "Start demo session", done: activeSessions.length > 0, text: "Manual transparent sessions appear here." }
  ];

  return (
    <div className="grid gap-6">
      {loading && <DashboardSkeleton />}
      {loadError && (
        <Card className="flex flex-wrap items-center justify-between gap-4 border-rose-400/20 bg-rose-500/10">
          <div>
            <CardTitle>Dashboard unavailable</CardTitle>
            <p className="mt-2 text-sm leading-6 text-rose-100/80">{loadError}</p>
          </div>
          <Button variant="ghost" onClick={() => refresh()}>Retry</Button>
        </Card>
      )}

      <Card className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-sm font-semibold text-emerald-200">Launch checklist</div>
            <CardTitle className="mt-1">Get workspace-ready in a few steps</CardTitle>
          </div>
          <Badge className="border-emerald-300/30 text-emerald-200">
            {onboardingSteps.filter((step) => step.done).length}/{onboardingSteps.length} complete
          </Badge>
        </div>
        <div className="grid gap-3 md:grid-cols-5">
          {onboardingSteps.map((step) => (
            <div key={step.title} className={`rounded-xl border p-3 ${step.done ? "border-emerald-300/20 bg-emerald-300/10" : "border-white/10 bg-white/5"}`}>
              <div className="text-sm font-bold">{step.title}</div>
              <div className="mt-2 text-xs leading-5 text-slate-400">{step.text}</div>
            </div>
          ))}
        </div>
      </Card>

      <section className="grid gap-4 md:grid-cols-4">
        {[
          ["Accounts", overview?.accounts_count ?? "-"],
          ["Online sessions", `${overview?.online_sessions ?? 0}/${overview?.active_session_limit ?? "-"}`],
          ["Active games", overview?.active_games ?? "-"],
          ["Subscription", overview?.subscription_status ?? "-"]
        ].map(([itemLabel, value]) => (
          <motion.div key={itemLabel} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            <Card>
              <div className="text-xs font-semibold uppercase text-slate-400">{itemLabel}</div>
              <div className="mt-3 text-3xl font-black">{value}</div>
            </Card>
          </motion.div>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <Card className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle>Steam accounts</CardTitle>
              <p className="text-sm text-slate-400">Owner-only access, encrypted credentials, visible status.</p>
            </div>
          </div>
          <form className="grid gap-3 md:grid-cols-4" onSubmit={addAccount}>
            <Input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Label" required />
            <Input value={displayName} onChange={(e) => setDisplayName(e.target.value)} placeholder="Display name" autoComplete="off" required />
            <Input value={steamId} onChange={(e) => setSteamId(e.target.value)} placeholder="SteamID64 (optional)" autoComplete="off" />
            <Button type="submit" disabled={!ownershipAttested}>Add account</Button>
            <label className="md:col-span-4 flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 p-3 text-sm text-slate-300">
              <input className="mt-1" type="checkbox" checked={ownershipAttested} onChange={(event) => setOwnershipAttested(event.target.checked)} required />
              <span>I confirm this is my own Steam account. Demo mode does not require a Steam password.</span>
            </label>
          </form>
          <div className="grid gap-3">
            {accounts.length === 0 && <Empty title="No accounts yet" text="Add a Steam account you own. Test mode uses the safe mock adapter." />}
            {accounts.map((account) => (
              <div key={account.id} className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-bold">{account.label}</div>
                    <div className="text-xs text-slate-400">
                      SteamID64: {account.steamid64 || "not connected"} / selected games: {account.selected_games_count}
                    </div>
                  </div>
                  <Badge className={statusClass(account.status)}>{account.status}</Badge>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button variant="ghost" onClick={() => loginAccount(account)}>Login</Button>
                  <Button variant="ghost" onClick={() => openGames(account)}>Games</Button>
                  <Button variant="success" onClick={() => startSession(account)}>
                    <Activity className="h-4 w-4" />
                    Start
                  </Button>
                  <Button variant="danger" onClick={() => deleteAccount(account)}>Delete</Button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <div className="grid gap-6">
          <Card>
            <div className="flex items-center justify-between gap-3">
              <CardTitle>Active sessions</CardTitle>
              <Badge>{activeSessions.length} active</Badge>
            </div>
            <div className="mt-4 grid gap-3">
              {sessions.length === 0 && <Empty title="No sessions" text="Sessions are started manually and recorded with visible lifecycle events." />}
              {sessions.map((session) => (
                <div key={session.id} className="rounded-xl border border-white/10 bg-white/5 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="font-semibold">Session #{session.id}</div>
                      <div className="text-xs text-slate-500">Account {session.account_id} / games {session.current_games.join(", ") || "-"}</div>
                    </div>
                    <Badge className={statusClass(session.status)}>{session.status}</Badge>
                  </div>
                  <div className="mt-3 grid gap-2 text-xs text-slate-400">
                    <div className="flex items-center gap-2">
                      <Clock3 className="h-3.5 w-3.5" />
                      heartbeat {formatTime(session.last_heartbeat_at)}
                    </div>
                    {session.error_message && (
                      <div className="flex items-start gap-2 rounded-lg border border-rose-300/20 bg-rose-300/10 p-2 text-rose-100">
                        <AlertTriangle className="mt-0.5 h-3.5 w-3.5" />
                        <span>{session.error_message}</span>
                      </div>
                    )}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {activeStatuses.has(session.status) && (
                      <Button variant="ghost" onClick={() => stopSession(session)}>
                        <Square className="h-4 w-4" />
                        Stop
                      </Button>
                    )}
                    {session.status === "error" && (
                      <Button variant="ghost" onClick={() => recoverSession(session)}>
                        <RotateCcw className="h-4 w-4" />
                        Retry
                      </Button>
                    )}
                  </div>
                  <div className="mt-3 grid gap-2 border-t border-white/10 pt-3">
                    {(sessionEvents[session.id] || []).slice(0, 4).map((event) => (
                      <div key={event.id} className="rounded-lg bg-black/15 p-2 text-xs">
                        <div className="font-semibold text-slate-200">{event.event_type}</div>
                        <div className="text-slate-400">{event.message}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <Card>
            <CardTitle>Recent activity</CardTitle>
            <div className="mt-4 grid gap-3">
              {overview?.recent_activity?.length ? overview.recent_activity.map((item, index) => (
                <div key={`${item.action}-${item.target_id}-${item.created_at}-${index}`} className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm">
                  <div className="font-semibold">{item.action}</div>
                  <div className="text-slate-400">{item.target_type} #{item.target_id}</div>
                </div>
              )) : <Empty title="Activity log is empty" text="Account, session, billing, and admin actions will appear here." />}
            </div>
          </Card>
        </div>
      </section>

      {selectedAccount && (
        <Card className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle>Game picker / {selectedAccount.label}</CardTitle>
              <p className="text-sm text-slate-400">Search and save games through the Steam integration abstraction.</p>
            </div>
            <Button onClick={saveGames}>Save selection</Button>
          </div>
          <Input value={gameQuery} onChange={(e) => setGameQuery(e.target.value)} placeholder="Search games" />
          <div className="grid gap-2 md:grid-cols-2">
            {filteredGames.map((game) => (
              <label key={game.app_id} className="flex cursor-pointer items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-3 text-sm">
                <input
                  type="checkbox"
                  checked={game.selected}
                  onChange={() => setGames((items) => items.map((item) => item.app_id === game.app_id ? { ...item, selected: !item.selected } : item))}
                />
                {game.name}
              </label>
            ))}
          </div>
        </Card>
      )}

      {guardAccount && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4 backdrop-blur-lg">
          <form className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-950/95 p-5 shadow-glow" onSubmit={submitSteamGuard}>
            <CardTitle>Steam Guard</CardTitle>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Enter the one-time code for {guardAccount.label}. The code is used only for this login attempt.
            </p>
            <Input
              className="mt-4"
              value={guardCode}
              onChange={(event) => setGuardCode(event.target.value)}
              placeholder="Steam Guard code"
              autoComplete="one-time-code"
              maxLength={32}
              required
            />
            <div className="mt-5 flex justify-end gap-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setGuardAccount(null);
                  setGuardCode("");
                }}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={guardSubmitting}>
                {guardSubmitting ? "Checking..." : "Continue"}
              </Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function Empty({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-white/15 bg-white/[0.03] p-6 text-center">
      <div className="font-semibold">{title}</div>
      <p className="mt-2 text-sm text-slate-400">{text}</p>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="h-28 rounded-2xl border border-white/10 skeleton-shimmer" />
      ))}
    </div>
  );
}
