import * as React from "react";
import { PlusCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export function EmptyState({ title, description, actionLabel, onAction, icon, className, ...props }: EmptyStateProps) {
  return (
    <div className={cn("rounded-xl border border-dashed border-shb-border bg-white/[0.035] p-6 text-center", className)} {...props}>
      <div className="mx-auto grid h-12 w-12 place-items-center rounded-lg border border-white/10 bg-white/5 text-shb-primary">
        {icon ?? <PlusCircle className="h-5 w-5" />}
      </div>
      <h3 className="mt-4 text-base font-bold text-shb-text">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-shb-muted">{description}</p>
      {actionLabel && onAction && (
        <Button className="mt-5" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
