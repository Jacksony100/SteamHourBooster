"use client";

import { matchesToNextLevel, nextLevelProgress } from "./lib";
import type { FaceitResult } from "./types";

function Fact({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.03] p-3 text-center">
      <div className="font-display text-lg font-bold text-white">{value}</div>
      <div className="mt-0.5 text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
    </div>
  );
}

export function QuickFacts({ result }: { result: FaceitResult }) {
  const elos = result.elo_history.map((p) => p.elo);
  const peak = elos.length ? Math.max(...elos) : null;
  const low = elos.length ? Math.min(...elos) : null;
  const mapsPlayed = new Set(result.matches.map((m) => m.map).filter(Boolean)).size;
  const prog = nextLevelProgress(result.faceit_elo);
  const toLevel = matchesToNextLevel(prog?.toNext);

  const facts: { label: string; value: React.ReactNode }[] = [];
  if (peak != null) facts.push({ label: "Peak ELO", value: peak });
  if (low != null && peak != null && low !== peak) facts.push({ label: "ELO range", value: `${low}–${peak}` });
  if (mapsPlayed) facts.push({ label: "Maps played", value: mapsPlayed });
  if (toLevel && prog?.nextElo) facts.push({ label: `To level ${prog.level + 1}`, value: `~${toLevel} wins` });

  if (facts.length < 2) return null;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {facts.map((f) => <Fact key={f.label} label={f.label} value={f.value} />)}
    </div>
  );
}

export function WinLossDonut({ wins, total }: { wins: number; total: number }) {
  if (total <= 0) return null;
  const losses = total - wins;
  const pct = wins / total;
  const r = 42;
  const c = 2 * Math.PI * r;
  return (
    <div className="premium-card flex items-center gap-5 rounded-xl p-4">
      <svg viewBox="0 0 120 120" className="h-28 w-28" role="img" aria-label={`${wins} wins, ${losses} losses`}>
        <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,92,122,0.4)" strokeWidth="14" />
        <circle cx="60" cy="60" r={r} fill="none" stroke="#3DF5A0" strokeWidth="14" strokeLinecap="round" strokeDasharray={`${c * pct} ${c}`} transform="rotate(-90 60 60)" />
        <text x="60" y="60" textAnchor="middle" dominantBaseline="central" fill="#eaf0fa" fontSize="22" fontWeight="700">{Math.round(pct * 100)}%</text>
      </svg>
      <div>
        <div className="text-xs uppercase tracking-wide text-slate-400">Recent win rate</div>
        <div className="mt-1 flex gap-4 text-sm">
          <span className="text-emerald-400">{wins} W</span>
          <span className="text-rose-400">{losses} L</span>
        </div>
      </div>
    </div>
  );
}
