"use client";

import type { Route } from "next";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Command,
  Gamepad2,
  LayoutDashboard,
  LifeBuoy,
  LogOut,
  PlaySquare,
  ScrollText,
  Settings,
  Shield,
  Users,
  WalletCards,
  type LucideIcon
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { useLanguage } from "@/components/language-provider";
import { Button } from "@/components/ui/button";
import { LanguageToggle } from "@/components/ui-kit/language-toggle";
import { ThemeToggle } from "@/components/ui-kit/theme-toggle";
import { CommandPalette } from "@/features/command-palette";
import { SystemModeBanner } from "@/features/system/system-mode-banner";
import { api } from "@/lib/api";
import { product } from "@/lib/product";
import type { CurrentUser } from "@/lib/server-auth";

export function AppShell({ children, currentUser }: { children: React.ReactNode; currentUser: CurrentUser }) {
  const pathname = usePathname();
  const router = useRouter();
  const [commandOpen, setCommandOpen] = useState(false);
  const { t } = useLanguage();

  const allNav: Array<{ href: Route; label: string; icon: LucideIcon; adminOnly?: boolean }> = [
    { href: "/dashboard", label: t.nav.dashboard, icon: LayoutDashboard },
    { href: "/accounts", label: t.nav.accounts, icon: Users },
    { href: "/sessions", label: t.nav.sessions, icon: PlaySquare },
    { href: "/games", label: t.nav.games, icon: Gamepad2 },
    { href: "/billing", label: t.nav.billing, icon: WalletCards },
    { href: "/logs", label: t.nav.logs, icon: ScrollText },
    { href: "/support", label: t.nav.support, icon: LifeBuoy },
    { href: "/admin", label: t.nav.admin, icon: Shield, adminOnly: true },
    { href: "/settings", label: t.nav.settings, icon: Settings }
  ];
  const nav = allNav.filter((item) => !item.adminOnly || currentUser.is_admin);
  const currentPage = nav.find((item) => pathname.startsWith(item.href))?.label || product.name;

  async function logout() {
    await api("/api/v1/auth/logout", { method: "POST", csrf: true });
    toast.success(t.shell.signedOut);
    router.push("/login");
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-[268px_1fr]">
      <aside className="border-b border-shb-border bg-shb-surface p-5 backdrop-blur-2xl lg:border-b-0 lg:border-r">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl border border-sky-300/30 bg-sky-300/15 font-black shadow-glow">{product.shortName}</div>
          <div className="min-w-0">
            <div className="truncate font-black">{product.name}</div>
            <div className="truncate text-xs text-slate-400">{product.tagline}</div>
          </div>
        </Link>
        <nav className="mt-5 flex gap-2 overflow-x-auto pb-1 lg:mt-8 lg:grid lg:overflow-visible lg:pb-0">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex shrink-0 items-center gap-3 rounded-xl px-3 py-2 text-sm font-semibold transition ${
                pathname.startsWith(item.href) ? "bg-sky-400 text-slate-950 shadow-glow" : "text-slate-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          ))}
        </nav>
        <nav className="mt-6 hidden gap-3 text-xs text-slate-500 lg:flex lg:flex-wrap">
          <Link className="hover:text-sky-200" href={"/terms" as Route}>Terms</Link>
          <Link className="hover:text-sky-200" href={"/privacy" as Route}>Privacy</Link>
          <Link className="hover:text-sky-200" href={"/security" as Route}>Security</Link>
          <Link className="hover:text-sky-200" href={"/status" as Route}>Status</Link>
        </nav>
      </aside>
      <main className="min-w-0 p-5 lg:p-8">
        <header className="mb-7 flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-sky-200">{product.name}</div>
            <h1 className="text-3xl font-black">{currentPage}</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <ThemeToggle />
            <LanguageToggle />
            <Button variant="ghost" onClick={() => setCommandOpen(true)}>
              <Command className="h-4 w-4" />
              {t.shell.command}
            </Button>
            <Button variant="danger" onClick={logout}>
              <LogOut className="h-4 w-4" />
              {t.shell.logout}
            </Button>
          </div>
        </header>
        <SystemModeBanner />
        {children}
      </main>
      <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} currentUser={currentUser} />
    </div>
  );
}
