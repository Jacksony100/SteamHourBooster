"use client";

import { ThemeProvider } from "next-themes";

import { LanguageProvider } from "@/components/language-provider";
import { PremiumToaster } from "@/components/ui-kit/toast";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} storageKey="deckpilot-theme" themes={["light", "dark", "full-dark"]}>
      <LanguageProvider>{children}</LanguageProvider>
      <PremiumToaster />
    </ThemeProvider>
  );
}
