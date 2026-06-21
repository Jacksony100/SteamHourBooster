"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Activity,
  Ban,
  CreditCard,
  FileClock,
  KeyRound,
  Search,
  Shield,
  Users,
  XCircle,
  type LucideIcon
} from "lucide-react";
import { toast } from "sonner";

import { Drawer } from "@/components/ui-kit/drawer";
import { Modal } from "@/components/ui-kit/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

type Overview = {
  total_users: number;
  active_subscriptions: number;
  expired_subscriptions: number;
  banned_users: number;
  active_sessions: number;
  failed_logins: number;
  payments_total_cents: number;
};

type AdminUser = {
  id: number;
  username: string;
  is_admin: boolean;
  banned: boolean;
  subscription_status: string | null;
  subscription_plan: string | null;
  subscription_expires_at: string | null;
  account_limit: number | null;
  active_session_limit: number | null;
  accounts_count: number;
  active_sessions_count: number;
  payments_total_cents: number;
  created_at: string;
  last_seen_at: string | null;
  last_ip: string | null;
};

type UserList = {
  items: AdminUser[];
  total: number;
  page: number;
  page_size: number;
};

type Plan = { code: string; name: string };
type AccountSummary = { id: number; label: string; steamid64: string | null; status: string; selected_games_count: number; created_at: string; last_login_at: string | null };
type SessionSummary = { id: number; account_id: number; status: string; selected_games: number[]; started_at: string | null; stopped_at: string | null; last_heartbeat_at: string | null; error_message: string | null };
type Payment = { id: number; user_id: number; username: string | null; plan_code: string; provider: string; status: string; amount_cents: number; currency: string; created_at: string; updated_at: string };
type AuditEvent = { id: number; actor_user_id: number | null; actor_username: string | null; action: string; target_type: string; target_id: string; metadata: Record<string, unknown>; created_at: string };
type UserDetail = { user: AdminUser; accounts: AccountSummary[]; sessions: SessionSummary[]; payments: Payment[]; audit_events: AuditEvent[] };
type CurrentUser = { id: number; username: string; is_admin: boolean; banned: boolean };
type UserFilter = "all" | "active" | "banned" | "admin" | "subscribed" | "expired";

type PendingAction = {
  title: string;
  description: string;
  danger?: boolean;
  run: () => Promise<void>;
};

const filters: Array<{ value: UserFilter; label: string }> = [
  { value: "all", label: "All" },
  { value: "active", label: "Active" },
  { value: "banned", label: "Banned" },
  { value: "admin", label: "Admins" },
  { value: "subscribed", label: "Subscribed" },
  { value: "expired", label: "Expired" }
];

function money(cents: number) {
  return `$${(cents / 100).toFixed(0)}`;
}

function date(value: string | null) {
  if (!value) return "never";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function statusClass(value: string | null | undefined) {
  if (value === "active" || value === "trialing" || value === "running") return "border-emerald-300/30 text-emerald-200";
  if (value === "banned" || value === "expired" || value === "canceled" || value === "error") return "border-rose-300/30 text-rose-200";
  if (value === "admin" || value === "paid") return "border-sky-300/30 text-sky-200";
  return "border-white/10 text-slate-300";
}

function SkeletonRows() {
  return (
    <div className="grid gap-3">
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className="h-16 rounded-xl border border-white/10 skeleton-shimmer" />
      ))}
    </div>
  );
}

export function AdminClient() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [users, setUsers] = useState<UserList>({ items: [], total: 0, page: 1, page_size: 25 });
  const [plans, setPlans] = useState<Plan[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [subscriptionChanges, setSubscriptionChanges] = useState<AuditEvent[]>([]);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [selectedUser, setSelectedUser] = useState<UserDetail | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<UserFilter>("all");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);

  const pageCount = useMemo(() => Math.max(1, Math.ceil(users.total / users.page_size)), [users.total, users.page_size]);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [overviewData, userRows, planRows, paymentRows, auditRows, subChangeRows, me] = await Promise.all([
        api<Overview>("/api/v1/admin/overview"),
        api<UserList>(`/api/v1/admin/users?query=${encodeURIComponent(query)}&filter=${filter}&page=${page}&page_size=25`),
        api<Plan[]>("/api/v1/billing/plans"),
        api<Payment[]>("/api/v1/admin/payments?page_size=8"),
        api<AuditEvent[]>("/api/v1/admin/audit?page_size=12"),
        api<AuditEvent[]>("/api/v1/admin/subscription-changes?page_size=8"),
        api<CurrentUser>("/api/v1/auth/me")
      ]);
      setOverview(overviewData);
      setUsers(userRows);
      setPlans(planRows.filter((plan) => plan.code !== "trial"));
      setPayments(paymentRows);
      setAudit(auditRows);
      setSubscriptionChanges(subChangeRows);
      setCurrentUser(me);
      setLoadError(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Admin data failed to load";
      setLoadError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, [filter, page, query]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function openUser(userId: number) {
    try {
      setSelectedUser(await api<UserDetail>(`/api/v1/admin/users/${userId}`));
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "User detail failed to load");
    }
  }

  async function afterAction(message: string) {
    toast.success(message);
    await refresh();
    if (selectedUser) await openUser(selectedUser.user.id);
  }

  function confirm(action: PendingAction) {
    setPendingAction(action);
  }

  async function runPendingAction() {
    if (!pendingAction) return;
    try {
      await pendingAction.run();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Action failed");
    } finally {
      setPendingAction(null);
    }
  }

  function patchUser(user: AdminUser, payload: Record<string, unknown>, label: string, danger = false) {
    confirm({
      title: label,
      description: `Apply "${label}" to ${user.username}? This action will be written to the audit log.`,
      danger,
      run: async () => {
        await api(`/api/v1/admin/users/${user.id}`, { method: "PATCH", csrf: true, body: JSON.stringify(payload) });
        await afterAction("User updated");
      }
    });
  }

  function updatePlan(user: AdminUser, planCode: string) {
    confirm({
      title: "Grant subscription",
      description: `Grant ${planCode} to ${user.username}? This does not touch Steam credentials.`,
      run: async () => {
        await api(`/api/v1/admin/users/${user.id}/subscription`, {
          method: "PATCH",
          csrf: true,
          body: JSON.stringify({ plan_code: planCode, status: "active", reason: "admin plan change" })
        });
        await afterAction("Subscription granted");
      }
    });
  }

  function revokeSubscription(user: AdminUser) {
    confirm({
      title: "Revoke subscription",
      description: `Cancel ${user.username}'s subscription? Existing transparent sessions should be stopped separately if needed.`,
      danger: true,
      run: async () => {
        await api(`/api/v1/admin/users/${user.id}/subscription`, {
          method: "PATCH",
          csrf: true,
          body: JSON.stringify({ status: "canceled", reason: "admin cancellation" })
        });
        await afterAction("Subscription revoked");
      }
    });
  }

  function extendSubscription(user: AdminUser) {
    confirm({
      title: "Extend subscription",
      description: `Add 30 days to ${user.username}'s subscription?`,
      run: async () => {
        await api(`/api/v1/admin/users/${user.id}/subscription`, {
          method: "PATCH",
          csrf: true,
          body: JSON.stringify({ extend_days: 30, status: "active", reason: "admin extension" })
        });
        await afterAction("Subscription extended");
      }
    });
  }

  function forceLogoutSessions(user: AdminUser) {
    confirm({
      title: "Force stop sessions",
      description: `Stop all active transparent sessions for ${user.username}?`,
      danger: true,
      run: async () => {
        await api(`/api/v1/admin/users/${user.id}/force-logout-sessions`, {
          method: "POST",
          csrf: true,
          body: JSON.stringify({ reason: "admin force stop" })
        });
        await afterAction("Active sessions stopped");
      }
    });
  }

  function toggleAdmin(user: AdminUser) {
    const selfRevoke = currentUser?.id === user.id && user.is_admin;
    patchUser(
      user,
      { is_admin: !user.is_admin, confirm_self_admin_revoke: selfRevoke, reason: user.is_admin ? "admin revoke" : "admin grant" },
      user.is_admin ? "Remove admin" : "Make admin",
      user.is_admin
    );
  }

  const metricCards: Array<{ label: string; value: string; icon: LucideIcon }> = [
    { label: "Users", value: String(overview?.total_users ?? "-"), icon: Users },
    { label: "Active subs", value: String(overview?.active_subscriptions ?? "-"), icon: Shield },
    { label: "Expired", value: String(overview?.expired_subscriptions ?? "-"), icon: XCircle },
    { label: "Banned", value: String(overview?.banned_users ?? "-"), icon: Ban },
    { label: "Sessions", value: String(overview?.active_sessions ?? "-"), icon: Activity },
    { label: "Failed logins", value: String(overview?.failed_logins ?? "-"), icon: KeyRound },
    { label: "Revenue", value: overview ? money(overview.payments_total_cents) : "-", icon: CreditCard }
  ];

  return (
    <div className="grid gap-6">
      {loadError && (
        <Card className="flex flex-wrap items-center justify-between gap-4 border-rose-400/20 bg-rose-500/10">
          <div>
            <CardTitle>Admin data unavailable</CardTitle>
            <p className="mt-2 text-sm leading-6 text-rose-100/80">{loadError}</p>
          </div>
          <Button variant="ghost" onClick={refresh}>Retry</Button>
        </Card>
      )}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-7">
        {metricCards.map(({ label, value, icon: Icon }) => (
          <Card key={label} className="space-y-3">
            <div className="flex items-center justify-between gap-3 text-slate-400">
              <span className="text-xs font-semibold uppercase">{label}</span>
              <Icon className="h-4 w-4" />
            </div>
            <div className="text-2xl font-black">{value}</div>
          </Card>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.45fr_0.55fr]">
        <Card className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <CardTitle>Users control center</CardTitle>
              <p className="text-sm text-slate-400">Search, filters, subscriptions, role changes, bans, sessions, audit-backed.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-500" />
                <Input className="pl-9" value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} placeholder="Search users" />
              </div>
              <Button onClick={refresh}>Refresh</Button>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {filters.map((item) => (
              <Button key={item.value} variant={filter === item.value ? "default" : "ghost"} onClick={() => { setFilter(item.value); setPage(1); }}>
                {item.label}
              </Button>
            ))}
          </div>

          {loading ? <SkeletonRows /> : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[980px] text-left text-sm">
                <thead className="text-xs uppercase text-slate-500">
                  <tr>
                    <th className="p-3">User</th>
                    <th className="p-3">Role</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Subscription</th>
                    <th className="p-3">Activity</th>
                    <th className="p-3">Last seen / IP</th>
                    <th className="p-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.items.length === 0 && (
                    <tr><td className="p-6 text-center text-slate-400" colSpan={7}>No users match this filter.</td></tr>
                  )}
                  {users.items.map((user) => (
                    <tr key={user.id} className="border-t border-white/10 align-top">
                      <td className="p-3">
                        <button className="text-left font-semibold text-slate-50 hover:text-sky-200" onClick={() => openUser(user.id)}>{user.username}</button>
                        <div className="text-xs text-slate-500">created {date(user.created_at)}</div>
                      </td>
                      <td className="p-3"><Badge className={statusClass(user.is_admin ? "admin" : "user")}>{user.is_admin ? "admin" : "user"}</Badge></td>
                      <td className="p-3"><Badge className={statusClass(user.banned ? "banned" : "active")}>{user.banned ? "banned" : "active"}</Badge></td>
                      <td className="p-3">
                        <div>{user.subscription_status || "inactive"} / {user.subscription_plan || "free"}</div>
                        <div className="text-xs text-slate-500">{user.subscription_expires_at ? date(user.subscription_expires_at) : "no expiry"}</div>
                      </td>
                      <td className="p-3 text-xs text-slate-400">
                        <div>{user.accounts_count} accounts</div>
                        <div>{user.active_sessions_count} active sessions</div>
                        <div>{money(user.payments_total_cents)} paid</div>
                      </td>
                      <td className="p-3 text-xs text-slate-400">
                        <div>{date(user.last_seen_at)}</div>
                        <div>{user.last_ip || "no IP"}</div>
                      </td>
                      <td className="p-3">
                        <div className="flex flex-wrap gap-2">
                          <Button variant="ghost" onClick={() => openUser(user.id)}>Details</Button>
                          <Button variant="ghost" onClick={() => patchUser(user, { banned: !user.banned, reason: user.banned ? "admin unban" : "admin ban" }, user.banned ? "Unban user" : "Ban user", !user.banned)}>
                            {user.banned ? "Unban" : "Ban"}
                          </Button>
                          <Button variant="ghost" onClick={() => toggleAdmin(user)}>{user.is_admin ? "Remove admin" : "Make admin"}</Button>
                          <Button variant="danger" onClick={() => forceLogoutSessions(user)}>Stop sessions</Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-4 text-sm text-slate-400">
            <div>Page {users.page} of {pageCount} / {users.total} users</div>
            <div className="flex gap-2">
              <Button variant="ghost" disabled={page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))}>Previous</Button>
              <Button variant="ghost" disabled={page >= pageCount} onClick={() => setPage((value) => value + 1)}>Next</Button>
            </div>
          </div>
        </Card>

        <div className="grid gap-6">
          <ActivityPanel title="Payments" icon={<CreditCard className="h-4 w-4" />} empty="No payments yet.">
            {payments.map((payment) => (
              <div key={payment.id} className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-semibold">{payment.username || `User ${payment.user_id}`}</div>
                  <Badge className={statusClass(payment.status)}>{payment.status}</Badge>
                </div>
                <div className="mt-1 text-xs text-slate-400">{payment.plan_code} / {money(payment.amount_cents)} {payment.currency}</div>
              </div>
            ))}
          </ActivityPanel>

          <ActivityPanel title="Subscription changes" icon={<FileClock className="h-4 w-4" />} empty="No subscription events.">
            {subscriptionChanges.map((event) => <AuditItem key={event.id} event={event} />)}
          </ActivityPanel>

          <ActivityPanel title="Audit log" icon={<Shield className="h-4 w-4" />} empty="Audit log is empty.">
            {audit.map((event) => <AuditItem key={event.id} event={event} />)}
          </ActivityPanel>
        </div>
      </section>

      <Drawer
        open={Boolean(selectedUser)}
        onOpenChange={(open) => !open && setSelectedUser(null)}
        title={selectedUser?.user.username || "User detail"}
        description="User profile, subscription, sessions, payments, and audit trail."
        footer={selectedUser && (
          <>
            <Button variant="ghost" onClick={() => extendSubscription(selectedUser.user)}>+30 days</Button>
            <Button variant="danger" onClick={() => revokeSubscription(selectedUser.user)}>Revoke subscription</Button>
          </>
        )}
      >
        {selectedUser && (
          <div className="grid gap-5">
            <div className="grid gap-3 text-sm">
              <Info label="User ID" value={`#${selectedUser.user.id}`} />
              <Info label="Last seen" value={date(selectedUser.user.last_seen_at)} />
              <Info label="Last IP" value={selectedUser.user.last_ip || "no IP"} />
              <Info label="Subscription" value={`${selectedUser.user.subscription_status || "inactive"} / ${selectedUser.user.subscription_plan || "free"}`} />
              <Info label="Limits" value={`${selectedUser.user.account_limit ?? 0} accounts / ${selectedUser.user.active_session_limit ?? 0} sessions`} />
            </div>

            <div className="grid gap-2">
              <div className="text-sm font-bold">Billing controls</div>
              <div className="flex flex-wrap gap-2">
                {plans.map((plan) => (
                  <Button key={plan.code} variant="ghost" onClick={() => updatePlan(selectedUser.user, plan.code)}>{plan.name}</Button>
                ))}
              </div>
            </div>

            <DrawerSection title="Accounts" empty="No Steam accounts.">
              {selectedUser.accounts.map((account) => (
                <div key={account.id} className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-semibold">{account.label}</div>
                    <Badge className={statusClass(account.status)}>{account.status}</Badge>
                  </div>
                  <div className="mt-1 text-xs text-slate-400">SteamID64: {account.steamid64 || "not connected"} / games {account.selected_games_count}</div>
                </div>
              ))}
            </DrawerSection>

            <DrawerSection title="Sessions" empty="No sessions.">
              {selectedUser.sessions.map((session) => (
                <div key={session.id} className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-semibold">Session #{session.id}</div>
                    <Badge className={statusClass(session.status)}>{session.status}</Badge>
                  </div>
                  <div className="mt-1 text-xs text-slate-400">Account {session.account_id} / games {session.selected_games.join(", ") || "-"}</div>
                  {session.error_message && <div className="mt-2 rounded-lg border border-rose-300/20 bg-rose-300/10 p-2 text-xs text-rose-100">{session.error_message}</div>}
                </div>
              ))}
            </DrawerSection>

            <DrawerSection title="Payments" empty="No payments.">
              {selectedUser.payments.map((payment) => (
                <div key={payment.id} className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-semibold">{payment.plan_code}</div>
                    <Badge className={statusClass(payment.status)}>{payment.status}</Badge>
                  </div>
                  <div className="mt-1 text-xs text-slate-400">{money(payment.amount_cents)} {payment.currency} / {date(payment.created_at)}</div>
                </div>
              ))}
            </DrawerSection>

            <DrawerSection title="Audit trail" empty="No audit events.">
              {selectedUser.audit_events.map((event) => <AuditItem key={event.id} event={event} />)}
            </DrawerSection>
          </div>
        )}
      </Drawer>

      <Modal
        open={Boolean(pendingAction)}
        onOpenChange={(open) => !open && setPendingAction(null)}
        title={pendingAction?.title || "Confirm action"}
        description={pendingAction?.description}
        footer={
          <>
            <Button variant="ghost" onClick={() => setPendingAction(null)}>Cancel</Button>
            <Button variant={pendingAction?.danger ? "danger" : "default"} onClick={runPendingAction}>Confirm</Button>
          </>
        }
      >
        <div className="rounded-xl border border-amber-300/20 bg-amber-300/10 p-4 text-sm leading-6 text-amber-100">
          This admin action is security-sensitive and will be recorded in the audit log.
        </div>
      </Modal>
    </div>
  );
}

function ActivityPanel({ title, icon, empty, children }: { title: string; icon: ReactNode; empty: string; children: ReactNode }) {
  const hasItems = Array.isArray(children) ? children.length > 0 : Boolean(children);
  return (
    <Card className="space-y-3">
      <div className="flex items-center gap-2">
        {icon}
        <CardTitle>{title}</CardTitle>
      </div>
      <div className="grid gap-2">
        {hasItems ? children : <div className="rounded-xl border border-dashed border-white/15 bg-white/[0.03] p-4 text-sm text-slate-400">{empty}</div>}
      </div>
    </Card>
  );
}

function DrawerSection({ title, empty, children }: { title: string; empty: string; children: ReactNode }) {
  const hasItems = Array.isArray(children) ? children.length > 0 : Boolean(children);
  return (
    <div className="grid gap-2">
      <div className="text-sm font-bold">{title}</div>
      {hasItems ? children : <div className="rounded-xl border border-dashed border-white/15 bg-white/[0.03] p-4 text-sm text-slate-400">{empty}</div>}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 p-3">
      <span className="text-slate-400">{label}</span>
      <span className="font-semibold text-slate-100">{value}</span>
    </div>
  );
}

function AuditItem({ event }: { event: AuditEvent }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-sm">
      <div className="flex items-center justify-between gap-3">
        <div className="font-semibold">{event.action}</div>
        <div className="text-xs text-slate-500">{date(event.created_at)}</div>
      </div>
      <div className="mt-1 text-xs text-slate-400">
        actor {event.actor_username || event.actor_user_id || "system"} / {event.target_type} #{event.target_id}
      </div>
      {Object.keys(event.metadata || {}).length > 0 && (
        <pre className="mt-2 max-h-24 overflow-auto rounded-lg bg-black/20 p-2 text-[11px] text-slate-400">
          {JSON.stringify(event.metadata, null, 2)}
        </pre>
      )}
    </div>
  );
}
