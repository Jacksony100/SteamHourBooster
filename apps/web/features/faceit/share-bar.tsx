"use client";

import { toast } from "sonner";
import { Code2, Copy, Download, ExternalLink, Hash, Send, Share2 } from "lucide-react";

import { useI18n } from "./i18n";
import {
  copyText, downloadJson, embedHtml, embedMarkdown, externalLinks, permalinkFor,
  telegramShareUrl, vkShareUrl, xShareUrl,
} from "./share";
import type { FaceitResult } from "./types";

const BTN = "inline-flex items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1.5 text-sm text-slate-200 transition hover:border-white/25";

export function ShareBar({ result }: { result: FaceitResult }) {
  const { lang } = useI18n();
  const nick = result.nickname;

  async function copy(text: string, msg: string) {
    const ok = await copyText(text);
    if (ok) toast.success(msg);
    else toast.error("Copy failed");
  }

  return (
    <div className="premium-card rounded-xl p-4">
      <div className="mb-3 flex items-center gap-1.5 text-xs uppercase tracking-wide text-slate-400">
        <Share2 className="h-3.5 w-3.5" /> Share &amp; embed
      </div>
      <div className="flex flex-wrap gap-2">
        {nick && <button className={BTN} onClick={() => copy(permalinkFor(nick), "Link copied")}><Copy className="h-3.5 w-3.5" /> {lang === "ru" ? "Ссылка" : "Link"}</button>}
        {nick && <button className={BTN} onClick={() => copy(embedMarkdown(nick), "Embed markdown copied")}><Code2 className="h-3.5 w-3.5" /> MD</button>}
        {nick && <button className={BTN} onClick={() => copy(embedHtml(nick), "Embed HTML copied")}><Code2 className="h-3.5 w-3.5" /> HTML</button>}
        <a className={BTN} href={xShareUrl(result)} target="_blank" rel="noopener noreferrer"><Share2 className="h-3.5 w-3.5" /> X</a>
        <a className={BTN} href={telegramShareUrl(result)} target="_blank" rel="noopener noreferrer"><Send className="h-3.5 w-3.5" /> Telegram</a>
        <a className={BTN} href={vkShareUrl(result)} target="_blank" rel="noopener noreferrer"><Share2 className="h-3.5 w-3.5" /> VK</a>
        <button className={BTN} onClick={() => downloadJson(result)}><Download className="h-3.5 w-3.5" /> JSON</button>
        {nick && <button className={BTN} onClick={() => copy(nick, "Nickname copied")}><Copy className="h-3.5 w-3.5" /> Nick</button>}
        {result.steamid64 && <button className={BTN} onClick={() => copy(result.steamid64!, "SteamID64 copied")}><Hash className="h-3.5 w-3.5" /> SteamID64</button>}
        {result.player_id && <button className={BTN} onClick={() => copy(result.player_id!, "FACEIT ID copied")}><Hash className="h-3.5 w-3.5" /> FACEIT ID</button>}
        {externalLinks(result).map((l) => (
          <a key={l.label} className={BTN} href={l.url} target="_blank" rel="noopener noreferrer">{l.label} <ExternalLink className="h-3 w-3" /></a>
        ))}
      </div>
    </div>
  );
}
