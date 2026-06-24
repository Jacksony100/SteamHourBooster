import type { ReactNode } from "react";

// Official FACEIT skill-level palette (1–10).
export const LEVEL_COLORS: Record<number, string> = {
  1: "#EEEEEE", 2: "#1CE400", 3: "#1CE400", 4: "#FFC800", 5: "#FFC800",
  6: "#FFC800", 7: "#FFC800", 8: "#FF6309", 9: "#FF6309", 10: "#FE1F00",
};

// Distinct brand colours for up to 5 compared players.
export const SERIES_COLORS = ["#2e8bff", "#8b5cf6", "#3df5a0", "#f5b83d", "#ff5c7a"] as const;

export function levelColor(level: number | null | undefined): string {
  return LEVEL_COLORS[level ?? 0] ?? "#3A4253";
}

export function mapLabel(name: string): string {
  return name.replace(/^de_/, "").replace(/\b\w/g, (c) => c.toUpperCase());
}

// FACEIT CS2 skill-level ELO lower bounds (levels 1..10).
export const LEVEL_MIN_ELO = [100, 501, 751, 901, 1051, 1201, 1351, 1531, 1751, 2001];

export type LevelProgress = { level: number; nextElo: number | null; toNext: number | null; pct: number };

export function nextLevelProgress(elo: number | null | undefined): LevelProgress | null {
  if (elo == null) return null;
  let level = 1;
  for (let i = 0; i < LEVEL_MIN_ELO.length; i++) if (elo >= LEVEL_MIN_ELO[i]) level = i + 1;
  if (level >= 10) return { level: 10, nextElo: null, toNext: null, pct: 100 };
  const floor = LEVEL_MIN_ELO[level - 1];
  const nextElo = LEVEL_MIN_ELO[level];
  const pct = Math.max(0, Math.min(100, Math.round(((elo - floor) / (nextElo - floor)) * 100)));
  return { level, nextElo, toNext: nextElo - elo, pct };
}

export function relativeDate(isoDate: string | null | undefined): string {
  if (!isoDate) return "";
  const then = new Date(isoDate).getTime();
  if (Number.isNaN(then)) return isoDate;
  const days = Math.floor((Date.now() - then) / 86_400_000);
  if (days <= 0) return "today";
  if (days === 1) return "1d ago";
  if (days < 30) return `${days}d ago`;
  if (days < 365) return `${Math.floor(days / 30)}mo ago`;
  return `${Math.floor(days / 365)}y ago`;
}

export function countryName(code: string | null | undefined, lang = "en"): string {
  if (!code || code.length !== 2) return "";
  try {
    return new Intl.DisplayNames([lang], { type: "region" }).of(code.toUpperCase()) ?? code.toUpperCase();
  } catch {
    return code.toUpperCase();
  }
}

export function formatNum(n: number | string | null | undefined): string {
  const v = typeof n === "string" ? Number(n) : n;
  return v == null || Number.isNaN(v) ? "—" : v.toLocaleString();
}

/** Approx matches needed to reach the next FACEIT level (~25 ELO per win). */
export function matchesToNextLevel(toNext: number | null | undefined): number | null {
  return toNext == null ? null : Math.max(1, Math.ceil(toNext / 25));
}

/** Composite recent-form score 0–100 from win rate, K/D and ADR. */
export function formScore(rf: { win_rate: number; kd_ratio: number | null; adr: number | null } | null | undefined): number | null {
  if (!rf) return null;
  const wr = Math.max(0, Math.min(100, rf.win_rate));
  const kd = rf.kd_ratio == null ? 50 : Math.max(0, Math.min(100, (rf.kd_ratio / 2) * 100));
  const adr = rf.adr == null ? 50 : Math.max(0, Math.min(100, (rf.adr / 110) * 100));
  return Math.round(wr * 0.4 + kd * 0.35 + adr * 0.25);
}

export function hsLabel(hs: number | string | null | undefined): string | null {
  const v = typeof hs === "string" ? Number(hs) : hs;
  if (v == null || Number.isNaN(v)) return null;
  if (v >= 55) return "Headshot machine";
  if (v >= 45) return "Sharp aim";
  if (v >= 35) return "Solid aim";
  return "Spray & pray";
}

const REGIONS: Record<string, string> = { EU: "Europe", NA: "North America", SA: "South America", AS: "Asia", OCE: "Oceania", AF: "Africa", SEA: "SE Asia" };
export function regionName(code: string | null | undefined): string {
  if (!code) return "";
  return REGIONS[code.toUpperCase()] ?? code;
}

/** Deterministic 2-colour gradient from a string (avatar fallback). */
export function avatarGradient(seed: string | null | undefined): string {
  let h = 0;
  for (const ch of seed ?? "?") h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  const a = h % 360;
  const b = (a + 50) % 360;
  return `linear-gradient(135deg, hsl(${a} 65% 45%), hsl(${b} 60% 35%))`;
}

export function levelEloRange(level: number | null | undefined): string | null {
  if (!level || level < 1 || level > 10) return null;
  const lo = LEVEL_MIN_ELO[level - 1];
  const hi = level >= 10 ? null : LEVEL_MIN_ELO[level] - 1;
  return hi == null ? `${lo}+` : `${lo}–${hi}`;
}

export function accountAgeYears(isoDate: string | null | undefined): number | null {
  if (!isoDate) return null;
  const then = new Date(isoDate).getTime();
  if (Number.isNaN(then)) return null;
  return Math.max(0, Math.floor((Date.now() - then) / (365.25 * 24 * 3600 * 1000)));
}

export function flag(country: string | null): string {
  if (!country || country.length !== 2) return "";
  const base = 0x1f1e6;
  return String.fromCodePoint(...country.toUpperCase().split("").map((c) => base + c.charCodeAt(0) - 65));
}

/** Parse a numeric stat string ("1.15", "58") to a number, or null if not parseable. */
export function toNum(value: string | null | undefined): number | null {
  if (value == null || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function Stat({ label, value, accent }: { label: string; value: ReactNode; accent?: boolean }) {
  return (
    <div className="premium-card rounded-xl p-4 text-center">
      <div className={`font-display text-2xl font-bold ${accent ? "text-gradient" : "text-white"}`}>{value ?? "—"}</div>
      <div className="mt-1 text-xs uppercase tracking-wide text-slate-400">{label}</div>
    </div>
  );
}

export function LevelBadge({ level, size = 64 }: { level: number | null; size?: number }) {
  const value = level ?? 0;
  const color = levelColor(value);
  return (
    <div
      className="grid place-items-center rounded-2xl font-display font-black"
      style={{
        width: size, height: size, fontSize: size * 0.36,
        background: `${color}22`, color, border: `2px solid ${color}`,
      }}
      title={`FACEIT level ${value}`}
    >
      {value || "?"}
    </div>
  );
}

export function ResultPip({ value, size = 28 }: { value: string; size?: number }) {
  const win = value === "1" || value === "win";
  return (
    <span
      className="grid place-items-center rounded-lg text-xs font-bold"
      style={{
        width: size, height: size,
        ...(win
          ? { background: "rgba(61,245,160,.15)", color: "#3DF5A0" }
          : { background: "rgba(255,92,122,.15)", color: "#FF5C7A" }),
      }}
    >
      {win ? "W" : "L"}
    </span>
  );
}
