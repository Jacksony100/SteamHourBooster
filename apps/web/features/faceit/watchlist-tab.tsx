"use client";

import { Search, X } from "lucide-react";

import { flag } from "./lib";
import { useI18n } from "./i18n";
import { useWatch } from "./watchlist-context";

export function WatchlistTab({ onPick }: { onPick: (nickname: string) => void }) {
  const { t } = useI18n();
  const { items, toggle, mode } = useWatch();

  if (mode === "loading") return <div className="mt-8 text-center text-slate-400">…</div>;
  if (!items.length) {
    return <div className="mt-8 rounded-xl border border-shb-border bg-white/[0.035] p-6 text-center text-slate-300">{t("watchEmpty")}</div>;
  }

  return (
    <div className="mt-8 space-y-2">
      {mode === "local" && <p className="text-xs text-slate-500">Saved on this device. Sign in to sync your watchlist.</p>}
      {items.map((w) => (
        <div key={w.player_id} className="premium-card flex items-center gap-3 rounded-xl px-4 py-3">
          <span className="text-lg">{flag(w.country)}</span>
          <span className="flex-1 truncate font-medium text-white">{w.nickname ?? w.player_id.slice(0, 10)}</span>
          {w.nickname && (
            <button onClick={() => onPick(w.nickname!)} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1 text-sm text-slate-200 hover:border-white/25">
              <Search className="h-3.5 w-3.5" /> {t("find")}
            </button>
          )}
          <button onClick={() => toggle(w)} className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-rose-300" aria-label="Remove">
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
