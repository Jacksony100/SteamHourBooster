import Link from "next/link";
import type { Route } from "next";
import { ArrowRight } from "lucide-react";

const steps: { n: number; title: string; body: string; href: Route; cta: string }[] = [
  { n: 1, title: "Add a Steam account you own", body: "Attest ownership and link an account. Credentials are encrypted; Steam Guard codes are never stored.", href: "/accounts", cta: "Add account" },
  { n: 2, title: "Browse the library & pick games", body: "Pull profile + owned-games artwork from Steam and select which games to track.", href: "/games", cta: "Open games" },
  { n: 3, title: "Run a transparent demo session", body: "Start a visible demo session from the dashboard and watch the lifecycle and logs update.", href: "/dashboard", cta: "Go to dashboard" },
  { n: 4, title: "Choose a plan", body: "Trial is active by default. Upgrade for more accounts and active sessions when you need them.", href: "/billing", cta: "View plans" },
];

export default function OnboardingPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <div className="text-sm font-semibold text-sky-200">Getting started</div>
        <h2 className="font-display text-3xl font-bold text-white">Set up your workspace in four steps</h2>
        <p className="mt-2 text-sm text-slate-400">A transparent console for accounts you own — encrypted, logged, and fully under your control.</p>
      </div>
      <div className="space-y-3">
        {steps.map((step) => (
          <div key={step.n} className="premium-card flex items-center gap-4 rounded-xl p-5">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl text-white" style={{ background: "var(--shb-icon-gradient)" }}>
              {step.n}
            </div>
            <div className="min-w-0 flex-1">
              <div className="font-semibold text-white">{step.title}</div>
              <p className="text-sm text-slate-400">{step.body}</p>
            </div>
            <Link href={step.href} className="flex shrink-0 items-center gap-1.5 rounded-lg border border-shb-border px-3 py-2 text-sm font-semibold text-slate-200 hover:bg-white/5">
              {step.cta}
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
