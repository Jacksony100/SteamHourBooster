"use client";

import { ExternalLink } from "lucide-react";

import { accountAgeYears } from "./lib";
import { useI18n } from "./i18n";
import type { FaceitSteam } from "./types";

function Chip({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.03] px-3 py-2 text-center">
      <div className="font-display text-lg font-bold text-white">{value}</div>
      <div className="text-[11px] uppercase tracking-wide text-slate-400">{label}</div>
    </div>
  );
}

export function SteamPanel({ steam }: { steam: FaceitSteam }) {
  const { t } = useI18n();
  const age = accountAgeYears(steam.account_created);
  return (
    <div className="premium-card rounded-xl p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs uppercase tracking-wide text-slate-400">{t("steam")}</span>
        {steam.profile_url && (
          <a href={steam.profile_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs text-sky-300 hover:text-sky-200">
            Steam <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {steam.cs2_hours != null && <Chip label={t("hours")} value={steam.cs2_hours.toLocaleString()} />}
        {steam.steam_level != null && <Chip label={t("steamLevel")} value={steam.steam_level} />}
        {age != null && <Chip label={t("account")} value={`${age} ${t("years")}`} />}
        <Chip
          label="VAC"
          value={
            steam.vac_banned
              ? <span className="text-rose-400">{t("vacBanned")}{steam.vac_ban_count ? ` ×${steam.vac_ban_count}` : ""}</span>
              : <span className="text-emerald-400">✓</span>
          }
        />
      </div>
      {steam.visibility === "private" && (
        <p className="mt-2 text-xs text-slate-500">Steam profile is private — some data may be hidden.</p>
      )}
    </div>
  );
}
