"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui-kit/empty-state";
import { ErrorState } from "@/components/ui-kit/error-state";
import { LoadingSkeleton } from "@/components/ui-kit/loading-skeleton";
import { StatusBadge } from "@/components/ui-kit/status-badge";
import { SteamAvatar } from "@/components/ui-kit/steam-avatar";
import { listAccounts, type SteamAccount } from "@/lib/accounts";
import { getSteamProfile, refreshSteamProfile, type SteamProfile } from "@/lib/steam";
import type { StatusTone } from "@/lib/design-tokens";

function errMessage(e: unknown) {
  return e instanceof Error ? e.message : "Request failed";
}

const TONE: Record<string, StatusTone> = { online: "online", offline: "offline", starting: "session", error: "error" };

export function AccountsClient() {
  const [accounts, setAccounts] = useState<SteamAccount[]>([]);
  const [profiles, setProfiles] = useState<Record<number, SteamProfile>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAccounts()
      .then(async (rows) => {
        setAccounts(rows);
        const entries = await Promise.all(
          rows.map(async (a) => {
            try {
              return [a.id, await getSteamProfile(a.id)] as const;
            } catch {
              return null;
            }
          })
        );
        setProfiles(Object.fromEntries(entries.filter((e): e is readonly [number, SteamProfile] => e !== null)));
      })
      .catch((e) => setError(errMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  async function refreshProfile(accountId: number) {
    try {
      const profile = await refreshSteamProfile(accountId);
      setProfiles((prev) => ({ ...prev, [accountId]: profile }));
      toast.success("Steam profile refreshed");
    } catch (e) {
      toast.error(errMessage(e));
    }
  }

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <LoadingSkeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    );
  }
  if (error) return <ErrorState title="Could not load accounts" description={error} />;
  if (accounts.length === 0) {
    return (
      <EmptyState
        title="No Steam accounts"
        description="Add an account you own from the dashboard to manage it here."
        actionLabel="Go to dashboard"
        onAction={() => {
          window.location.href = "/dashboard";
        }}
      />
    );
  }

  return (
    <div className="space-y-3">
      {accounts.map((account) => {
        const profile = profiles[account.id];
        return (
          <div key={account.id} className="premium-card flex flex-wrap items-center gap-4 rounded-xl p-4">
            <SteamAvatar src={profile?.avatar_full} personaName={profile?.persona_name ?? account.label} size={52} online={profile?.persona_state ? profile.persona_state > 0 : undefined} />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate font-semibold text-white">{profile?.persona_name || account.label}</span>
                <StatusBadge tone={TONE[account.status] ?? "offline"}>{account.status}</StatusBadge>
              </div>
              <div className="truncate text-xs text-slate-400">
                {account.steamid64 ? `SteamID ${account.steamid64}` : "Not linked"} · {account.selected_games_count} games selected
                {profile?.visibility === "private" && " · profile private"}
              </div>
            </div>
            <Button variant="ghost" onClick={() => refreshProfile(account.id)}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        );
      })}
    </div>
  );
}
