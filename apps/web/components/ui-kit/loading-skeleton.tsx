import * as React from "react";

import { cn } from "@/lib/utils";

export function LoadingSkeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("skeleton-shimmer rounded-md", className)} aria-hidden="true" {...props} />;
}

export function MetricCardSkeleton() {
  return (
    <div className="premium-card rounded-xl p-5">
      <LoadingSkeleton className="h-3 w-28" />
      <LoadingSkeleton className="mt-6 h-8 w-20" />
      <LoadingSkeleton className="mt-5 h-4 w-full" />
    </div>
  );
}

export function AccountCardSkeleton() {
  return (
    <div className="premium-card rounded-xl p-5">
      <div className="flex items-center justify-between gap-4">
        <div className="space-y-3">
          <LoadingSkeleton className="h-4 w-36" />
          <LoadingSkeleton className="h-3 w-56" />
        </div>
        <LoadingSkeleton className="h-7 w-20 rounded-md" />
      </div>
      <LoadingSkeleton className="mt-5 h-10 w-full" />
    </div>
  );
}
