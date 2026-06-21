import type { Route } from "next";
import Link from "next/link";

const links = [
  { href: "/terms" as Route, label: "Terms" },
  { href: "/privacy" as Route, label: "Privacy" },
  { href: "/security" as Route, label: "Security" },
  { href: "/status" as Route, label: "Status" }
];

export function LegalFooter() {
  return (
    <footer className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-8 text-xs text-slate-500">
      <div>DeckPilot beta. Not affiliated with Valve or Steam.</div>
      <nav className="flex flex-wrap gap-3">
        {links.map((link) => (
          <Link key={link.href} className="font-semibold text-slate-400 hover:text-sky-200" href={link.href}>
            {link.label}
          </Link>
        ))}
      </nav>
    </footer>
  );
}
