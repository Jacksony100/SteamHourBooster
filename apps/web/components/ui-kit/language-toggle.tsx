"use client";

import { Languages } from "lucide-react";

import { useLanguage } from "@/components/language-provider";
import { languages, type LanguageCode } from "@/lib/i18n";

export function LanguageToggle() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <label className="inline-flex h-11 items-center gap-2 rounded-xl border border-shb-border bg-shb-surface px-3 text-sm font-semibold text-slate-200">
      <Languages className="h-4 w-4 text-sky-200" />
      <span className="sr-only">{t.shell.language}</span>
      <select
        className="bg-transparent text-sm font-semibold outline-none"
        value={language}
        onChange={(event) => setLanguage(event.target.value as LanguageCode)}
        aria-label={t.shell.language}
      >
        {languages.map((item) => (
          <option key={item.code} value={item.code} className="bg-slate-950 text-white">
            {item.label}
          </option>
        ))}
      </select>
    </label>
  );
}
