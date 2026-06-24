"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type Lang = "ru" | "en";

const DICT: Record<string, { ru: string; en: string }> = {
  back: { ru: "На главную", en: "Back to home" },
  subtitle: {
    ru: "Полная статистика FACEIT CS2 — уровень, ELO, тренд ELO, разбивка по картам, последние матчи, тиммейты и форма. По нику FACEIT, ссылке Steam или SteamID64. Или сравните до 5 игроков. Без входа.",
    en: "Full FACEIT CS2 stats — level, ELO, ELO trend, per-map breakdown, recent matches, teammates and form. From a FACEIT nickname, Steam link or SteamID64. Or compare up to 5 players. No login.",
  },
  tabLookup: { ru: "Поиск", en: "Lookup" },
  tabCompare: { ru: "Сравнение", en: "Compare" },
  tabWatch: { ru: "Избранное", en: "Watchlist" },
  find: { ru: "Найти", en: "Find" },
  searching: { ru: "Ищу…", en: "Searching…" },
  compare: { ru: "Сравнить", en: "Compare" },
  comparing: { ru: "Сравниваю…", en: "Comparing…" },
  addPlayer: { ru: "Добавить игрока", en: "Add player" },
  vsPro: { ru: "Сравнить с про", en: "Compare with a pro" },
  notFound: { ru: "Профиль FACEIT не найден.", en: "No FACEIT profile found." },
  eloTrend: { ru: "Тренд ELO", en: "ELO trend" },
  recentResults: { ru: "Последние результаты", en: "Recent results" },
  byMap: { ru: "По картам", en: "By map" },
  lastMatches: { ru: "Последние матчи", en: "Last matches" },
  recentForm: { ru: "Текущая форма", en: "Recent form" },
  winRate: { ru: "Винрейт", en: "Win rate" },
  matches: { ru: "Матчи", en: "Matches" },
  headshots: { ru: "Хедшоты", en: "Headshots" },
  teammates: { ru: "Частые тиммейты", en: "Frequent teammates" },
  streakWin: { ru: "Серия побед", en: "Win streak" },
  streakLoss: { ru: "Серия поражений", en: "Loss streak" },
  tilt: { ru: "Возможный тилт", en: "Possible tilt" },
  smurf: { ru: "Похоже на смурфа", en: "Possible smurf" },
  smurfNote: { ru: "Эвристика, не доказательство", en: "Heuristic, not proof" },
  nextLevel: { ru: "До следующего уровня", en: "To next level" },
  maxLevel: { ru: "Максимальный уровень", en: "Max level reached" },
  steam: { ru: "Профиль Steam", en: "Steam profile" },
  hours: { ru: "часов в CS2", en: "CS2 hours" },
  steamLevel: { ru: "Уровень Steam", en: "Steam level" },
  account: { ru: "Аккаунту", en: "Account age" },
  years: { ru: "лет", en: "yrs" },
  vacClean: { ru: "VAC чист", en: "VAC clean" },
  vacBanned: { ru: "VAC-бан", en: "VAC banned" },
  watch: { ru: "В избранное", en: "Watch" },
  watching: { ru: "В избранном", en: "Watching" },
  shareCard: { ru: "Скачать карточку", en: "Download card" },
  openProfile: { ru: "Профиль FACEIT", en: "FACEIT profile" },
  bestMap: { ru: "Лучшая карта", en: "Best map" },
  worstMap: { ru: "Худшая карта", en: "Worst map" },
  vetoHint: { ru: "Совет по вето", en: "Veto tip" },
  pick: { ru: "пикать", en: "pick" },
  ban: { ru: "банить", en: "ban" },
  teamAvg: { ru: "Средние по команде", en: "Team averages" },
  sinceLast: { ru: "с прошлой проверки", en: "since last check" },
  empty: { ru: "Пусто", en: "Empty" },
  watchEmpty: { ru: "Список пуст. Найдите игрока и нажмите «В избранное».", en: "Empty. Look a player up and hit Watch." },
};

type Ctx = { lang: Lang; setLang: (l: Lang) => void; t: (k: keyof typeof DICT) => string };
const I18nContext = createContext<Ctx>({ lang: "ru", setLang: () => {}, t: (k) => DICT[k]?.ru ?? String(k) });

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("ru");
  useEffect(() => {
    const saved = (typeof localStorage !== "undefined" && localStorage.getItem("faceit_lang")) as Lang | null;
    if (saved === "ru" || saved === "en") {
      setLangState(saved);
    } else if (typeof navigator !== "undefined" && !navigator.language.toLowerCase().startsWith("ru")) {
      setLangState("en"); // first visit: default RU, but switch to EN for non-RU browsers
    }
  }, []);
  const setLang = (l: Lang) => {
    setLangState(l);
    try { localStorage.setItem("faceit_lang", l); } catch {}
  };
  const t = (k: keyof typeof DICT) => DICT[k]?.[lang] ?? DICT[k]?.en ?? String(k);
  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}
