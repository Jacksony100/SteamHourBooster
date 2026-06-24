import type { FaceitResult } from "./types";

// Server-side API origin (mirrors next.config.mjs). The browser uses the /api rewrite;
// server components / OG routes must call the API host directly.
const API_ORIGIN =
  process.env.INTERNAL_API_ORIGIN ||
  process.env.API_INTERNAL_ORIGIN ||
  (process.env.NODE_ENV === "production" ? "http://api:8000" : "http://127.0.0.1:8000");

export async function getPlayer(query: string): Promise<FaceitResult | null> {
  try {
    const res = await fetch(`${API_ORIGIN}/api/v1/faceit/find?steam=${encodeURIComponent(query)}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as FaceitResult;
  } catch {
    return null;
  }
}
