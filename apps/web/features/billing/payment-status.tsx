"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AlertTriangle, CheckCircle2, Clock3, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";

type PaymentStatusProps = {
  status: "pending" | "success" | "failed";
};

const copy = {
  pending: {
    icon: Clock3,
    title: "Payment pending",
    body: "A checkout was created, but access is not granted until the API receives a verified provider webhook.",
    tone: "border-amber-300/25 bg-amber-300/10 text-amber-100"
  },
  success: {
    icon: CheckCircle2,
    title: "Payment verified",
    body: "Your payment event was verified and the subscription can now be reflected in the dashboard.",
    tone: "border-emerald-300/25 bg-emerald-300/10 text-emerald-100"
  },
  failed: {
    icon: XCircle,
    title: "Payment failed",
    body: "The provider reported a failed, expired, or canceled payment. No subscription was granted.",
    tone: "border-rose-300/25 bg-rose-300/10 text-rose-100"
  }
};

export function PaymentStatus({ status }: PaymentStatusProps) {
  const searchParams = useSearchParams();
  const payment = searchParams.get("payment") || searchParams.get("plan") || "not provided";
  const item = copy[status];
  const Icon = item.icon || AlertTriangle;

  return (
    <div className="mx-auto grid max-w-3xl gap-6">
      <Card className={`space-y-5 ${item.tone}`}>
        <div className="flex items-center gap-3">
          <div className="grid h-12 w-12 place-items-center rounded-xl border border-current/20 bg-white/10">
            <Icon className="h-6 w-6" />
          </div>
          <div>
            <div className="text-sm font-semibold opacity-80">Billing status</div>
            <CardTitle className="text-2xl">{item.title}</CardTitle>
          </div>
        </div>
        <p className="text-sm leading-7 opacity-90">{item.body}</p>
        <div className="rounded-xl border border-current/15 bg-black/15 p-4 text-sm">
          <div className="opacity-70">Payment reference</div>
          <div className="mt-1 font-mono text-xs">{payment}</div>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link href="/billing">Back to billing</Link>
          </Button>
          <Button asChild variant="ghost">
            <Link href="/dashboard">Dashboard</Link>
          </Button>
        </div>
      </Card>
    </div>
  );
}
