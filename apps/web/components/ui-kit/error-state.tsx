import * as React from "react";
import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function ErrorState({ title, description, actionLabel, onAction, className, ...props }: ErrorStateProps) {
  return (
    <div className={cn("rounded-xl border border-shb-danger/30 bg-shb-danger/10 p-5 text-rose-50 shadow-glow-danger", className)} role="alert" {...props}>
      <div className="flex items-start gap-3">
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-md border border-shb-danger/30 bg-shb-danger/10">
          <AlertTriangle className="h-5 w-5" />
        </div>
        <div>
          <h3 className="font-bold">{title}</h3>
          <p className="mt-1 text-sm leading-6 text-rose-100/80">{description}</p>
          {actionLabel && onAction && (
            <Button className="mt-4" variant="danger" onClick={onAction}>
              {actionLabel}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
