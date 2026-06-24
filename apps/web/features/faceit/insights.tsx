"use client";

import { AlertTriangle, Flame, Snowflake } from "lucide-react";

import { useI18n } from "./i18n";
import { levelColor, mapLabel, nextLevelProgress, toNum } from "./lib";
import type { FaceitMap, FaceitRecentForm, FaceitSmurf, FaceitStreak } from "./types";

export function RecentForm({ form }: { form: FaceitRecentForm }) {
  const { t } = useI18n();
  const delta = form.kd_delta;
  return (
    <div className="premium-card rounded-xl p-4">
      <div className="mb-3 text-xs uppercase tracking-wide text-slate-400">{t("recentForm")} · {form.matches}</div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Cell label={t("winRate")} value={`${form.win_rate}%`} />
        <Cell
          label="K/D"
          value={
            <span className="inline-flex items-center gap-1">
              {form.kd_ratio ?? "—"}
              {delta != null && delta !== 0 && (
                <span className={`text-xs ${delta > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                  {delta > 0 ? "▲" : "▼"}{Math.abs(delta)}
                </span>
              )}
            </span>
          }
        />
        <Cell label="ADR" value={form.adr ?? "—"} />
        <Cell label={t("headshots")} value={form.headshots != null ? `${form.headshots}%` : "—"} />
      </div>
    </div>
  );
}

function Cell({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.03] p-3 text-center">
      <div className="font-display text-xl font-bold text-white">{value}</div>
      <div className="mt-0.5 text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
    </div>
  );
}

export function StreakBadge({ streak }: { streak: FaceitStreak }) {
  const { t } = useI18n();
  if (streak.length < 2) return null;
  const win = streak.type === "win";
  const Icon = win ? Flame : Snowflake;
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-sm font-semibold"
      style={win ? { background: "rgba(61,245,160,.14)", color: "#3DF5A0" } : { background: "rgba(255,92,122,.14)", color: "#FF5C7A" }}
    >
      <Icon className="h-4 w-4" />
      {win ? t("streakWin") : t("streakLoss")} {streak.length}
      {streak.tilt && <span className="ml-1 inline-flex items-center gap-1 text-amber-300"><AlertTriangle className="h-3.5 w-3.5" /> {t("tilt")}</span>}
    </span>
  );
}

export function SmurfBadge({ smurf }: { smurf: FaceitSmurf }) {
  const { t } = useI18n();
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-lg bg-amber-400/15 px-2.5 py-1 text-sm font-semibold text-amber-300"
      title={`${t("smurfNote")}: ${smurf.flags.join("; ")}`}
    >
      <AlertTriangle className="h-4 w-4" /> {t("smurf")} · {smurf.score}/100
    </span>
  );
}

export function NextLevel({ elo, level }: { elo: number | null; level: number | null }) {
  const { t } = useI18n();
  const prog = nextLevelProgress(elo);
  if (!prog) return null;
  const color = levelColor(level);
  if (prog.nextElo == null) {
    return <div className="premium-card rounded-xl p-4 text-center text-sm text-slate-300">🏆 {t("maxLevel")}</div>;
  }
  const nextColor = levelColor(prog.level + 1);
  return (
    <div className="premium-card rounded-xl p-4">
      <div className="mb-2 flex items-center justify-between text-xs text-slate-400">
        <span className="uppercase tracking-wide">{t("nextLevel")} {prog.level + 1}</span>
        <span><span className="font-semibold text-white">{prog.toNext}</span> ELO</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full" style={{ width: `${prog.pct}%`, background: `linear-gradient(90deg, ${color}, ${nextColor})` }} />
      </div>
    </div>
  );
}

export function LevelScale({ level }: { level: number | null }) {
  if (!level) return null;
  return (
    <div className="premium-card rounded-xl p-4">
      <div className="mb-2 text-xs uppercase tracking-wide text-slate-400">Skill level {level}/10</div>
      <div className="flex gap-1">
        {Array.from({ length: 10 }, (_, i) => {
          const lv = i + 1;
          const on = lv <= level;
          return (
            <div
              key={lv}
              className="h-3 flex-1 rounded-sm"
              title={`Level ${lv}`}
              style={{ background: on ? levelColor(lv) : "rgba(255,255,255,0.08)", opacity: lv === level ? 1 : on ? 0.55 : 1 }}
            />
          );
        })}
      </div>
    </div>
  );
}

export function MapInsights({ maps }: { maps: FaceitMap[] }) {
  const { t } = useI18n();
  const rated = maps
    .map((m) => ({ ...m, wr: toNum(m.win_rate), n: toNum(m.matches) ?? 0 }))
    .filter((m) => m.wr != null && m.n >= 3);
  if (rated.length < 2) return null;
  const sorted = [...rated].sort((a, b) => (b.wr! - a.wr!));
  const best = sorted[0];
  const worst = sorted[sorted.length - 1];
  return (
    <div className="premium-card grid gap-3 rounded-xl p-4 sm:grid-cols-2">
      <div className="rounded-lg border border-emerald-400/20 bg-emerald-400/[0.06] p-3">
        <div className="text-[11px] uppercase tracking-wide text-emerald-300/80">{t("bestMap")} · {t("pick")}</div>
        <div className="mt-1 flex items-baseline justify-between">
          <span className="font-semibold text-white">{mapLabel(best.name)}</span>
          <span className="text-emerald-300">{best.wr}% WR</span>
        </div>
      </div>
      <div className="rounded-lg border border-rose-400/20 bg-rose-400/[0.06] p-3">
        <div className="text-[11px] uppercase tracking-wide text-rose-300/80">{t("worstMap")} · {t("ban")}</div>
        <div className="mt-1 flex items-baseline justify-between">
          <span className="font-semibold text-white">{mapLabel(worst.name)}</span>
          <span className="text-rose-300">{worst.wr}% WR</span>
        </div>
      </div>
    </div>
  );
}
