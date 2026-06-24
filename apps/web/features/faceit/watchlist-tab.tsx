"use client";

import { useRef } from "react";
import { toast } from "sonner";
import { Download, Search, Swords, Upload, X } from "lucide-react";

import { flag } from "./lib";
import { useI18n } from "./i18n";
import type { WatchItem } from "./types";
import { useWatch } from "./watchlist-context";

export function WatchlistTab({ onPick, onCompareAll }: { onPick: (nickname: string) => void; onCompareAll: (nicks: string[]) => void }) {
  const { lang } = useI18n();
  const { items, toggle, mode } = useWatch();
  const fileRef = useRef<HTMLInputElement>(null);

  function exportList() {
    try {
      const blob = new Blob([JSON.stringify(items, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "faceit-watchlist.json";
      a.click();
      URL.revokeObjectURL(a.href);
    } catch { /* ignore */ }
  }

  async function importList(file: File) {
    try {
      const data = JSON.parse(await file.text());
      if (!Array.isArray(data)) throw new Error();
      let added = 0;
      for (const raw of data as WatchItem[]) {
        if (raw?.player_id && !items.some((i) => i.player_id === raw.player_id)) {
          await toggle({ player_id: raw.player_id, nickname: raw.nickname ?? null, country: raw.country ?? null });
          added++;
        }
      }
      toast.success(`Imported ${added}`);
    } catch {
      toast.error("Invalid watchlist file");
    }
  }

  const nicks = items.map((w) => w.nickname).filter((n): n is string => !!n);

  if (mode === "loading") return <div className="mt-8 text-center text-slate-400">…</div>;

  return (
    <div className="mt-8 space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="mr-auto text-sm text-slate-400">{items.length} {lang === "ru" ? "в избранном" : "watched"}</span>
        {nicks.length >= 2 && (
          <button onClick={() => onCompareAll(nicks.slice(0, 5))} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1.5 text-sm text-slate-200 hover:border-white/25">
            <Swords className="h-3.5 w-3.5" /> {lang === "ru" ? "Сравнить всех" : "Compare all"}
          </button>
        )}
        {items.length > 0 && <button onClick={exportList} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1.5 text-sm text-slate-200 hover:border-white/25"><Download className="h-3.5 w-3.5" /> Export</button>}
        <button onClick={() => fileRef.current?.click()} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1.5 text-sm text-slate-200 hover:border-white/25"><Upload className="h-3.5 w-3.5" /> Import</button>
        <input ref={fileRef} type="file" accept="application/json" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) importList(f); e.target.value = ""; }} />
      </div>

      {mode === "local" && <p className="text-xs text-slate-500">Saved on this device. Sign in to sync your watchlist.</p>}

      {!items.length ? (
        <div className="rounded-xl border border-shb-border bg-white/[0.035] p-6 text-center text-slate-300">{lang === "ru" ? "Список пуст. Найдите игрока и нажмите «В избранное»." : "Empty. Look a player up and hit Watch."}</div>
      ) : (
        items.map((w) => (
          <div key={w.player_id} className="premium-card flex items-center gap-3 rounded-xl px-4 py-3">
            <span className="text-lg">{flag(w.country)}</span>
            <span className="flex-1 truncate font-medium text-white">{w.nickname ?? w.player_id.slice(0, 10)}</span>
            {w.nickname && (
              <button onClick={() => onPick(w.nickname!)} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1 text-sm text-slate-200 hover:border-white/25">
                <Search className="h-3.5 w-3.5" /> {lang === "ru" ? "Найти" : "Find"}
              </button>
            )}
            <button onClick={() => toggle(w)} className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-rose-300" aria-label="Remove"><X className="h-4 w-4" /></button>
          </div>
        ))
      )}
    </div>
  );
}
