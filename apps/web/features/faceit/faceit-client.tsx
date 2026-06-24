"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Toaster, toast } from "sonner";
import { ArrowLeft, Eye, Maximize2, Plus, RefreshCw, Search, Star, Swords, X } from "lucide-react";

import { api } from "@/lib/api";

import { CompareView } from "./compare-view";
import { I18nProvider, useI18n } from "./i18n";
import { PlayerResult } from "./player-result";
import { addRecent, clearRecent, getRecent } from "./recent";
import { comparePermalink, copyText } from "./share";
import type { FaceitCompare, FaceitResult } from "./types";
import { WatchlistProvider } from "./watchlist-context";
import { WatchlistTab } from "./watchlist-tab";

type Mode = "single" | "compare" | "watch";

const PRESET_PROS = ["s1mple", "donk", "ZywOo", "NiKo", "m0NESY"];
const INPUT_CLASS = "flex-1 rounded-xl border border-shb-border bg-white/5 px-4 py-3 text-white outline-none focus:border-sky-400/60";

function FaceitInner({ initialQuery }: { initialQuery?: string }) {
  const { t, lang, setLang } = useI18n();
  const [mode, setMode] = useState<Mode>("single");

  const [input, setInput] = useState(initialQuery ?? "");
  const [result, setResult] = useState<FaceitResult | null>(null);

  const [inputs, setInputs] = useState<string[]>(["", ""]);
  const [compare, setCompare] = useState<FaceitCompare | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recent, setRecent] = useState<string[]>([]);
  const [me, setMe] = useState<string | null>(null);
  const [wide, setWide] = useState(false);
  const didInit = useRef(false);
  const searchRef = useRef<HTMLInputElement>(null);

  const lookup = useCallback(async (value: string, opts?: { refresh?: boolean }) => {
    const q = value.trim();
    if (!q) return;
    setMode("single");
    setInput(q);
    setLoading(true);
    setError(null);
    if (!opts?.refresh) setResult(null);
    try {
      const url = `/faceit/find?steam=${encodeURIComponent(q)}${opts?.refresh ? "&refresh=1" : ""}`;
      const data = await api<FaceitResult>(url);
      setResult(data);
      setRecent(addRecent(q));
      try { history.replaceState(null, "", `?q=${encodeURIComponent(q)}`); } catch {}
      if (opts?.refresh) toast.success("Refreshed");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lookup failed");
    } finally {
      setLoading(false);
    }
  }, []);

  const runCompareWith = useCallback(async (qs: string[]) => {
    const clean = qs.map((v) => v.trim()).filter(Boolean);
    if (clean.length < 2) return;
    setMode("compare");
    setLoading(true);
    setError(null);
    setCompare(null);
    try {
      const query = clean.map((q) => `players=${encodeURIComponent(q)}`).join("&");
      setCompare(await api<FaceitCompare>(`/faceit/compare?${query}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setLoading(false);
    }
  }, []);

  // Init: stored prefs + deep links (?q= / ?compare=) or initialQuery.
  useEffect(() => {
    if (didInit.current) return;
    didInit.current = true;
    setRecent(getRecent());
    try {
      setMe(localStorage.getItem("faceit_me"));
      const savedTab = localStorage.getItem("faceit_tab") as Mode | null;
      if (savedTab && ["single", "compare", "watch"].includes(savedTab)) setMode(savedTab);
      setWide(localStorage.getItem("faceit_wide") === "1");
    } catch {}
    const params = new URLSearchParams(typeof window !== "undefined" ? window.location.search : "");
    // Compare deep link: prefer plain ?players=a&players=b; fall back to legacy ?compare=<querystring>.
    let players = params.getAll("players");
    if (players.length < 2 && params.get("compare")) {
      players = new URLSearchParams(params.get("compare")!).getAll("players");
    }
    const q = initialQuery || params.get("q");
    if (players.length >= 2) { setInputs(players.slice(0, 5)); runCompareWith(players); return; }
    if (q) { lookup(q); return; }
    searchRef.current?.focus();
  }, [initialQuery, lookup, runCompareWith]);

  // "/" focuses the search box; Esc clears it when focused.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "/" && document.activeElement?.tagName !== "INPUT") {
        e.preventDefault();
        searchRef.current?.focus();
      } else if (e.key === "Escape" && document.activeElement === searchRef.current) {
        setInput("");
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function switchMode(next: Mode) {
    setMode(next);
    setError(null);
    try { localStorage.setItem("faceit_tab", next); } catch {}
  }
  function setInputAt(i: number, v: string) { setInputs((arr) => arr.map((x, j) => (j === i ? v : x))); }
  function addInput() { setInputs((arr) => (arr.length < 5 ? [...arr, ""] : arr)); }
  function removeInput(i: number) { setInputs((arr) => (arr.length > 2 ? arr.filter((_, j) => j !== i) : arr)); }
  function addPreset(nick: string) {
    setInputs((arr) => {
      const empty = arr.findIndex((x) => !x.trim());
      if (empty >= 0) return arr.map((x, j) => (j === empty ? nick : x));
      return arr.length < 5 ? [...arr, nick] : arr.map((x, j) => (j === arr.length - 1 ? nick : x));
    });
  }
  function setAsMe(nick: string) {
    setMe(nick);
    try { localStorage.setItem("faceit_me", nick); } catch {}
    toast.success(`Set ${nick} as you`);
  }
  async function copyCompareLink() {
    const ok = await copyText(comparePermalink(inputs));
    toast[ok ? "success" : "error"](ok ? "Compare link copied" : "Copy failed");
  }
  function toggleWide() {
    setWide((w) => { try { localStorage.setItem("faceit_wide", w ? "0" : "1"); } catch {} return !w; });
  }

  const tab = (m: Mode, label: string, Icon: typeof Search) => (
    <button type="button" onClick={() => switchMode(m)} className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${mode === m ? "bg-white/10 text-white" : "text-slate-400 hover:text-white"}`}>
      <Icon className="h-4 w-4" /> {label}
    </button>
  );

  return (
    <main className={`mx-auto min-h-screen px-5 py-12 transition-[max-width] ${wide ? "max-w-5xl" : "max-w-3xl"}`}>
      <Toaster theme="dark" position="bottom-right" richColors />
      <div className="mb-8 flex items-center justify-between">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
          <ArrowLeft className="h-4 w-4" /> {t("back")}
        </Link>
        <div className="flex items-center gap-2">
          <button onClick={toggleWide} className={`rounded-lg border border-shb-border p-1.5 ${wide ? "bg-white/10 text-white" : "text-slate-400"}`} aria-label="Toggle width" title="Wide layout">
            <Maximize2 className="h-4 w-4" />
          </button>
          <div className="inline-flex rounded-lg border border-shb-border bg-white/5 p-0.5 text-xs">
            {(["ru", "en"] as const).map((l) => (
              <button key={l} onClick={() => setLang(l)} className={`rounded-md px-2.5 py-1 font-semibold uppercase ${lang === l ? "bg-white/10 text-white" : "text-slate-400"}`}>{l}</button>
            ))}
          </div>
        </div>
      </div>

      <h1 className="font-display text-4xl font-bold">FACEIT <span className="text-gradient">Finder</span></h1>
      <p className="mt-2 max-w-xl text-slate-400">{t("subtitle")}</p>

      <div className="mt-6 inline-flex rounded-xl border border-shb-border bg-white/5 p-1">
        {tab("single", t("tabLookup"), Search)}
        {tab("compare", t("tabCompare"), Swords)}
        {tab("watch", t("tabWatch"), Eye)}
      </div>

      {mode === "single" && (
        <>
          <form onSubmit={(e) => { e.preventDefault(); lookup(input); }} className="mt-4 flex flex-col gap-3 sm:flex-row">
            <input ref={searchRef} value={input} onChange={(e) => setInput(e.target.value)} placeholder="FACEIT nickname  ·  steamcommunity.com/id/...  ·  7656119...  ( / )" className={INPUT_CLASS} aria-label="FACEIT nickname, Steam profile URL, or SteamID64" />
            <button type="submit" disabled={loading || !input.trim()} className="cta-gradient flex items-center justify-center gap-2 rounded-xl px-6 py-3 font-semibold text-white disabled:opacity-50">
              <Search className="h-4 w-4" /> {loading ? t("searching") : t("find")}
            </button>
          </form>
          {recent.length > 0 && (
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <span className="text-xs text-slate-500">{lang === "ru" ? "Недавние" : "Recent"}:</span>
              {recent.map((r) => (
                <button key={r} onClick={() => lookup(r)} className="rounded-lg border border-white/10 px-2.5 py-1 text-xs text-slate-300 hover:border-white/25">{r}</button>
              ))}
              {me && <button onClick={() => lookup(me)} className="rounded-lg border border-amber-400/30 px-2.5 py-1 text-xs text-amber-300">★ {me}</button>}
              <button onClick={() => setRecent(clearRecent())} className="text-xs text-slate-500 hover:text-rose-300">✕</button>
            </div>
          )}
        </>
      )}

      {mode === "compare" && (
        <form onSubmit={(e) => { e.preventDefault(); runCompareWith(inputs); }} className="mt-4 space-y-3">
          <div className="space-y-2">
            {inputs.map((v, i) => (
              <div key={i} className="flex items-center gap-2">
                <input value={v} onChange={(e) => setInputAt(i, e.target.value)} placeholder={`#${i + 1} — nickname / Steam link / ID`} className={INPUT_CLASS} aria-label={`Player ${i + 1}`} />
                {inputs.length > 2 && <button type="button" onClick={() => removeInput(i)} className="rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-rose-300" aria-label="Remove player"><X className="h-4 w-4" /></button>}
              </div>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {inputs.length < 5 && <button type="button" onClick={addInput} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-sm text-slate-300 hover:border-white/25"><Plus className="h-3.5 w-3.5" /> {t("addPlayer")}</button>}
            <span className="text-xs text-slate-500">{t("vsPro")}:</span>
            {me && <button type="button" onClick={() => addPreset(me)} className="rounded-lg border border-amber-400/30 px-2.5 py-1 text-xs text-amber-300">★ {me}</button>}
            {PRESET_PROS.map((p) => <button key={p} type="button" onClick={() => addPreset(p)} className="rounded-lg border border-white/10 px-2.5 py-1 text-xs text-slate-300 hover:border-white/25">{p}</button>)}
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="submit" disabled={loading || inputs.filter((v) => v.trim()).length < 2} className="cta-gradient flex items-center justify-center gap-2 rounded-xl px-6 py-3 font-semibold text-white disabled:opacity-50">
              <Swords className="h-4 w-4" /> {loading ? t("comparing") : t("compare")}
            </button>
            {compare && <button type="button" onClick={copyCompareLink} className="rounded-xl border border-white/10 px-4 py-3 text-sm text-slate-300 hover:border-white/25">{lang === "ru" ? "Копировать ссылку" : "Copy link"}</button>}
          </div>
        </form>
      )}

      {error && <div className="mt-6 rounded-xl border border-shb-danger/30 bg-shb-danger/10 p-4 text-rose-50" role="alert">{error}</div>}

      {mode === "single" && loading && !result && <ResultSkeleton />}

      {mode === "single" && !loading && !result && !error && (
        <div className="mt-8 rounded-xl border border-shb-border bg-white/[0.035] p-6 text-center">
          <p className="text-slate-300">{lang === "ru" ? "Введите ник, ссылку Steam или SteamID64. Например:" : "Enter a nickname, Steam link or SteamID64. Try:"}</p>
          <div className="mt-3 flex flex-wrap justify-center gap-2">
            {PRESET_PROS.map((p) => (
              <button key={p} onClick={() => lookup(p)} className="rounded-lg border border-white/10 px-3 py-1.5 text-sm text-slate-200 hover:border-white/25">{p}</button>
            ))}
          </div>
        </div>
      )}

      {mode === "single" && result && !result.found && (
        <div className="mt-6 rounded-xl border border-shb-border bg-white/[0.035] p-6 text-center text-slate-300">{result.message ?? t("notFound")}</div>
      )}
      {mode === "single" && result?.found && (
        <div className="mt-8">
          <div className="mb-3 flex items-center justify-end gap-2">
            {result.nickname && me !== result.nickname && (
              <button onClick={() => setAsMe(result.nickname!)} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1 text-xs text-slate-300 hover:border-amber-400/40 hover:text-amber-300">
                <Star className="h-3.5 w-3.5" /> {lang === "ru" ? "Это я" : "This is me"}
              </button>
            )}
            <button onClick={() => lookup(input, { refresh: true })} disabled={loading} className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1 text-xs text-slate-300 hover:border-white/25 disabled:opacity-50">
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> {lang === "ru" ? "Обновить" : "Refresh"}
            </button>
          </div>
          <PlayerResult result={result} onPick={lookup} />
        </div>
      )}
      {mode === "compare" && compare && <div className="mt-8"><CompareView players={compare.players} /></div>}
      {mode === "watch" && <WatchlistTab onPick={lookup} />}
    </main>
  );
}

function ResultSkeleton() {
  return (
    <div className="mt-8 animate-pulse space-y-5">
      <div className="premium-card flex items-center gap-5 rounded-2xl p-6">
        <div className="h-[72px] w-[72px] rounded-xl bg-white/10" />
        <div className="flex-1 space-y-2">
          <div className="h-5 w-40 rounded bg-white/10" />
          <div className="h-3 w-24 rounded bg-white/5" />
        </div>
        <div className="h-16 w-16 rounded-2xl bg-white/10" />
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[0, 1, 2, 3].map((i) => <div key={i} className="premium-card h-20 rounded-xl" />)}
      </div>
      <div className="premium-card h-44 rounded-xl" />
    </div>
  );
}

export function FaceitClient({ initialQuery }: { initialQuery?: string }) {
  return (
    <I18nProvider>
      <WatchlistProvider>
        <FaceitInner initialQuery={initialQuery} />
      </WatchlistProvider>
    </I18nProvider>
  );
}
