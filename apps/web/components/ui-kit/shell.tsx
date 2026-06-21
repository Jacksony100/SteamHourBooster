"use client";

import * as React from "react";
import type { Route } from "next";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Command, LayoutDashboard, Settings, Shield, WalletCards, type LucideIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui-kit/status-badge";
import { ThemeToggle } from "@/components/ui-kit/theme-toggle";
import { LanguageToggle } from "@/components/ui-kit/language-toggle";
import { product } from "@/lib/product";
import { cn } from "@/lib/utils";

export type ShellNavItem = {
  href: Route;
  label: string;
  icon: LucideIcon;
  badge?: string;
};

export const defaultShellNav: ShellNavItem[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/billing", label: "Billing", icon: WalletCards },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/admin", label: "Admin", icon: Shield }
];

export interface SidebarProps {
  items?: ShellNavItem[];
  safetyNotice?: string;
}

export function Sidebar({ items = defaultShellNav, safetyNotice }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside className="hidden min-h-screen border-r border-shb-border bg-shb-bg-2/70 p-5 backdrop-blur-2xl lg:block">
      <Link href="/dashboard" className="flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-lg border border-shb-primary/30 bg-shb-primary/15 font-black text-sky-100 shadow-glow-primary">{product.shortName}</div>
        <div className="min-w-0">
          <div className="truncate font-black text-shb-text">{product.name}</div>
          <div className="text-xs text-shb-muted">{product.tagline}</div>
        </div>
      </Link>

      <nav className="mt-8 grid gap-2" aria-label="Primary navigation">
        {items.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center justify-between gap-3 rounded-md border px-3 py-2.5 text-sm font-semibold transition",
                active ? "border-shb-primary/35 bg-shb-primary/10 text-white shadow-glow-primary" : "border-transparent text-shb-muted hover:border-white/10 hover:bg-white/5 hover:text-white"
              )}
            >
              <span className="flex items-center gap-3">
                <item.icon className="h-4 w-4" />
                {item.label}
              </span>
              {item.badge && <span className="rounded-sm bg-white/10 px-1.5 py-0.5 text-[10px]">{item.badge}</span>}
            </Link>
          );
        })}
      </nav>

      {safetyNotice && <div className="mt-8 rounded-lg border border-shb-success/20 bg-shb-success/10 p-4 text-sm leading-6 text-emerald-100">{safetyNotice}</div>}
    </aside>
  );
}

export interface TopbarProps {
  title: string;
  subtitle?: string;
  subscriptionLabel?: string;
  onCommandOpen?: () => void;
  actions?: React.ReactNode;
}

export function Topbar({ title, subtitle, subscriptionLabel = "Subscription active", onCommandOpen, actions }: TopbarProps) {
  return (
    <header className="mb-7 flex flex-wrap items-center justify-between gap-3">
      <div>
        <div className="text-sm font-semibold text-shb-primary">{product.name}</div>
        <h1 className="text-2xl font-black text-shb-text md:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-shb-muted">{subtitle}</p>}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <StatusBadge tone="success">{subscriptionLabel}</StatusBadge>
        <ThemeToggle />
        <LanguageToggle />
        <Button variant="ghost" onClick={onCommandOpen} aria-label="Open command palette">
          <Command className="h-4 w-4" />
          Command
        </Button>
        {actions}
      </div>
    </header>
  );
}

export interface UiKitAppShellProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  navItems?: ShellNavItem[];
  topbarActions?: React.ReactNode;
  onCommandOpen?: () => void;
}

export function UiKitAppShell({ title, subtitle, children, navItems, topbarActions, onCommandOpen }: UiKitAppShellProps) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[280px_1fr]">
      <Sidebar items={navItems} />
      <main className="min-w-0 p-4 md:p-6 lg:p-8">
        <Topbar title={title} subtitle={subtitle} onCommandOpen={onCommandOpen} actions={topbarActions} />
        {children}
      </main>
    </div>
  );
}
