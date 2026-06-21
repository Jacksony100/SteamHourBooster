import * as React from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-11 w-full rounded-xl border border-white/10 bg-slate-950/60 px-3 text-sm text-slate-50 outline-none transition placeholder:text-slate-500 focus:border-sky-300/70 focus:ring-4 focus:ring-sky-400/10",
        className
      )}
      {...props}
    />
  );
}
