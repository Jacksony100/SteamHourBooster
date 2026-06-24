import type { Metadata } from "next";

import { FaceitClient } from "@/features/faceit/faceit-client";
import { getPlayer } from "@/features/faceit/server";

type Params = { params: Promise<{ nickname: string }> };

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { nickname } = await params;
  const nick = decodeURIComponent(nickname);
  const p = await getPlayer(nick);
  const title = p?.found
    ? `${p.nickname} · FACEIT CS2 — Level ${p.skill_level ?? "?"}, ${p.faceit_elo ?? "?"} ELO`
    : `${nick} · FACEIT Finder`;
  const description = p?.found
    ? `FACEIT CS2 stats for ${p.nickname}: Level ${p.skill_level ?? "?"}, ${p.faceit_elo ?? "?"} ELO, K/D ${p.stats?.kd_ratio ?? "—"}, ${p.stats?.win_rate ?? "—"}% win rate.`
    : "Look up full FACEIT CS2 stats — level, ELO, ELO trend and recent matches.";
  return {
    title,
    description,
    openGraph: { title, description, type: "profile" },
    twitter: { card: "summary_large_image", title, description },
  };
}

export default async function FaceitPlayerPage({ params }: Params) {
  const { nickname } = await params;
  return <FaceitClient initialQuery={decodeURIComponent(nickname)} />;
}
