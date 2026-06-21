"use client";

import * as React from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface DrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export function Drawer({ open, onOpenChange, title, description, children, footer, className }: DrawerProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/65 backdrop-blur-sm" />
        <Dialog.Content className={cn("glass fixed bottom-0 right-0 top-0 z-50 flex w-[min(520px,100vw)] flex-col rounded-l-xl border-r-0 p-5 shadow-glass animate-drawer-in", className)}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <Dialog.Title className="text-xl font-black text-shb-text">{title}</Dialog.Title>
              {description && <Dialog.Description className="mt-2 text-sm leading-6 text-shb-muted">{description}</Dialog.Description>}
            </div>
            <Dialog.Close asChild>
              <Button variant="ghost" aria-label="Close drawer" className="h-9 w-9 px-0">
                <X className="h-4 w-4" />
              </Button>
            </Dialog.Close>
          </div>
          <div className="mt-6 min-h-0 flex-1 overflow-y-auto pr-1">{children}</div>
          {footer && <div className="mt-6 flex flex-wrap justify-end gap-2 border-t border-white/10 pt-4">{footer}</div>}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
