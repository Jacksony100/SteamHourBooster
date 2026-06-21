"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui-kit/empty-state";
import { ErrorState } from "@/components/ui-kit/error-state";
import { GameImage } from "@/components/ui-kit/game-image";
import { LoadingSkeleton } from "@/components/ui-kit/loading-skeleton";
import { listAccounts, type SteamAccount } from "@/lib/accounts";
import { getOwnedGames, refreshOwnedGames, type OwnedGame } from "@/lib/steam";

function errMessage(e: unknown) {
  return e instanceof Error ? e.message : "Request failed";
}

function hours(minutes: number) {
  return `${Math.round((minutes / 60) * 10) / 10} h`;
}

export function GamesClient() {
  const [accounts, setAccounts] = useState<SteamAccount[]>([]);
  const [accountId, setAccountId] = useState<number | null>(null);
  const [games, setGames] = useState<OwnedGame[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    listAccounts()
      .then((rows) => {
        setAccounts(rows);
        setAccountId(rows[0]?.id ?? null);
        if (rows.length === 0) setLoading(false);
      })
      .catch((e) => {
        setError(errMessage(e));
        setLoading(false);
      });
  }, []);

  const load = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const result = await getOwnedGames(id);
      setGames(result.games);
    } catch (e) {
      setError(errMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (accountId != null) void load(accountId);
  }, [accountId, load]);

  async function refresh() {
    if (accountId == null) return;
    setRefreshing(true);
    try {
      const result = await refreshOwnedGames(accountId);
      setGames(result.games);
      toast.success("Steam library refreshed");
    } catch (e) {
      toast.error(errMessage(e));
    } finally {
      setRefreshing(false);
    }
  }

  if (accounts.length === 0 && !loading && !error) {
    return (
      <EmptyState
        title="No accounts yet"
        description="Add a Steam account you own to browse its library artwork."
        actionLabel="Go to accounts"
        onAction={() => {
          window.location.href = "/accounts";
        }}
      />
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label className="flex items-center gap-2 text-sm text-slate-300">
          Account
          <select
            value={accountId ?? ""}
            onChange={(e) => setAccountId(Number(e.target.value))}
            className="rounded-lg border border-shb-border bg-white/5 px-3 py-2 text-sm text-white"
          >
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.label}
              </option>
            ))}
          </select>
        </label>
        <Button variant="ghost" onClick={refresh} disabled={refreshing || accountId == null}>
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          Refresh Steam data
        </Button>
      </div>

      {error ? (
        <ErrorState title="Could not load games" description={error} actionLabel="Retry" onAction={() => accountId != null && load(accountId)} />
      ) : loading ? (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <LoadingSkeleton key={i} className="aspect-[616/353] w-full" />
          ))}
        </div>
      ) : games.length === 0 ? (
        <EmptyState title="No games found" description="This account's Steam library is empty or private." />
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {games.map((game) => (
            <div key={game.app_id} className="premium-card interactive-card overflow-hidden rounded-xl p-2">
              <GameImage appId={game.app_id} name={game.name} src={game.capsule_image_url} variant="capsule" />
              <div className="px-1 pb-1 pt-2">
                <div className="truncate text-sm font-semibold text-white">{game.name}</div>
                <div className="text-xs text-slate-400">{hours(game.playtime_forever)} played</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
