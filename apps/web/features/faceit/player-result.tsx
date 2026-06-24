"use client";

import { useEffect, useState } from "react";
import { Download, ExternalLink, Eye, EyeOff } from "lucide-react";

import { AdvancedPanel } from "./advanced-stats";
import { EloChart } from "./elo-chart";
import { ActivityHeatmap, BestWorst, MapCharts, WinLossStrip } from "./extras";
import { useI18n } from "./i18n";
import { MapInsights, NextLevel, RecentForm, SmurfBadge, StreakBadge } from "./insights";
import { LevelBadge, ResultPip, Stat, countryName, flag } from "./lib";
import { MatchList } from "./match-list";
import { QuickFacts, WinLossDonut } from "./quick-facts";
import { ShareBar } from "./share-bar";
import { SteamPanel } from "./steam-panel";
import { Teammates } from "./teammates";
import type { FaceitResult } from "./types";
import { useWatch } from "./watchlist-context";

/** #19 — delta vs the ELO we saw last time this player was looked up (localStorage). */
function useEloDelta(playerId: string | null, elo: number | null) {
  const [delta, setDelta] = useState<number | null>(null);
  useEffect(() => {
    if (!playerId || elo == null) return;
    const key = `faceit_lastelo_${playerId}`;
    try {
      const prev = Number(localStorage.getItem(key));
      if (Number.isFinite(prev) && prev !== elo) setDelta(elo - prev);
      else setDelta(null);
      localStorage.setItem(key, String(elo));
    } catch {}
  }, [playerId, elo]);
  return delta;
}

export function PlayerResult({ result, onPick }: { result: FaceitResult; onPick?: (nickname: string) => void }) {
  const { t, lang } = useI18n();
  const { isWatched, toggle } = useWatch();
  const delta = useEloDelta(result.player_id, result.faceit_elo);
  const watched = isWatched(result.player_id);
  const cardHref = result.nickname ? `/faceit/p/${encodeURIComponent(result.nickname)}/opengraph-image` : null;

  return (
    <div className="space-y-5">
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
            <span className="text-lg" title={countryName(result.country, lang)}>{flag(result.country)}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            {result.region && `Region ${result.region} · `}
            {result.faceit_elo != null && `${result.faceit_elo} ELO`}
            {delta != null && (
              <span className={`text-xs ${delta > 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {delta > 0 ? "+" : ""}{delta} {t("sinceLast")}
              </span>
            )}
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            {result.faceit_url && (
              <a href={result.faceit_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-sm text-sky-300 hover:text-sky-200">
                {t("openProfile")} <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
            {result.player_id && (
              <button
                onClick={() => toggle({ player_id: result.player_id!, nickname: result.nickname, country: result.country })}
                className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-sm transition ${watched ? "border-sky-400/40 bg-sky-400/10 text-sky-200" : "border-white/10 text-slate-300 hover:border-white/25"}`}
              >
                {watched ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                {watched ? t("watching") : t("watch")}
              </button>
            )}
            {cardHref && (
              <a href={cardHref} download={`faceit-${result.nickname}.png`} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1 text-sm text-slate-300 hover:border-white/25">
                <Download className="h-3.5 w-3.5" /> {t("shareCard")}
              </a>
            )}
          </div>
        </div>
        <div className="grid place-items-center">
          <LevelBadge level={result.skill_level} />
          <div className="mt-1 text-xs text-slate-400">Level</div>
        </div>
      </div>

      {(result.streak || result.smurf) && (
        <div className="flex flex-wrap gap-2">
          {result.streak && <StreakBadge streak={result.streak} />}
          {result.smurf && <SmurfBadge smurf={result.smurf} />}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label={t("matches")} value={result.stats.matches} />
        <Stat label={t("winRate")} value={result.stats.win_rate ? `${result.stats.win_rate}%` : null} />
        <Stat label="K/D" value={result.stats.kd_ratio} />
        <Stat label={t("headshots")} value={result.stats.headshots ? `${result.stats.headshots}%` : null} />
      </div>

      <NextLevel elo={result.faceit_elo} level={result.skill_level} />

      <QuickFacts result={result} />

      {result.recent_form && (
        <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
          <RecentForm form={result.recent_form} />
          <WinLossDonut wins={result.recent_form.wins} total={result.recent_form.matches} />
        </div>
      )}

      <AdvancedPanel result={result} />

      {result.elo_history.length > 1 && (
        <div className="premium-card rounded-xl p-4">
          <EloChart points={result.elo_history} approx={result.elo_history_approx} />
        </div>
      )}

      <WinLossStrip matches={result.matches} />

      {result.stats.recent_results.length > 0 && (
        <div className="premium-card rounded-xl p-4">
          <div className="mb-2 text-xs uppercase tracking-wide text-slate-400">{t("recentResults")}</div>
          <div className="flex gap-2">
            {result.stats.recent_results.map((r, i) => <ResultPip key={i} value={r} />)}
          </div>
        </div>
      )}

      <BestWorst best={result.best_match} worst={result.worst_match} />

      <MapInsights maps={result.maps} />
      <MapCharts maps={result.maps} />

      <Teammates teammates={result.teammates} onPick={onPick} />

      <MatchList matches={result.matches} playerId={result.player_id} />

      {result.activity && <ActivityHeatmap activity={result.activity} />}

      <ShareBar result={result} />

      {result.steam && <SteamPanel steam={result.steam} />}

      {result.detail_level === "basic" && (
        <p className="text-xs text-slate-500">
          Level &amp; ELO are exact. Detailed stats, per-map breakdown and match history require a free FACEIT API key
          on the server (keyless FACEIT stat endpoints are blocked by FACEIT&apos;s bot protection). Set
          <code className="mx-1 rounded bg-white/10 px-1">FACEIT_API_KEY</code> and restart the API for full data.
        </p>
      )}
    </div>
  );
}
