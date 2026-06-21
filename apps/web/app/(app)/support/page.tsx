import Link from "next/link";
import { BookOpen, LifeBuoy, ShieldCheck } from "lucide-react";

const cards = [
  {
    icon: BookOpen,
    title: "Documentation",
    body: "Architecture, security, billing, and the Steam data integration are documented in the repo's docs/ folder.",
  },
  {
    icon: ShieldCheck,
    title: "Safety scope",
    body: "DeckPilot is a transparent manager for accounts you own. It never bypasses Steam Guard, anti-fraud, or platform rules.",
  },
  {
    icon: LifeBuoy,
    title: "Demo mode",
    body: "Steam session activity runs in a clearly-labeled demo mode in this build. Real official linking is gated and opt-in.",
  },
];

export default function SupportPage() {
  return (
    <div className="space-y-6">
      <div className="premium-card rounded-2xl p-6">
        <h2 className="font-display text-2xl font-bold text-white">How can we help?</h2>
        <p className="mt-2 max-w-2xl text-sm text-slate-400">
          This is a closed/demo beta. For issues or feedback, reach the workspace owner. Account recovery emails are sent when an email
          provider is configured; otherwise contact the owner directly.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link href="/billing" className="cta-gradient rounded-xl px-4 py-2 text-sm font-semibold text-white">
            View plans
          </Link>
          <Link href="/settings" className="rounded-xl border border-shb-border px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-white/5">
            Account settings
          </Link>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {cards.map((card) => (
          <div key={card.title} className="premium-card rounded-xl p-5">
            <card.icon className="h-5 w-5 text-sky-300" />
            <div className="mt-3 font-semibold text-white">{card.title}</div>
            <p className="mt-1 text-sm text-slate-400">{card.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
