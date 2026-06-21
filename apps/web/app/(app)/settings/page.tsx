"use client";

import { useLanguage } from "@/components/language-provider";
import { Card, CardTitle } from "@/components/ui/card";
import { LanguageToggle } from "@/components/ui-kit/language-toggle";
import { ThemeToggle } from "@/components/ui-kit/theme-toggle";
import { SettingsSecurityClient } from "@/features/settings/settings-security-client";

export default function SettingsPage() {
  const { t } = useLanguage();

  return (
    <div className="grid gap-6">
      <Card>
        <CardTitle>{t.settings.title}</CardTitle>
        <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">{t.settings.body}</p>
      </Card>
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardTitle>{t.settings.theme}</CardTitle>
          <div className="mt-5">
            <ThemeToggle />
          </div>
        </Card>
        <Card>
          <CardTitle>{t.settings.language}</CardTitle>
          <div className="mt-5">
            <LanguageToggle />
          </div>
        </Card>
      </div>
      <SettingsSecurityClient />
    </div>
  );
}
