"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, ExternalLink, Search } from "lucide-react";

import { api } from "@/lib/api";

type FaceitStats = {
  matches: string | null;
  win_rate: string | null;
  kd_ratio: string | null;
  headshots: string | null;
  avg_kills: string | null;
  mvps: string | null;
  current_win_streak: string | null;
  longest_win_streak: string | null;
  recent_results: string[];
};

type FaceitMap = {
  name: string;
  matches: string | null;
  win_rate: string | null;
  kd_ratio: string | null;
};

type FaceitMatch = {
  match_id: string | null;
  map: string | null;
  result: string | null;
  score: string | null;
  kills: string | null;
  deaths: string | null;
  kd_ratio: string | null;
  headshots: string | null;
  date: string | null;
  faceit_url: string | null;
};

type FaceitResult = {
  found: boolean;
  configured: boolean;
  steamid64: string | null;
  nickname: string | null;
  avatar: string | null;
  country: string | null;
  faceit_url: string | null;
  skill_level: number | null;
  faceit_elo: number | null;
  region: string | null;
  stats: FaceitStats;
  maps: FaceitMap[];
  matches: FaceitMatch[];
  message: string | null;
  source: string | null;
  detail_level: string;
};

function mapLabel(name: string) {
  return name.replace(/^de_/, "").replace(/\b\w/g, (c) => c.toUpperCase());
}

// Official FACEIT skill-level palette (1–10).
const LEVEL_COLORS: Record<number, string> = {
  1: "#EEEEEE", 2: "#1CE400", 3: "#1CE400", 4: "#FFC800", 5: "#FFC800",
  6: "#FFC800", 7: "#FFC800", 8: "#FF6309", 9: "#FF6309", 10: "#FE1F00",
};

function flag(country: string | null) {
  if (!country || country.length !== 2) return "";
  const base = 0x1f1e6;
  return String.fromCodePoint(...country.toUpperCase().split("").map((c) => base + c.charCodeAt(0) - 65));
}

function Stat({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="premium-card rounded-xl p-4 text-center">
      <div className="font-display text-2xl font-bold text-white">{value ?? "—"}</div>
      <div className="mt-1 text-xs uppercase tracking-wide text-slate-400">{label}</div>
    </div>
  );
}

export function FaceitClient() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FaceitResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api<FaceitResult>(`/faceit/find?steam=${encodeURIComponent(input.trim())}`);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lookup failed");
    } finally {
      setLoading(false);
    }
  }

  const level = result?.skill_level ?? 0;
  const levelColor = LEVEL_COLORS[level] ?? "#3A4253";

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-5 py-12">
      <Link href="/" className="mb-8 inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
        <ArrowLeft className="h-4 w-4" />
        Back to home
      </Link>

      <h1 className="font-display text-4xl font-bold">
        FACEIT <span className="text-gradient">Finder</span>
      </h1>
      <p className="mt-2 max-w-xl text-slate-400">
        Enter a FACEIT nickname, a Steam profile link, or a SteamID64 to look up full FACEIT CS2 stats — level, ELO,
        per-map breakdown and recent matches with K/D. No login required.
      </p>

      <form onSubmit={search} className="mt-6 flex flex-col gap-3 sm:flex-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="FACEIT nickname  ·  steamcommunity.com/id/...  ·  7656119..."
          className="flex-1 rounded-xl border border-shb-border bg-white/5 px-4 py-3 text-white outline-none focus:border-sky-400/60"
          aria-label="FACEIT nickname, Steam profile URL, or SteamID64"
        />
        <button type="submit" disabled={loading || !input.trim()} className="cta-gradient flex items-center justify-center gap-2 rounded-xl px-6 py-3 font-semibold text-white disabled:opacity-50">
          <Search className="h-4 w-4" />
          {loading ? "Searching..." : "Find"}
        </button>
      </form>

      {error && <div className="mt-6 rounded-xl border border-shb-danger/30 bg-shb-danger/10 p-4 text-rose-50" role="alert">{error}</div>}

      {result && !result.found && (
        <div className="mt-6 rounded-xl border border-shb-border bg-white/[0.035] p-6 text-center text-slate-300">
          {result.message ?? "No FACEIT profile found for this account."}
        </div>
      )}

      {result?.found && (
        <div className="mt-8 space-y-5">
          <div className="premium-card flex flex-wrap items-center gap-5 rounded-2xl p-6">
            {result.avatar ? (
              // eslint-disable-next-line @next/next/no-img-element -- external FACEIT CDN avatar
              <img src={result.avatar} alt={result.nickname ?? "avatar"} width={72} height={72} className="rounded-xl border border-white/10 object-cover" />
            ) : (
              <div className="grid h-[72px] w-[72px] place-items-center rounded-xl border border-white/10 bg-white/5 text-2xl text-slate-300">
                {(result.nickname ?? "?").charAt(0).toUpperCase()}
              </div>
            )}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 text-xl font-bold text-white">
                <span className="truncate">{result.nickname}</span>
                <span className="text-lg">{flag(result.country)}</span>
              </div>
              <div className="text-sm text-slate-400">
                {result.region && `Region ${result.region} · `}
                {result.faceit_elo != null && `${result.faceit_elo} ELO`}
              </div>
              {result.faceit_url && (
                <a href={result.faceit_url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-flex items-center gap-1.5 text-sm text-sky-300 hover:text-sky-200">
                  Open FACEIT profile <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
            <div className="grid place-items-center">
              <div
                className="grid h-16 w-16 place-items-center rounded-2xl font-display text-2xl font-black"
                style={{ background: `${levelColor}22`, color: levelColor, border: `2px solid ${levelColor}` }}
                title={`FACEIT level ${level}`}
              >
                {level || "?"}
              </div>
              <div className="mt-1 text-xs text-slate-400">Level</div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat label="Matches" value={result.stats.matches} />
            <Stat label="Win rate" value={result.stats.win_rate ? `${result.stats.win_rate}%` : null} />
            <Stat label="K/D" value={result.stats.kd_ratio} />
            <Stat label="Headshots" value={result.stats.headshots ? `${result.stats.headshots}%` : null} />
          </div>

          {result.stats.recent_results.length > 0 && (
            <div className="premium-card rounded-xl p-4">
              <div className="mb-2 text-xs uppercase tracking-wide text-slate-400">Recent results</div>
              <div className="flex gap-2">
                {result.stats.recent_results.map((r, i) => (
                  <span
                    key={i}
                    className="grid h-7 w-7 place-items-center rounded-lg text-xs font-bold"
                    style={r === "1" ? { background: "rgba(61,245,160,.15)", color: "#3DF5A0" } : { background: "rgba(255,92,122,.15)", color: "#FF5C7A" }}
                  >
                    {r === "1" ? "W" : "L"}
                  </span>
                ))}
              </div>
            </div>
          )}

          {result.maps.length > 0 && (
            <div className="premium-card rounded-xl p-4">
              <div className="mb-3 text-xs uppercase tracking-wide text-slate-400">By map</div>
              <div className="grid gap-2 sm:grid-cols-2">
                {result.maps.map((m) => (
                  <div key={m.name} className="flex items-center justify-between rounded-lg border border-white/5 bg-white/[0.03] px-3 py-2">
                    <span className="font-medium text-white">{mapLabel(m.name)}</span>
                    <span className="text-xs text-slate-400">
                      {m.matches ?? "—"} matches · {m.win_rate ? `${m.win_rate}% WR` : "—"} · {m.kd_ratio ?? "—"} K/D
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.matches.length > 0 && (
            <div className="premium-card rounded-xl p-4">
              <div className="mb-3 text-xs uppercase tracking-wide text-slate-400">Last {result.matches.length} matches</div>
              <div className="space-y-1.5">
                {result.matches.map((m, i) => (
                  <a
                    key={m.match_id ?? i}
                    href={m.faceit_url ?? undefined}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 rounded-lg border border-white/5 bg-white/[0.03] px-3 py-2 text-sm transition hover:border-white/15"
                  >
                    <span
                      className="grid h-6 w-6 shrink-0 place-items-center rounded text-xs font-bold"
                      style={m.result === "win" ? { background: "rgba(61,245,160,.15)", color: "#3DF5A0" } : { background: "rgba(255,92,122,.15)", color: "#FF5C7A" }}
                    >
                      {m.result === "win" ? "W" : m.result === "loss" ? "L" : "?"}
                    </span>
                    <span className="w-24 shrink-0 truncate font-medium text-white">{m.map ? mapLabel(m.map) : "—"}</span>
                    <span className="w-16 shrink-0 text-slate-400">{m.score ?? ""}</span>
                    <span className="flex-1 text-right text-slate-300">
                      {m.kills ?? "—"}/{m.deaths ?? "—"} <span className="text-slate-500">({m.kd_ratio ?? "—"} K/D)</span>
                    </span>
                    <span className="hidden w-20 shrink-0 text-right text-xs text-slate-500 sm:block">{m.date ?? ""}</span>
                  </a>
                ))}
              </div>
            </div>
          )}

          {result.detail_level === "basic" && (
            <p className="text-xs text-slate-500">
              Level &amp; ELO are exact. Detailed stats, per-map breakdown and match history require a free FACEIT API key
              on the server (keyless FACEIT stat endpoints are blocked by FACEIT&apos;s bot protection). Set
              <code className="mx-1 rounded bg-white/10 px-1">FACEIT_API_KEY</code> and restart the API for full data.
            </p>
          )}
        </div>
      )}
    </main>
  );
}
