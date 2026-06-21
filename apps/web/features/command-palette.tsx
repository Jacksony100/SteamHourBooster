"use client";

import * as Dialog from "@radix-ui/react-dialog";
import type { Route } from "next";
import Link from "next/link";

import { useLanguage } from "@/components/language-provider";
import { Input } from "@/components/ui/input";
import type { CurrentUser } from "@/lib/server-auth";

export function CommandPalette({ open, onOpenChange, currentUser }: { open: boolean; onOpenChange: (open: boolean) => void; currentUser: CurrentUser }) {
  const { t } = useLanguage();
  const allCommands: Array<[Route, string, boolean?]> = [
    ["/dashboard", t.nav.dashboard],
    ["/admin", t.nav.admin, true],
    ["/billing", t.nav.billing],
    ["/settings", t.nav.settings]
  ];
  const commands = allCommands.filter(([, , adminOnly]) => !adminOnly || currentUser.is_admin);

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
        <Dialog.Content className="glass fixed left-1/2 top-24 w-[min(640px,calc(100vw-32px))] -translate-x-1/2 rounded-2xl p-4">
          <Dialog.Title className="mb-3 text-lg font-bold">{t.shell.command}</Dialog.Title>
          <Input placeholder="Search commands..." autoFocus />
          <div className="mt-4 grid gap-2 text-sm">
            {commands.map(([href, label]) => (
              <Link key={href} href={href} onClick={() => onOpenChange(false)} className="rounded-xl border border-white/10 bg-white/5 p-3 hover:bg-white/10">
                {label}
              </Link>
            ))}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
