"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Clock3, ShieldCheck, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { PricingCard } from "@/components/ui-kit/pricing-card";
import { api } from "@/lib/api";

type Plan = {
  code: string;
  name: string;
  price_cents: number;
  duration_days: number | null;
  account_limit: number;
  active_session_limit: number;
  support_level: string;
  features: string[];
  active: boolean;
};

type Subscription = {
  plan_code: string;
  status: string;
  active: boolean;
  starts_at: string | null;
  expires_at: string | null;
  ends_at: string | null;
  manual_override: boolean;
  account_limit: number;
  active_session_limit: number;
  support_level: string;
  features: string[];
};

type Payment = {
  id: number;
  plan_code: string;
  provider: string;
  status: string;
  amount_cents: number;
  currency: string;
  checkout_url: string | null;
  idempotency_key: string;
  provider_payment_id: string | null;
  created_at: string;
  updated_at: string;
};
type SystemMode = {
  environment: string;
  steam_test_mode: boolean;
  real_steam_enabled: boolean;
  billing_provider: string;
  demo_mode: boolean;
  checkout_disabled_reason: string | null;
};

function money(cents: number) {
  if (cents === 0) return "$0";
  return `$${(cents / 100).toFixed(0)}`;
}

function duration(days: number | null) {
  if (!days) return "lifetime";
  if (days === 14) return "14 days";
  if (days === 30) return "per month";
  return `${days} days`;
}

function formatDate(value: string | null) {
  if (!value) return "No expiry";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value));
}

export function BillingClient() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [systemMode, setSystemMode] = useState<SystemMode | null>(null);
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      const [planRows, currentSub, paymentRows, mode] = await Promise.all([
        api<Plan[]>("/api/v1/billing/plans"),
        api<Subscription>("/api/v1/billing/subscription"),
        api<Payment[]>("/api/v1/billing/payments"),
        api<SystemMode>("/api/v1/system/mode")
      ]);
      setPlans(planRows);
      setSubscription(currentSub);
      setPayments(paymentRows);
      setSystemMode(mode);
      setLoadError(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Billing failed to load";
      setLoadError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  const paidPlans = useMemo(() => plans.filter((plan) => plan.code !== "trial"), [plans]);

  async function checkout(plan: Plan) {
    if (systemMode?.checkout_disabled_reason) {
      toast.error(systemMode.checkout_disabled_reason);
      return;
    }
    setLoadingPlan(plan.code);
    try {
      const payment = await api<Payment & { payment_id: number }>("/api/v1/billing/checkout", {
        method: "POST",
        csrf: true,
        body: JSON.stringify({ plan_code: plan.code })
      });
      toast.success("Checkout created. Waiting for verified payment event.");
      if (payment.checkout_url) {
        window.location.href = payment.checkout_url;
      } else {
        await refresh();
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Checkout failed");
    } finally {
      setLoadingPlan(null);
    }
  }

  return (
    <div className="grid gap-6">
      {loading && (
        <div className="grid gap-4 md:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="h-32 rounded-2xl border border-white/10 skeleton-shimmer" />
          ))}
        </div>
      )}
      {loadError && (
        <Card className="flex flex-wrap items-center justify-between gap-4 border-rose-400/20 bg-rose-500/10">
          <div>
            <CardTitle>Billing unavailable</CardTitle>
            <p className="mt-2 text-sm leading-6 text-rose-100/80">{loadError}</p>
          </div>
          <Button variant="ghost" onClick={refresh}>Retry</Button>
        </Card>
      )}
      <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="space-y-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-sky-200">Current plan</div>
              <CardTitle className="mt-1 text-2xl">{subscription?.plan_code || "loading"}</CardTitle>
            </div>
            <Badge className={subscription?.active ? "border-emerald-300/30 text-emerald-200" : "border-amber-300/30 text-amber-200"}>
              {subscription?.status || "loading"}
            </Badge>
          </div>
          <div className="grid gap-3 text-sm text-slate-300 md:grid-cols-3">
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <div className="text-slate-500">Accounts</div>
              <div className="mt-2 text-2xl font-black">{subscription?.account_limit ?? "-"}</div>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <div className="text-slate-500">Active sessions</div>
              <div className="mt-2 text-2xl font-black">{subscription?.active_session_limit ?? "-"}</div>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <div className="text-slate-500">Renews/expires</div>
              <div className="mt-2 text-sm font-bold text-slate-100">{formatDate(subscription?.expires_at || null)}</div>
            </div>
          </div>
          <div className="rounded-xl border border-sky-300/20 bg-sky-300/10 p-4 text-sm leading-6 text-sky-100">
            <ShieldCheck className="mr-2 inline h-4 w-4" />
            Subscriptions are activated only by a verified webhook or an audited admin action.
          </div>
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center gap-2">
            <Clock3 className="h-5 w-5 text-sky-300" />
            <CardTitle>Recent payments</CardTitle>
          </div>
          <div className="grid gap-3">
            {payments.length === 0 ? (
              <div className="rounded-xl border border-dashed border-white/15 bg-white/[0.03] p-6 text-sm text-slate-400">
                No payments yet. Start a checkout below and confirm it through a verified provider webhook.
              </div>
            ) : payments.map((payment) => (
              <div key={payment.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 p-4">
                <div>
                  <div className="font-semibold">{payment.plan_code} / {payment.provider}</div>
                  <div className="text-xs text-slate-500">{payment.idempotency_key}</div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="font-bold">{money(payment.amount_cents)} {payment.currency}</div>
                  <Badge>{payment.status}</Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </section>

      <section>
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-emerald-200">Pricing</div>
            <h2 className="text-3xl font-black">Choose the right capacity</h2>
          </div>
          <Badge className="border-emerald-300/30 text-emerald-200">
            <Sparkles className="h-3.5 w-3.5" />
            Server-managed checkout
          </Badge>
        </div>
        <div className="grid gap-4 lg:grid-cols-4">
          {paidPlans.length === 0 && !loading ? (
            <Card className="lg:col-span-4">
              <CardTitle>No paid plans available</CardTitle>
              <p className="mt-2 text-sm leading-6 text-slate-400">Plans are seeded by the API. Retry after migrations and seed have completed.</p>
            </Card>
          ) : paidPlans.map((plan) => (
            <PricingCard
              key={plan.code}
              name={plan.name}
              price={money(plan.price_cents)}
              duration={duration(plan.duration_days)}
              features={[
                `${plan.account_limit} accounts`,
                `${plan.active_session_limit} active sessions`,
                `${plan.support_level} support`,
                ...plan.features
              ]}
              recommended={plan.code === "pro"}
              actionLabel={
                loadingPlan === plan.code
                  ? "Creating..."
                  : plan.code === subscription?.plan_code
                    ? "Current plan"
                    : plan.code === "lifetime"
                      ? "Manual grant"
                      : systemMode?.checkout_disabled_reason
                        ? "Disabled in demo"
                        : "Checkout"
              }
              onSelect={plan.code === subscription?.plan_code || plan.code === "lifetime" || systemMode?.checkout_disabled_reason ? undefined : () => checkout(plan)}
            />
          ))}
        </div>
      </section>

      <Card className="flex flex-wrap items-center justify-between gap-4 border-amber-300/20 bg-amber-300/10">
        <div>
          <CardTitle>Payment safety</CardTitle>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-amber-100/90">
            Redirects never grant access by themselves. The API records a pending payment first, then applies the plan only after an idempotent verified payment event.
          </p>
        </div>
        <Button variant="ghost" onClick={refresh}>
          Refresh billing
          <ArrowRight className="h-4 w-4" />
        </Button>
      </Card>
    </div>
  );
}
