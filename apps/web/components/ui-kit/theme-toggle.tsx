"use client";

import { MonitorDot, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

import { useLanguage } from "@/components/language-provider";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const { t } = useLanguage();
  const themes = [
    { value: "light", label: t.shell.lightTheme, icon: Sun },
    { value: "dark", label: t.shell.darkTheme, icon: Moon },
    { value: "full-dark", label: t.shell.fullDarkTheme, icon: MonitorDot }
  ] as const;

  return (
    <div className="inline-flex rounded-xl border border-shb-border bg-shb-surface p-1" aria-label="Theme selector">
      {themes.map((item) => {
        const Icon = item.icon;
        const active = (theme || "dark") === item.value;
        return (
          <button
            key={item.value}
            type="button"
            className={`inline-flex h-9 items-center gap-2 rounded-lg px-3 text-xs font-semibold transition ${
              active ? "bg-sky-400 text-slate-950 shadow-glow" : "text-slate-300 hover:bg-white/10 hover:text-white"
            }`}
            onClick={() => setTheme(item.value)}
            aria-pressed={active}
          >
            <Icon className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{item.label}</span>
          </button>
        );
      })}
    </div>
  );
}
