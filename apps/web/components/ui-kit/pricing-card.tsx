import * as React from "react";
import { Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface PricingCardProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string;
  price: string;
  duration: string;
  features: string[];
  recommended?: boolean;
  actionLabel?: string;
  onSelect?: () => void;
}

export function PricingCard({ name, price, duration, features, recommended = false, actionLabel = "Choose plan", onSelect, className, ...props }: PricingCardProps) {
  return (
    <div className={cn("premium-card relative rounded-xl p-5", recommended && "border-shb-primary/45 shadow-glow-primary", className)} {...props}>
      {recommended && <div className="absolute right-4 top-4 rounded-md border border-shb-primary/30 bg-shb-primary/10 px-2.5 py-1 text-xs font-bold text-sky-100">Recommended</div>}
      <h3 className="text-xl font-black">{name}</h3>
      <div className="mt-5 flex items-end gap-2">
        <div className="text-4xl font-black">{price}</div>
        <div className="pb-1 text-sm text-shb-muted">{duration}</div>
      </div>
      <ul className="mt-5 grid gap-3 text-sm text-slate-200">
        {features.map((feature, index) => (
          <li key={`${feature}-${index}`} className="flex gap-2">
            <Check className="mt-0.5 h-4 w-4 text-shb-success" />
            <span>{feature}</span>
          </li>
        ))}
      </ul>
      {onSelect && <Button className="mt-6 w-full" variant={recommended ? "default" : "ghost"} onClick={onSelect}>{actionLabel}</Button>}
    </div>
  );
}
