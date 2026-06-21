import type { Metadata } from "next";

import { FaceitClient } from "@/features/faceit/faceit-client";

export const metadata: Metadata = {
  title: "FACEIT Finder",
  description: "Look up public FACEIT CS2 level and stats from a Steam profile — no login required.",
};

export default function FaceitPage() {
  return <FaceitClient />;
}
