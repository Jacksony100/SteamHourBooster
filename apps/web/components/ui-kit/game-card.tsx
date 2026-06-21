import * as React from "react";
import { CheckCircle2 } from "lucide-react";

import { cn } from "@/lib/utils";

export interface GameCardProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  name: string;
  appId: number | string;
  selected?: boolean;
  active?: boolean;
}

export function GameCard({ name, appId, selected = false, active = false, className, ...props }: GameCardProps) {
  return (
    <button
      type="button"
      className={cn(
        "interactive-card min-h-[96px] rounded-xl border p-4 text-left focus-ring",
        selected ? "border-shb-primary/45 bg-shb-primary/10 shadow-glow-primary" : "border-shb-border bg-white/[0.035] hover:bg-white/[0.06]",
        className
      )}
      aria-pressed={selected}
      {...props}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate font-bold text-shb-text">{name}</div>
          <div className="mt-1 text-xs text-shb-muted">AppID {appId}</div>
        </div>
        {selected && <CheckCircle2 className="h-5 w-5 text-shb-primary" />}
      </div>
      {active && <div className="mt-3 inline-flex items-center gap-2 text-xs font-semibold text-shb-success"><span className="status-dot status-dot-success" />Active now</div>}
    </button>
  );
}
