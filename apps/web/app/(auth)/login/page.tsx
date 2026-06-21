"use client";

import Link from "next/link";

import { useLanguage } from "@/components/language-provider";
import { LegalFooter } from "@/components/legal-footer";
import { LanguageToggle } from "@/components/ui-kit/language-toggle";
import { ThemeToggle } from "@/components/ui-kit/theme-toggle";
import { AuthForm } from "@/features/auth/auth-form";
import { product } from "@/lib/product";

export default function LoginPage() {
  const { t } = useLanguage();

  return (
    <main className="min-h-screen">
      <div className="mx-auto grid w-full max-w-6xl items-center gap-8 px-6 py-12 md:min-h-[calc(100vh-96px)] md:grid-cols-[1.2fr_0.8fr]">
        <section className="space-y-6">
          <Link href="/" className="inline-flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-xl border border-sky-300/30 bg-sky-300/15 font-black shadow-glow">{product.shortName}</div>
            <div>
              <div className="font-black">{product.name}</div>
              <div className="text-xs text-slate-400">{product.tagline}</div>
            </div>
          </Link>
          <div className="flex flex-wrap gap-2">
            <ThemeToggle />
            <LanguageToggle />
          </div>
          <div className="w-fit rounded-full border border-sky-300/20 bg-sky-300/10 px-3 py-1 text-sm font-semibold text-sky-200">{t.auth.loginEyebrow}</div>
          <h1 className="text-gradient text-5xl font-black md:text-7xl">{t.auth.loginHeadline}</h1>
          <p className="max-w-xl text-lg leading-8 text-slate-300">{t.auth.loginBody}</p>
          <Link className="text-sm font-semibold text-sky-200" href="/register">
            {t.auth.noAccount}
          </Link>
        </section>
        <AuthForm mode="login" />
      </div>
      <LegalFooter />
    </main>
  );
}
