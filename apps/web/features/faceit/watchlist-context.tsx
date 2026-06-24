"use client";

import { createContext, useContext, useEffect, useState } from "react";

import type { WatchItem } from "./types";

const BASE = "/api/v1/faceit/watchlist";
const LS_KEY = "faceit_watchlist";

function csrfToken() {
  if (typeof document === "undefined") return "";
  const rows = document.cookie.split("; ");
  return (
    rows.find((r) => r.startsWith("deckpilot_csrf="))?.split("=")[1] ||
    rows.find((r) => r.startsWith("shb_csrf="))?.split("=")[1] ||
    ""
  );
}

function localGet(): WatchItem[] {
  try { return JSON.parse(localStorage.getItem(LS_KEY) || "[]"); } catch { return []; }
}
function localSet(items: WatchItem[]) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(items)); } catch {}
}

type Mode = "loading" | "server" | "local";
type Ctx = { items: WatchItem[]; mode: Mode; isWatched: (id: string | null) => boolean; toggle: (p: WatchItem) => Promise<void> };

const WatchCtx = createContext<Ctx>({ items: [], mode: "loading", isWatched: () => false, toggle: async () => {} });

export function WatchlistProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<WatchItem[]>([]);
  const [mode, setMode] = useState<Mode>("loading");

  useEffect(() => {
    let alive = true;
    // Raw fetch (not the api() helper) so a 401 does NOT redirect anonymous users to /login.
    fetch(BASE, { credentials: "include", cache: "no-store" })
      .then(async (r) => {
        if (!alive) return;
        if (r.ok) {
          const data = await r.json().catch(() => ({ items: [] }));
          setItems(data.items ?? []);
          setMode("server");
        } else {
          setItems(localGet());
          setMode("local");
        }
      })
      .catch(() => { if (alive) { setItems(localGet()); setMode("local"); } });
    return () => { alive = false; };
  }, []);

  function isWatched(id: string | null) {
    return !!id && items.some((i) => i.player_id === id);
  }

  async function toggle(p: WatchItem) {
    if (!p.player_id) return;
    const has = items.some((i) => i.player_id === p.player_id);
    if (mode === "server") {
      const opts: RequestInit = { credentials: "include", headers: { "X-CSRF-Token": csrfToken() } };
      const res = has
        ? await fetch(`${BASE}/${p.player_id}`, { ...opts, method: "DELETE" })
        : await fetch(BASE, { ...opts, method: "POST", headers: { ...opts.headers, "Content-Type": "application/json" }, body: JSON.stringify(p) });
      if (res.ok) {
        const data = await res.json().catch(() => ({ items: [] }));
        setItems(data.items ?? []);
      }
    } else {
      const next = has ? items.filter((i) => i.player_id !== p.player_id) : [p, ...items];
      localSet(next);
      setItems(next);
    }
  }

  return <WatchCtx.Provider value={{ items, mode, isWatched, toggle }}>{children}</WatchCtx.Provider>;
}

export function useWatch() {
  return useContext(WatchCtx);
}
