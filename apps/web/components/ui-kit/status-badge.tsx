import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";
import type { StatusTone } from "@/lib/design-tokens";

const badgeVariants = cva(
  "inline-flex items-center gap-2 rounded-md border px-2.5 py-1 text-xs font-semibold",
  {
    variants: {
      tone: {
        online: "border-shb-success/30 bg-shb-success/10 text-emerald-100",
        success: "border-shb-success/30 bg-shb-success/10 text-emerald-100",
        offline: "border-white/10 bg-white/5 text-shb-muted",
        session: "border-shb-primary/30 bg-shb-primary/10 text-sky-100",
        warning: "border-shb-warning/35 bg-shb-warning/10 text-amber-100",
        error: "border-shb-danger/35 bg-shb-danger/10 text-rose-100",
        admin: "border-shb-violet/35 bg-shb-violet/10 text-violet-100"
      } satisfies Record<StatusTone, string>
    },
    defaultVariants: {
      tone: "offline"
    }
  }
);

const dotClass: Record<StatusTone, string> = {
  online: "status-dot-online",
  success: "status-dot-success",
  offline: "",
  session: "status-dot-session",
  warning: "status-dot-warning",
  error: "status-dot-error",
  admin: "status-dot-primary"
};

export interface StatusBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  showDot?: boolean;
}

export function StatusBadge({ tone = "offline", showDot = true, className, children, ...props }: StatusBadgeProps) {
  const resolvedTone = tone ?? "offline";

  return (
    <span className={cn(badgeVariants({ tone: resolvedTone }), className)} {...props}>
      {showDot && <span aria-hidden="true" className={cn("status-dot", dotClass[resolvedTone])} />}
      {children}
    </span>
  );
}
