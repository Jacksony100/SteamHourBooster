"use client";

import { Users } from "lucide-react";

import { useI18n } from "./i18n";
import type { FaceitTeammate } from "./types";

export function Teammates({ teammates, onPick }: { teammates: FaceitTeammate[]; onPick?: (nickname: string) => void }) {
  const { t } = useI18n();
  if (!teammates.length) return null;
  return (
    <div className="premium-card rounded-xl p-4">
      <div className="mb-3 flex items-center gap-1.5 text-xs uppercase tracking-wide text-slate-400">
        <Users className="h-3.5 w-3.5" /> {t("teammates")}
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {teammates.map((m) => {
          const wr = m.win_rate ? Number(m.win_rate) : null;
          const inner = (
            <>
              <span className="truncate font-medium text-white">{m.nickname ?? m.player_id.slice(0, 8)}</span>
              <span className="shrink-0 text-xs text-slate-400">
                {m.games} games ·{" "}
                <span style={wr != null ? { color: wr >= 50 ? "#3DF5A0" : "#FF5C7A" } : undefined}>{m.win_rate ?? "—"}% WR</span>
              </span>
            </>
          );
          const cls = "flex items-center justify-between gap-2 rounded-lg border border-white/5 bg-white/[0.03] px-3 py-2 text-left";
          return onPick && m.nickname ? (
            <button key={m.player_id} onClick={() => onPick(m.nickname!)} className={`${cls} transition hover:border-white/20`}>
              {inner}
            </button>
          ) : (
            <div key={m.player_id} className={cls}>{inner}</div>
          );
        })}
      </div>
    </div>
  );
}
