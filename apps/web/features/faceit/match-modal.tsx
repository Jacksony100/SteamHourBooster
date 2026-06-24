"use client";

import { useEffect, useRef, useState } from "react";
import { X } from "lucide-react";

import { api } from "@/lib/api";

import { mapLabel } from "./lib";
import type { FaceitScoreboard, FaceitScoreTeam } from "./types";

function TeamTable({ team, highlightId }: { team: FaceitScoreTeam; highlightId?: string | null }) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="font-semibold text-white">{team.name}</span>
        <span
          className="rounded px-2 py-0.5 text-xs font-bold"
          style={team.win ? { background: "rgba(61,245,160,.15)", color: "#3DF5A0" } : { background: "rgba(255,92,122,.15)", color: "#FF5C7A" }}
        >
          {team.win ? "WIN" : "LOSS"} {team.score ?? ""}
        </span>
      </div>
      <div className="space-y-0.5">
        <div className="grid grid-cols-[1fr_auto_auto_auto] gap-2 px-2 text-[10px] uppercase tracking-wide text-slate-500">
          <span>Player</span><span className="w-16 text-right">K / D / A</span><span className="w-10 text-right">K/D</span><span className="w-12 text-right">ADR</span>
        </div>
        {team.players.map((p, i) => {
          const me = highlightId && p.player_id === highlightId;
          return (
            <div key={p.player_id ?? i} className={`grid grid-cols-[1fr_auto_auto_auto] gap-2 rounded px-2 py-1 text-sm ${me ? "bg-sky-400/10" : ""}`}>
              <span className={`truncate ${me ? "font-semibold text-sky-200" : "text-white"}`}>{p.nickname ?? "—"}</span>
              <span className="w-16 text-right text-slate-300">{p.kills ?? "–"}/{p.deaths ?? "–"}/{p.assists ?? "–"}</span>
              <span className="w-10 text-right text-slate-400">{p.kd_ratio ?? "–"}</span>
              <span className="w-12 text-right text-slate-400">{p.adr ?? "–"}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function MatchModal({ matchId, highlightId, onClose }: { matchId: string; highlightId?: string | null; onClose: () => void }) {
  const [board, setBoard] = useState<FaceitScoreboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    api<FaceitScoreboard>(`/faceit/match/${matchId}`)
      .then((b) => alive && setBoard(b))
      .catch((e) => alive && setError(e instanceof Error ? e.message : "Failed to load match"))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
  }, [matchId]);

  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onCloseRef.current(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={onClose} role="dialog" aria-modal="true">
      <div className="w-full max-w-2xl rounded-2xl border border-shb-border bg-shb-bg-2 p-5 shadow-glass" onClick={(e) => e.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between">
          <div className="text-lg font-bold text-white">
            {board?.map ? mapLabel(board.map) : "Match"} <span className="ml-2 text-sm font-normal text-slate-400">{board?.score ?? ""}</span>
          </div>
          <button onClick={onClose} className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white" aria-label="Close">
            <X className="h-5 w-5" />
          </button>
        </div>
        {loading && <div className="py-10 text-center text-slate-400">Loading scoreboard…</div>}
        {error && <div className="rounded-lg border border-shb-danger/30 bg-shb-danger/10 p-4 text-rose-50">{error}</div>}
        {board && (
          <div className="grid gap-3 sm:grid-cols-2">
            {board.teams.map((t, i) => <TeamTable key={i} team={t} highlightId={highlightId} />)}
          </div>
        )}
      </div>
    </div>
  );
}
