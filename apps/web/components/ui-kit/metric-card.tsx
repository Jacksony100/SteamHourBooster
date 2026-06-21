import * as React from "react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { StatusTone } from "@/lib/design-tokens";
import { StatusBadge } from "@/components/ui-kit/status-badge";

export interface MetricCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: React.ReactNode;
  description?: React.ReactNode;
  trend?: React.ReactNode;
  tone?: StatusTone;
  icon?: React.ReactNode;
}

export function MetricCard({ label, value, description, trend, tone = "session", icon, className, ...props }: MetricCardProps) {
  return (
    <Card className={cn("premium-card interactive-card min-h-[132px] space-y-4 rounded-xl p-5", className)} {...props}>
      <div className="flex items-start justify-between gap-3">
        <div className="text-xs font-bold uppercase tracking-[0.14em] text-shb-muted">{label}</div>
        {icon && <div className="grid h-9 w-9 place-items-center rounded-md border border-white/10 bg-white/5 text-shb-primary">{icon}</div>}
      </div>
      <div className="text-3xl font-black leading-none text-shb-text">{value}</div>
      <div className="flex items-center justify-between gap-3 text-sm text-shb-muted">
        {description && <span>{description}</span>}
        {trend && <StatusBadge tone={tone}>{trend}</StatusBadge>}
      </div>
    </Card>
  );
}
