import { getPlayer } from "@/features/faceit/server";

export const dynamic = "force-dynamic";

const LEVEL_COLORS: Record<number, string> = {
  1: "#EEEEEE", 2: "#1CE400", 3: "#1CE400", 4: "#FFC800", 5: "#FFC800",
  6: "#FFC800", 7: "#FFC800", 8: "#FF6309", 9: "#FF6309", 10: "#FE1F00",
};

function esc(s: string) {
  return s.replace(/[<>&'"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", "'": "&apos;", '"': "&quot;" }[c]!));
}

export async function GET(_req: Request, { params }: { params: Promise<{ nickname: string }> }) {
  const { nickname } = await params;
  const nick = decodeURIComponent(nickname);
  const p = await getPlayer(nick);
  const level = p?.skill_level ?? 0;
  const color = LEVEL_COLORS[level] ?? "#3A4253";
  const name = esc(p?.found ? (p.nickname ?? nick) : nick);
  const elo = p?.found && p.faceit_elo != null ? `${p.faceit_elo} ELO` : "not found";

  const W = 300;
  const H = 64;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="FACEIT ${name} ${elo}">
  <rect width="${W}" height="${H}" rx="10" fill="#0d1422"/>
  <rect x="1" y="1" width="${W - 2}" height="${H - 2}" rx="9" fill="none" stroke="rgba(255,255,255,0.12)"/>
  <rect x="12" y="12" width="40" height="40" rx="8" fill="${color}22" stroke="${color}" stroke-width="2"/>
  <text x="32" y="40" font-family="Segoe UI,Arial,sans-serif" font-size="22" font-weight="800" fill="${color}" text-anchor="middle">${level || "?"}</text>
  <text x="66" y="28" font-family="Segoe UI,Arial,sans-serif" font-size="16" font-weight="700" fill="#eaf0fa">${name}</text>
  <text x="66" y="47" font-family="Segoe UI,Arial,sans-serif" font-size="13" fill="#9daac2">${esc(elo)}</text>
  <text x="${W - 14}" y="26" font-family="Segoe UI,Arial,sans-serif" font-size="11" font-weight="700" fill="#FF5500" text-anchor="end">FACEIT</text>
</svg>`;

  return new Response(svg, {
    headers: {
      "Content-Type": "image/svg+xml; charset=utf-8",
      "Cache-Control": "public, max-age=300, s-maxage=300",
    },
  });
}
