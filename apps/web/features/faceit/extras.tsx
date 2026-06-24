"use client";

import { mapLabel, toNum } from "./lib";
import type { FaceitMatch, FaceitMap } from "./types";

const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function WinLossStrip({ matches }: { matches: FaceitMatch[] }) {
  const played = [...matches].reverse().filter((m) => m.result === "win" || m.result === "loss");
  if (played.length < 3) return null;
  return (
    <div className="premium-card rounded-xl p-4">
      <div className="mb-2 text-xs uppercase tracking-wide text-slate-400">Form · last {played.length}</div>
      <div className="flex flex-wrap gap-1">
        {played.map((m, i) => (
          <span
            key={i}
            title={m.map ? mapLabel(m.map) : ""}
            className="h-6 flex-1 min-w-[10px] rounded-sm"
            style={{ background: m.result === "win" ? "#3DF5A0" : "#FF5C7A", opacity: 0.85 }}
          />
        ))}
      </div>
    </div>
  );
}

export function ActivityHeatmap({ activity }: { activity: number[] }) {
  const max = Math.max(...activity, 1);
  if (activity.reduce((a, b) => a + b, 0) < 3) return null;
  return (
    <div className="premium-card rounded-xl p-4">
      <div className="mb-3 text-xs uppercase tracking-wide text-slate-400">Activity · weekday</div>
      <div className="flex items-end justify-between gap-2" style={{ height: 90 }}>
        {activity.map((c, i) => (
          <div key={i} className="flex flex-1 flex-col items-center justify-end gap-1">
            <div className="w-full rounded-t" style={{ height: `${Math.max(4, (c / max) * 70)}px`, background: "#2e8bff", opacity: c ? 0.4 + 0.6 * (c / max) : 0.15 }} title={`${c}`} />
            <span className="text-[10px] text-slate-500">{DOW[i]}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MatchMini({ m, label, tone }: { m: FaceitMatch; label: string; tone: string }) {
  return (
    <div className="rounded-lg border p-3" style={{ borderColor: `${tone}33`, background: `${tone}0d` }}>
      <div className="text-[11px] uppercase tracking-wide" style={{ color: tone }}>{label}</div>
      <div className="mt-1 flex items-baseline justify-between">
        <span className="font-semibold text-white">{m.map ? mapLabel(m.map) : "—"}</span>
        <span className="text-sm text-slate-300">{m.kills ?? "—"}/{m.deaths ?? "—"}/{m.assists ?? "—"}</span>
      </div>
      <div className="mt-0.5 text-xs text-slate-400">{m.kd_ratio ?? "—"} K/D · {m.adr ?? "—"} ADR · {m.result === "win" ? "W" : "L"}</div>
    </div>
  );
}

export function BestWorst({ best, worst }: { best: FaceitMatch | null; worst: FaceitMatch | null }) {
  if (!best && !worst) return null;
  return (
    <div className="premium-card grid gap-3 rounded-xl p-4 sm:grid-cols-2">
      {best && <MatchMini m={best} label="Best recent" tone="#3DF5A0" />}
      {worst && <MatchMini m={worst} label="Worst recent" tone="#FF5C7A" />}
    </div>
  );
}

export function MapCharts({ maps }: { maps: FaceitMap[] }) {
  const rated = maps.map((m) => ({ ...m, wr: toNum(m.win_rate), n: toNum(m.matches) ?? 0 })).filter((m) => m.wr != null && m.n >= 1);
  if (rated.length < 2) return null;
  return (
    <div className="premium-card rounded-xl p-4">
      <div className="mb-3 text-xs uppercase tracking-wide text-slate-400">Win rate by map</div>
      <div className="space-y-2">
        {rated.map((m) => (
          <div key={m.name} className="flex items-center gap-3">
            <span className="w-20 shrink-0 truncate text-sm text-white">{mapLabel(m.name)}</span>
            <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full" style={{ width: `${m.wr}%`, background: m.wr! >= 50 ? "#3DF5A0" : "#FF5C7A" }} />
            </div>
            <span className="w-24 shrink-0 text-right text-xs text-slate-400">{m.wr}% · {m.kd_ratio ?? "—"} K/D</span>
          </div>
        ))}
      </div>
    </div>
  );
}
