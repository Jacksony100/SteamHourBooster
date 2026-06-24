"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ExternalLink, LayoutGrid, Search, Star } from "lucide-react";

import { useI18n } from "./i18n";
import { mapLabel, relativeDate, toNum } from "./lib";
import { MatchModal } from "./match-modal";
import { PerfBars } from "./perf-chart";
import type { FaceitMatch } from "./types";

type Filter = "all" | "win" | "loss";
type Sort = "recent" | "kills" | "adr";

function MiniStat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md bg-white/[0.04] px-2 py-1.5 text-center">
      <div className="text-sm font-semibold text-white">{value ?? "—"}</div>
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
    </div>
  );
}

export function MatchList({ matches, playerId }: { matches: FaceitMatch[]; playerId: string | null }) {
  const { t } = useI18n();
  const [open, setOpen] = useState<string | null>(null);
  const [modal, setModal] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [sort, setSort] = useState<Sort>("recent");
  const [mapQuery, setMapQuery] = useState("");

  const shown = useMemo(() => {
    let list = matches.filter((m) => (filter === "all" ? true : m.result === filter));
    if (mapQuery.trim()) {
      const q = mapQuery.trim().toLowerCase();
      list = list.filter((m) => (m.map ?? "").toLowerCase().includes(q));
    }
    if (sort === "kills") list = [...list].sort((a, b) => (toNum(b.kills) ?? 0) - (toNum(a.kills) ?? 0));
    else if (sort === "adr") list = [...list].sort((a, b) => (toNum(b.adr) ?? 0) - (toNum(a.adr) ?? 0));
    return list;
  }, [matches, filter, sort, mapQuery]);

  if (!matches.length) return null;
  const chrono = [...matches].reverse();
  const series = (key: keyof FaceitMatch) => chrono.map((m) => ({ value: toNum(m[key] as string) ?? NaN, win: m.result === "win" }));
  const charts: { label: string; key: keyof FaceitMatch; threshold?: number; fixed: number }[] = [
    { label: "K/D", key: "kd_ratio", threshold: 1, fixed: 2 },
    { label: "ADR", key: "adr", threshold: 70, fixed: 0 },
    { label: "Kills", key: "kills", threshold: 18, fixed: 0 },
    { label: "HS%", key: "headshots", threshold: 50, fixed: 0 },
  ];

  const FILTERS: { v: Filter; label: string }[] = [
    { v: "all", label: t("matches") }, { v: "win", label: "W" }, { v: "loss", label: "L" },
  ];

  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        {charts.map((c) => {
          const pts = series(c.key);
          return pts.filter((p) => Number.isFinite(p.value)).length >= 2 ? (
            <div key={c.label} className="premium-card rounded-xl p-4"><PerfBars points={pts} label={c.label} threshold={c.threshold} fixed={c.fixed} /></div>
          ) : null;
        })}
      </div>

      <div className="premium-card rounded-xl p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="mr-auto text-xs uppercase tracking-wide text-slate-400">{t("lastMatches")} · {shown.length}/{matches.length}</span>
          <div className="inline-flex rounded-lg border border-white/10 p-0.5 text-xs">
            {FILTERS.map((f) => (
              <button key={f.v} onClick={() => setFilter(f.v)} className={`rounded-md px-2 py-1 font-semibold ${filter === f.v ? "bg-white/10 text-white" : "text-slate-400"}`}>{f.label}</button>
            ))}
          </div>
          <select value={sort} onChange={(e) => setSort(e.target.value as Sort)} className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-200 outline-none">
            <option value="recent">Recent</option>
            <option value="kills">Kills</option>
            <option value="adr">ADR</option>
          </select>
          <div className="relative">
            <Search className="pointer-events-none absolute left-2 top-1.5 h-3.5 w-3.5 text-slate-500" />
            <input value={mapQuery} onChange={(e) => setMapQuery(e.target.value)} placeholder="map" className="w-24 rounded-lg border border-white/10 bg-white/5 py-1 pl-7 pr-2 text-xs text-white outline-none focus:border-sky-400/60" />
          </div>
        </div>

        <div className="space-y-1.5">
          {shown.map((m, i) => {
            const id = m.match_id ?? String(i);
            const isOpen = open === id;
            const win = m.result === "win";
            const ace = (toNum(m.penta_kills) ?? 0) > 0;
            const mvp = (toNum(m.mvps) ?? 0) > 0;
            return (
              <div key={id} className="rounded-lg border border-white/5 bg-white/[0.03]">
                <button onClick={() => setOpen(isOpen ? null : id)} className="flex w-full items-center gap-3 px-3 py-2 text-left text-sm" aria-expanded={isOpen}>
                  <span className="grid h-6 w-6 shrink-0 place-items-center rounded text-xs font-bold" style={win ? { background: "rgba(61,245,160,.15)", color: "#3DF5A0" } : { background: "rgba(255,92,122,.15)", color: "#FF5C7A" }}>
                    {win ? "W" : m.result === "loss" ? "L" : "?"}
                  </span>
                  <span className="flex w-24 shrink-0 items-center gap-1 truncate font-medium text-white">
                    {m.map ? mapLabel(m.map) : "—"}
                    {ace && <span title="Ace" className="text-[10px] text-rose-400">ACE</span>}
                    {mvp && <Star className="h-3 w-3 text-amber-300" aria-label="MVP" />}
                  </span>
                  <span className="w-14 shrink-0 text-slate-400">{m.score ?? ""}</span>
                  <span className="flex-1 text-right text-slate-300">{m.kills ?? "—"}/{m.deaths ?? "—"}/{m.assists ?? "—"} <span className="text-slate-500">({m.kd_ratio ?? "—"})</span></span>
                  <span className="hidden w-16 shrink-0 text-right text-xs text-slate-500 sm:block" title={m.date ?? ""}>{relativeDate(m.date)}</span>
                  <ChevronDown className={`h-4 w-4 shrink-0 text-slate-500 transition ${isOpen ? "rotate-180" : ""}`} />
                </button>
                {isOpen && (
                  <div className="border-t border-white/5 px-3 py-3">
                    <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
                      <MiniStat label="ADR" value={m.adr} />
                      <MiniStat label="HS%" value={m.headshots} />
                      <MiniStat label="K/R" value={m.kr_ratio} />
                      <MiniStat label="MVP" value={m.mvps} />
                      <MiniStat label="3K+" value={m.triple_kills} />
                      <MiniStat label="Clutch" value={m.clutches} />
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {m.match_id && <button onClick={() => setModal(m.match_id)} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1 text-xs text-slate-200 hover:border-white/25"><LayoutGrid className="h-3.5 w-3.5" /> Scoreboard</button>}
                      {m.faceit_url && <a href={m.faceit_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1 text-xs text-sky-300 hover:border-white/25">FACEIT <ExternalLink className="h-3 w-3" /></a>}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
          {shown.length === 0 && <div className="py-4 text-center text-sm text-slate-500">No matches match the filter.</div>}
        </div>
      </div>

      {modal && <MatchModal matchId={modal} highlightId={playerId} onClose={() => setModal(null)} />}
    </div>
  );
}
