"use client";

import { Crosshair, Flame, Sparkles } from "lucide-react";

import { useI18n } from "./i18n";
import { RadarChart } from "./radar-chart";
import type { FaceitResult } from "./types";

function Chip({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.03] p-3 text-center">
      <div className="font-display text-lg font-bold text-white">{value ?? "—"}</div>
      <div className="mt-0.5 text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
    </div>
  );
}

export function AdvancedPanel({ result }: { result: FaceitResult }) {
  const { t } = useI18n();
  const adv = result.advanced;
  const radar = result.radar;
  const hasRadar = radar && Object.values(radar).some((v) => v != null);

  return (
    <div className="space-y-3">
      {(hasRadar || result.consistency != null || result.percentile != null) && (
        <div className="premium-card grid gap-4 rounded-xl p-4 sm:grid-cols-[280px_1fr] sm:items-center">
          {hasRadar && (
            <RadarChart series={[{ values: radar!, color: "#2e8bff" }]} />
          )}
          <div className="grid grid-cols-2 gap-3">
            {result.percentile != null && (
              <div className="rounded-lg border border-white/5 bg-white/[0.03] p-3 text-center">
                <div className="font-display text-2xl font-bold text-gradient">≈ top {100 - result.percentile}%</div>
                <div className="mt-0.5 text-[11px] uppercase tracking-wide text-slate-400">ELO percentile</div>
              </div>
            )}
            {result.consistency != null && (
              <div className="rounded-lg border border-white/5 bg-white/[0.03] p-3 text-center">
                <div className="font-display text-2xl font-bold text-white">{result.consistency}<span className="text-base text-slate-500">/100</span></div>
                <div className="mt-0.5 text-[11px] uppercase tracking-wide text-slate-400">Consistency</div>
              </div>
            )}
          </div>
        </div>
      )}

      {adv && (
        <div className="premium-card rounded-xl p-4">
          <div className="mb-3 flex items-center gap-1.5 text-xs uppercase tracking-wide text-slate-400">
            <Crosshair className="h-3.5 w-3.5" /> Advanced · {t("recentForm").toLowerCase()}
          </div>
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
            <Chip label="Entry win" value={adv.entry_success != null ? `${adv.entry_success}%` : null} />
            <Chip label="Clutch 1v1" value={adv.clutch_1v1 != null ? `${adv.clutch_1v1}%` : null} />
            <Chip label="Clutch 1v2" value={adv.clutch_1v2 != null ? `${adv.clutch_1v2}%` : null} />
            <Chip label="Util dmg" value={adv.utility_dmg_per_match} />
            <Chip label="AWP /match" value={adv.sniper_per_match} />
            <Chip label="Flashes /m" value={adv.flashes_per_match} />
            <Chip label="Avg K/D/A" value={adv.avg_kills != null ? `${adv.avg_kills}/${adv.avg_deaths}/${adv.avg_assists}` : null} />
            <Chip label="Pistol kills" value={adv.pistol_total} />
          </div>
          {(adv.aces || adv.quad_kills || adv.triple_kills) ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {adv.aces ? <Badge icon={<Sparkles className="h-3.5 w-3.5" />} text={`${adv.aces} ACE`} tone="#FE1F00" /> : null}
              {adv.quad_kills ? <Badge icon={<Flame className="h-3.5 w-3.5" />} text={`${adv.quad_kills} quad`} tone="#FF6309" /> : null}
              {adv.triple_kills ? <Badge icon={<Flame className="h-3.5 w-3.5" />} text={`${adv.triple_kills} triple`} tone="#FFC800" /> : null}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

function Badge({ icon, text, tone }: { icon: React.ReactNode; text: string; tone: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-sm font-semibold" style={{ background: `${tone}22`, color: tone }}>
      {icon} {text}
    </span>
  );
}
