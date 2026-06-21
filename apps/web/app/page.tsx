"use client";

import Link from "next/link";
import { Activity, ArrowRight, BarChart3, CreditCard, Gamepad2, KeyRound, Layers3, ShieldCheck, Sparkles } from "lucide-react";

import { useLanguage } from "@/components/language-provider";
import { LegalFooter } from "@/components/legal-footer";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { LanguageToggle } from "@/components/ui-kit/language-toggle";
import { ThemeToggle } from "@/components/ui-kit/theme-toggle";
import { SystemModeBanner } from "@/features/system/system-mode-banner";
import { product } from "@/lib/product";

const featureIcons = [KeyRound, Activity, Gamepad2, CreditCard, ShieldCheck, Layers3];

export default function HomePage() {
  const { t } = useLanguage();

  return (
    <main className="min-h-screen overflow-hidden">
      <header className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-5 py-5">
        <Link href="/" className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl border border-sky-300/30 bg-sky-300/15 font-black shadow-glow">{product.shortName}</div>
          <div>
            <div className="font-black">{product.name}</div>
            <div className="text-xs text-slate-400">{product.tagline}</div>
          </div>
        </Link>
        <div className="flex flex-wrap items-center justify-end gap-2">
          <ThemeToggle />
          <LanguageToggle />
          <Button asChild variant="ghost">
            <Link href="/login">{t.auth.submitLogin}</Link>
          </Button>
        </div>
      </header>

      <div className="mx-auto w-full max-w-7xl px-5">
        <SystemModeBanner />
      </div>

      <section className="mx-auto grid w-full max-w-7xl items-center gap-10 px-5 pb-14 pt-10 lg:grid-cols-[1.05fr_0.95fr] lg:pt-20">
        <div className="space-y-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-sky-300/20 bg-sky-300/10 px-3 py-1 text-sm font-semibold text-sky-200">
            <Sparkles className="h-4 w-4" />
            {t.landing.eyebrow}
          </div>
          <div className="space-y-5">
            <h1 className="text-gradient max-w-4xl text-5xl font-black leading-[0.98] tracking-tight md:text-7xl">{t.landing.headline}</h1>
            <p className="max-w-2xl text-lg leading-8 text-slate-300">{t.landing.body}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <Link href="/dashboard">
                {t.landing.primaryCta}
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="ghost">
              <Link href="/register">{t.landing.secondaryCta}</Link>
            </Button>
            <Button asChild variant="ghost">
              <Link href="#pricing">{t.landing.demoCta}</Link>
            </Button>
          </div>
        </div>

        <div className="relative">
          <Card className="interactive-card space-y-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-sky-200">{product.name}</div>
                <h2 className="mt-1 text-2xl font-black">{t.landing.offerTitle}</h2>
              </div>
              <BarChart3 className="h-7 w-7 text-sky-200" />
            </div>
            <p className="text-sm leading-7 text-slate-300">{t.landing.offerBody}</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {t.landing.metrics.map((metric, index) => (
                <div key={metric} className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <div className="text-3xl font-black">{["12", "4", "38", "1.2k"][index]}</div>
                  <div className="mt-1 text-sm text-slate-400">{metric}</div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </section>

      <section className="mx-auto grid w-full max-w-7xl gap-4 px-5 pb-16 md:grid-cols-2 lg:grid-cols-3">
        {t.landing.features.map((feature, index) => {
          const Icon = featureIcons[index] || Layers3;
          return (
            <Card key={feature} className="interactive-card">
              <Icon className="h-5 w-5 text-sky-200" />
              <div className="mt-4 text-lg font-bold">{feature}</div>
              <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                <div className="h-full w-2/3 rounded-full bg-gradient-to-r from-sky-400 to-emerald-300" />
              </div>
            </Card>
          );
        })}
      </section>

      <section id="pricing" className="mx-auto grid w-full max-w-7xl gap-6 px-5 pb-20 lg:grid-cols-[0.8fr_1.2fr]">
        <div>
          <h2 className="text-3xl font-black">{t.landing.pricingTitle}</h2>
          <p className="mt-3 max-w-xl text-sm leading-7 text-slate-300">{t.landing.pricingBody}</p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {[
            ["Trial", "$0", "1 account"],
            ["Starter", "$9", "3 accounts"],
            ["Pro", "$19", "10 accounts"]
          ].map(([name, price, limit]) => (
            <Card key={name} className="interactive-card">
              <div className="text-sm font-semibold text-slate-400">{name}</div>
              <div className="mt-3 text-3xl font-black">{price}</div>
              <div className="mt-2 text-sm text-slate-400">{limit}</div>
            </Card>
          ))}
        </div>
      </section>
      <LegalFooter />
    </main>
  );
}
