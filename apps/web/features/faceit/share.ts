import type { FaceitResult } from "./types";

function origin() {
  return typeof window !== "undefined" ? window.location.origin : "";
}

export function permalinkFor(nick: string) {
  return `${origin()}/faceit/p/${encodeURIComponent(nick)}`;
}

export function badgeUrlFor(nick: string) {
  return `${origin()}/faceit/badge/${encodeURIComponent(nick)}`;
}

export function comparePermalink(nicks: string[]) {
  const qs = nicks.filter((n) => n.trim()).map((n) => `players=${encodeURIComponent(n.trim())}`).join("&");
  return `${origin()}/faceit?${qs}`;
}

export function embedMarkdown(nick: string) {
  return `[![FACEIT ${nick}](${badgeUrlFor(nick)})](${permalinkFor(nick)})`;
}

export function embedHtml(nick: string) {
  return `<a href="${permalinkFor(nick)}"><img src="${badgeUrlFor(nick)}" alt="FACEIT ${nick}" height="64"></a>`;
}

export function xShareUrl(result: FaceitResult) {
  const text = result.nickname
    ? `${result.nickname} — FACEIT CS2: Level ${result.skill_level ?? "?"}, ${result.faceit_elo ?? "?"} ELO, ${result.stats.kd_ratio ?? "—"} K/D`
    : "FACEIT CS2 stats";
  const url = result.nickname ? permalinkFor(result.nickname) : origin();
  return `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
}

function shareText(result: FaceitResult) {
  return result.nickname
    ? `${result.nickname} — FACEIT CS2: Level ${result.skill_level ?? "?"}, ${result.faceit_elo ?? "?"} ELO`
    : "FACEIT CS2 stats";
}

export function telegramShareUrl(result: FaceitResult) {
  const url = result.nickname ? permalinkFor(result.nickname) : origin();
  return `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(shareText(result))}`;
}

export function vkShareUrl(result: FaceitResult) {
  const url = result.nickname ? permalinkFor(result.nickname) : origin();
  return `https://vk.com/share.php?url=${encodeURIComponent(url)}&title=${encodeURIComponent(shareText(result))}`;
}

/** Download the player's data as a JSON file. */
export function downloadJson(result: FaceitResult) {
  try {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `faceit-${result.nickname ?? "player"}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  } catch {
    /* ignore */
  }
}

export function statsSummary(result: FaceitResult): string {
  const s = result.stats;
  return [
    `${result.nickname} — FACEIT CS2`,
    `Level ${result.skill_level ?? "?"} · ${result.faceit_elo ?? "?"} ELO`,
    `${s.matches ?? "—"} matches · ${s.win_rate ?? "—"}% WR · ${s.kd_ratio ?? "—"} K/D · ${s.headshots ?? "—"}% HS`,
    result.nickname ? permalinkFor(result.nickname) : "",
  ].filter(Boolean).join("\n");
}

export function downloadCsv(filename: string, rows: (string | number | null)[][]) {
  try {
    const csv = rows.map((r) => r.map((c) => `"${String(c ?? "").replace(/"/g, '""')}"`).join(",")).join("\r\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  } catch {
    /* ignore */
  }
}

/** Native share sheet (mobile); returns false if unavailable so callers can fall back to copy. */
export async function nativeShare(result: FaceitResult): Promise<boolean> {
  const url = result.nickname ? permalinkFor(result.nickname) : origin();
  if (typeof navigator !== "undefined" && "share" in navigator) {
    try {
      await (navigator as Navigator & { share: (d: ShareData) => Promise<void> }).share({ title: "FACEIT Finder", text: statsSummary(result), url });
      return true;
    } catch {
      return false;
    }
  }
  return false;
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

/** External profile links for the same player. */
export function externalLinks(result: FaceitResult): { label: string; url: string }[] {
  const links: { label: string; url: string }[] = [];
  if (result.faceit_url) links.push({ label: "FACEIT", url: result.faceit_url });
  if (result.steamid64) {
    links.push({ label: "Steam", url: `https://steamcommunity.com/profiles/${result.steamid64}` });
    links.push({ label: "Leetify", url: `https://leetify.com/app/profile/${result.steamid64}` });
    links.push({ label: "CSStats", url: `https://csstats.gg/player/${result.steamid64}` });
  }
  return links;
}
