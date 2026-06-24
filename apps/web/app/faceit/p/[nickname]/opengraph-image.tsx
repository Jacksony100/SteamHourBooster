import { ImageResponse } from "next/og";

import { getPlayer } from "@/features/faceit/server";

export const alt = "FACEIT CS2 stats card";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const LEVEL_COLORS: Record<number, string> = {
  1: "#EEEEEE", 2: "#1CE400", 3: "#1CE400", 4: "#FFC800", 5: "#FFC800",
  6: "#FFC800", 7: "#FFC800", 8: "#FF6309", 9: "#FF6309", 10: "#FE1F00",
};

type Params = { params: Promise<{ nickname: string }> };

export default async function OpengraphImage({ params }: Params) {
  const { nickname } = await params;
  const nick = decodeURIComponent(nickname);
  const p = await getPlayer(nick);
  const level = p?.skill_level ?? 0;
  const color = LEVEL_COLORS[level] ?? "#3A4253";

  const Stat = ({ label, value }: { label: string; value: string }) => (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "0 28px" }}>
      <div style={{ fontSize: 56, fontWeight: 800, color: "#ffffff" }}>{value}</div>
      <div style={{ fontSize: 22, color: "#9daac2", textTransform: "uppercase", letterSpacing: 2 }}>{label}</div>
    </div>
  );

  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", background: "#05070d", color: "#eaf0fa", padding: 64, fontFamily: "sans-serif" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 36 }}>
          {p?.avatar ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={p.avatar} width={148} height={148} style={{ borderRadius: 24, border: "3px solid rgba(255,255,255,0.15)" }} alt="" />
          ) : (
            <div style={{ width: 148, height: 148, borderRadius: 24, background: "rgba(255,255,255,0.06)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 64 }}>
              {(p?.nickname ?? nick ?? "?").charAt(0).toUpperCase()}
            </div>
          )}
          <div style={{ display: "flex", flexDirection: "column" }}>
            <div style={{ fontSize: 64, fontWeight: 800 }}>{p?.found ? p.nickname : nick}</div>
            <div style={{ fontSize: 30, color: "#9daac2" }}>{p?.found ? `${p.faceit_elo ?? "?"} ELO · ${p.region ?? ""}` : "FACEIT CS2 Finder"}</div>
          </div>
          <div style={{ marginLeft: "auto", width: 132, height: 132, borderRadius: 28, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 72, fontWeight: 900, color, background: `${color}22`, border: `5px solid ${color}` }}>
            {level || "?"}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: 28 }}>
          <Stat label="Matches" value={p?.stats?.matches ?? "—"} />
          <Stat label="Win rate" value={p?.stats?.win_rate ? `${p.stats.win_rate}%` : "—"} />
          <Stat label="K/D" value={p?.stats?.kd_ratio ?? "—"} />
          <Stat label="Headshots" value={p?.stats?.headshots ? `${p.stats.headshots}%` : "—"} />
          <div style={{ marginLeft: "auto", fontSize: 28, fontWeight: 700, color: "#5ba6ff" }}>FACEIT Finder</div>
        </div>
      </div>
    ),
    { ...size },
  );
}
