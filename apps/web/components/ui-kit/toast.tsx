"use client";

import { Toaster, toast } from "sonner";

export function PremiumToaster() {
  return (
    <Toaster
      theme="dark"
      position="bottom-right"
      richColors={false}
      toastOptions={{
        classNames: {
          toast: "glass border-shb-border bg-shb-bg-soft text-shb-text",
          title: "text-shb-text",
          description: "text-shb-muted",
          actionButton: "bg-shb-primary text-white",
          cancelButton: "bg-white/10 text-shb-text"
        }
      }}
    />
  );
}

export { toast };
