"use client";

import { toast } from "sonner";
import { Copy, ExternalLink, Table } from "lucide-react";

import { EloCompareChart } from "./elo-chart";
import { useI18n } from "./i18n";
import { LevelBadge, SERIES_COLORS, flag, toNum } from "./lib";
import { RadarChart } from "./radar-chart";
import { copyText, downloadCsv } from "./share";
import type { FaceitResult } from "./types";

type Metric = { label: string; num: (p: FaceitResult) => number | null; show: (p: FaceitResult) => string };

const METRICS: Metric[] = [
  { label: "ELO", num: (p) => p.faceit_elo, show: (p) => (p.faceit_elo != null ? String(p.faceit_elo) : "—") },
  { label: "Level", num: (p) => p.skill_level, show: (p) => (p.skill_level != null ? String(p.skill_level) : "—") },
  { label: "Matches", num: (p) => toNum(p.stats.matches), show: (p) => p.stats.matches ?? "—" },
  { label: "Win rate", num: (p) => toNum(p.stats.win_rate), show: (p) => (p.stats.win_rate ? `${p.stats.win_rate}%` : "—") },
  { label: "K/D", num: (p) => toNum(p.stats.kd_ratio), show: (p) => p.stats.kd_ratio ?? "—" },
  { label: "HS%", num: (p) => toNum(p.stats.headshots), show: (p) => (p.stats.headshots ? `${p.stats.headshots}%` : "—") },
  { label: "ADR", num: (p) => p.recent_form?.adr ?? null, show: (p) => (p.recent_form?.adr != null ? String(p.recent_form.adr) : "—") },
];

function avg(values: (number | null)[]): number | null {
  const v = values.filter((x): x is number => x != null);
  return v.length ? Math.round((v.reduce((a, b) => a + b, 0) / v.length) * 100) / 100 : null;
}

export function CompareView({ players }: { players: FaceitResult[] }) {
  const { t, lang } = useI18n();
  const found = players.filter((p) => p.found);
  const missing = players.filter((p) => !p.found);

  if (found.length < 2) {
    return (
      <div className="space-y-3">
        {players.map((p, i) => (
          <div key={p.player_id ?? `row-${i}`} className="rounded-xl border border-shb-border bg-white/[0.035] p-5 text-center text-sm text-slate-300">
            <span className="font-semibold text-white">#{i + 1}:</span> {p.found ? p.nickname : (p.message ?? t("notFound"))}
          </div>
        ))}
        <div className="text-center text-sm text-slate-500">Need at least 2 found players to compare.</div>
      </div>
    );
  }

  const color = (i: number) => SERIES_COLORS[i % SERIES_COLORS.length];
  // Per-player "wins" across metrics (for the header tally).
  const wins = found.map(() => 0);
  const bestByMetric = METRICS.map((m) => {
    const vals = found.map((p) => m.num(p));
    const max = Math.max(...vals.filter((v): v is number => v != null), -Infinity);
    const winners = vals.map((v) => v != null && v === max && Number.isFinite(max));
    winners.forEach((w, i) => { if (w) wins[i] += 1; });
    return winners;
  });

  const isStack = found.length >= 3;

  function exportCsv() {
    const header = ["Metric", ...found.map((p) => p.nickname ?? "?")];
    const rows = METRICS.map((m) => [m.label, ...found.map((p) => m.show(p))]);
    downloadCsv(`faceit-compare-${found.map((p) => p.nickname).join("-")}.csv`, [header, ...rows]);
  }
  async function copySummary() {
    const lines = [
      `FACEIT compare: ${found.map((p) => p.nickname).join(" vs ")}`,
      ...found.map((p) => `${p.nickname}: L${p.skill_level ?? "?"} · ${p.faceit_elo ?? "?"} ELO · ${p.stats.kd_ratio ?? "—"} K/D · ${wins[found.indexOf(p)]}🏆`),
    ];
    const ok = await copyText(lines.join("\n"));
    toast[ok ? "success" : "error"](ok ? "Summary copied" : "Copy failed");
  }

  return (
    <div className="space-y-5">
      <div className="premium-card rounded-2xl p-5">
        <div className="flex flex-wrap items-stretch gap-3">
          {found.map((p, i) => (
            <div key={p.player_id ?? `h-${i}`} className="flex min-w-[140px] flex-1 items-center gap-3 rounded-xl border bg-white/[0.02] p-3" style={{ borderColor: `${color(i)}55` }}>
              {p.avatar ? (
                // eslint-disable-next-line @next/next/no-img-element -- external FACEIT CDN avatar
                <img src={p.avatar} alt={p.nickname ?? "avatar"} width={44} height={44} className="rounded-lg border-2 object-cover" style={{ borderColor: color(i) }} />
              ) : (
                <div className="grid h-11 w-11 place-items-center rounded-lg border-2 bg-white/5 text-lg text-slate-200" style={{ borderColor: color(i) }}>
                  {(p.nickname ?? "?").charAt(0).toUpperCase()}
                </div>
              )}
              <div className="min-w-0">
                <div className="flex items-center gap-1 truncate font-semibold text-white">{p.nickname} <span>{flag(p.country)}</span></div>
                <div className="text-xs text-slate-400">{p.faceit_elo ?? "—"} ELO · {wins[i]}🏆</div>
              </div>
              <div className="ml-auto"><LevelBadge level={p.skill_level} size={36} /></div>
            </div>
          ))}
        </div>
        {missing.length > 0 && (
          <div className="mt-2 text-xs text-slate-500">Not found: {missing.map((p, i) => p.nickname || `#${i + 1}`).join(", ")}</div>
        )}
        {(() => {
          const top = wins.indexOf(Math.max(...wins));
          const tie = wins.filter((w) => w === wins[top]).length > 1;
          return (
            <div className="mt-3 border-t border-white/5 pt-3 text-center text-sm">
              {tie ? <span className="text-slate-300">It&apos;s close — no clear winner.</span> : (
                <span>🏆 <span className="font-bold" style={{ color: color(top) }}>{found[top].nickname}</span> leads {Math.max(...wins)}/{METRICS.length} metrics</span>
              )}
            </div>
          );
        })()}
      </div>

      {isStack && (
        <div className="premium-card rounded-xl p-4">
          <div className="mb-3 text-xs uppercase tracking-wide text-slate-400">{t("teamAvg")} · {found.length}-stack</div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { l: "ELO", v: avg(found.map((p) => p.faceit_elo)) },
              { l: "Level", v: avg(found.map((p) => p.skill_level)) },
              { l: "K/D", v: avg(found.map((p) => toNum(p.stats.kd_ratio))) },
              { l: "ADR", v: avg(found.map((p) => p.recent_form?.adr ?? null)) },
            ].map((c) => (
              <div key={c.l} className="rounded-lg border border-white/5 bg-white/[0.03] p-3 text-center">
                <div className="font-display text-xl font-bold text-gradient">{c.v ?? "—"}</div>
                <div className="mt-0.5 text-[11px] uppercase tracking-wide text-slate-400">{c.l}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap justify-end gap-2">
        <button onClick={copySummary} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1.5 text-sm text-slate-200 hover:border-white/25"><Copy className="h-3.5 w-3.5" /> {lang === "ru" ? "Сводка" : "Summary"}</button>
        <button onClick={exportCsv} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1.5 text-sm text-slate-200 hover:border-white/25"><Table className="h-3.5 w-3.5" /> CSV</button>
      </div>

      <div className="premium-card overflow-x-auto rounded-xl">
        <table className="w-full min-w-[420px] text-sm">
          <tbody>
            {METRICS.map((m, mi) => (
              <tr key={m.label} className="border-b border-white/5 last:border-0">
                <td className="px-4 py-2.5 text-xs uppercase tracking-wide text-slate-500">{m.label}</td>
                {found.map((p, i) => {
                  const win = bestByMetric[mi][i];
                  return (
                    <td key={p.player_id ?? `c-${i}`} className="px-3 py-2.5 text-center font-display text-lg" style={win ? { color: color(i), fontWeight: 700 } : { color: "#9daac2" }}>
                      {m.show(p)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {found.some((p) => p.radar && Object.values(p.radar).some((v) => v != null)) && (
        <div className="premium-card rounded-xl p-4">
          <div className="mb-2 text-xs uppercase tracking-wide text-slate-400">Skill radar</div>
          <RadarChart series={found.filter((p) => p.radar).map((p, i) => ({ values: p.radar!, color: color(found.indexOf(p)), label: p.nickname ?? `#${i + 1}` }))} size={320} />
          <div className="mt-2 flex flex-wrap justify-center gap-x-4 gap-y-1">
            {found.map((p, i) => (
              <span key={p.player_id ?? `r-${i}`} className="flex items-center gap-1.5 text-xs">
                <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: color(i) }} />
                <span className="text-white">{p.nickname}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {found.some((p) => p.elo_history.length > 1) && (
        <div className="premium-card rounded-xl p-4">
          <EloCompareChart
            series={found.map((p, i) => ({ points: p.elo_history, color: color(i), label: p.nickname ?? `#${i + 1}` }))}
            approx={found.some((p) => p.elo_history_approx)}
          />
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        {found.map((p, i) => (
          p.faceit_url && (
            <a key={p.player_id ?? `l-${i}`} href={p.faceit_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-sm hover:underline" style={{ color: color(i) }}>
              {p.nickname} <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )
        ))}
      </div>
    </div>
  );
}
