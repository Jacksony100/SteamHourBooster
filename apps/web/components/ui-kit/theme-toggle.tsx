"use client";

import { useEffect, useState } from "react";
import { MonitorDot, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

import { useLanguage } from "@/components/language-provider";

const ORDER = ["light", "dark", "full-dark"] as const;
type ThemeValue = (typeof ORDER)[number];

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const { t } = useLanguage();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const meta: Record<ThemeValue, { label: string; icon: typeof Sun }> = {
    light: { label: t.shell.lightTheme, icon: Sun },
    dark: { label: t.shell.darkTheme, icon: Moon },
    "full-dark": { label: t.shell.fullDarkTheme, icon: MonitorDot },
  };

  // Default to "dark" until mounted so SSR and the first client render match.
  const active: ThemeValue = mounted && (theme as ThemeValue) in meta ? (theme as ThemeValue) : "dark";
  const { label, icon: Icon } = meta[active];

  function cycle() {
    const i = ORDER.indexOf((theme as ThemeValue) ?? "dark");
    setTheme(ORDER[(i + 1) % ORDER.length]);
  }

  return (
    <button
      type="button"
      onClick={cycle}
      title={label}
      aria-label={`Theme: ${label}`}
      className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-lg border border-shb-border bg-shb-surface text-slate-300 transition hover:bg-white/10 hover:text-white"
    >
      <Icon className="h-4 w-4" />
    </button>
  );
}
