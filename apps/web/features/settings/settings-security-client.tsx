"use client";

import { useEffect, useState } from "react";
import { Download, KeyRound, MailCheck, RefreshCw, ShieldCheck, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

type User = {
  id: number;
  username: string;
  email: string | null;
  email_verified: boolean;
  is_admin: boolean;
  banned: boolean;
};

type UserSession = {
  id: number;
  created_at: string;
  last_seen_at: string | null;
  current: boolean;
  user_agent: string | null;
};

function formatDate(value: string | null) {
  if (!value) return "never";
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function downloadJson(filename: string, payload: unknown) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function SettingsSecurityClient() {
  const [user, setUser] = useState<User | null>(null);
  const [sessions, setSessions] = useState<UserSession[]>([]);
  const [email, setEmail] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState("");
  const [loading, setLoading] = useState(false);

  async function refresh() {
    const [me, sessionRows] = await Promise.all([api<User>("/api/v1/auth/me"), api<UserSession[]>("/api/v1/auth/sessions")]);
    setUser(me);
    setEmail(me.email || "");
    setSessions(sessionRows);
  }

  useEffect(() => {
    refresh().catch((error) => toast.error(error instanceof Error ? error.message : "Failed to load settings"));
  }, []);

  async function requestVerification() {
    setLoading(true);
    try {
      await api("/api/v1/auth/email-verification/request", {
        method: "POST",
        csrf: true,
        body: JSON.stringify({ email: email || null })
      });
      toast.success("Verification request created.");
      await refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Verification failed");
    } finally {
      setLoading(false);
    }
  }

  async function revokeSession(sessionId: number) {
    try {
      await api(`/api/v1/auth/sessions/${sessionId}`, { method: "DELETE", csrf: true });
      toast.success("Session revoked.");
      await refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not revoke session");
    }
  }

  async function exportData() {
    try {
      const payload = await api<unknown>("/api/v1/auth/export");
      downloadJson(`deckpilot-export-${new Date().toISOString().slice(0, 10)}.json`, payload);
      toast.success("Export generated.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Export failed");
    }
  }

  async function deleteAccount() {
    if (!user || deleteConfirm !== user.username) return;
    setLoading(true);
    try {
      await api("/api/v1/auth/account", { method: "DELETE", csrf: true });
      toast.success("Account deleted.");
      window.location.href = "/";
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Account deletion failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-6">
      <Card className="space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-sky-200">
              <ShieldCheck className="h-4 w-4" />
              Account security
            </div>
            <CardTitle className="mt-2">Profile and verification</CardTitle>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Keep your workspace recoverable and review active browser sessions from this device list.
            </p>
          </div>
          <Badge className={user?.email_verified ? "border-emerald-300/30 text-emerald-200" : "border-amber-300/30 text-amber-200"}>
            {user?.email_verified ? "Email verified" : "Email not verified"}
          </Badge>
        </div>

        <div className="grid gap-3 md:grid-cols-[1fr_auto]">
          <label className="grid gap-2 text-sm text-slate-300">
            Email
            <Input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" type="email" />
          </label>
          <Button className="self-end" disabled={loading} onClick={requestVerification}>
            <MailCheck className="h-4 w-4" />
            Verify email
          </Button>
        </div>
      </Card>

      <Card className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-emerald-200">
              <KeyRound className="h-4 w-4" />
              Active sessions
            </div>
            <CardTitle className="mt-2">Signed-in devices</CardTitle>
          </div>
          <Button variant="ghost" onClick={refresh}>
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        <div className="grid gap-3">
          {sessions.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/15 bg-white/[0.03] p-6 text-sm text-slate-400">
              No active web sessions were found.
            </div>
          ) : (
            sessions.map((session) => (
              <div key={session.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 p-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 font-semibold">
                    Session #{session.id}
                    {session.current ? <Badge className="border-sky-300/30 text-sky-200">Current</Badge> : null}
                  </div>
                  <div className="mt-1 max-w-2xl truncate text-xs text-slate-500">{session.user_agent || "Unknown browser"}</div>
                  <div className="mt-1 text-xs text-slate-500">Last seen {formatDate(session.last_seen_at)}</div>
                </div>
                <Button variant="ghost" onClick={() => revokeSession(session.id)}>
                  Revoke
                </Button>
              </div>
            ))
          )}
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-sky-200">
            <Download className="h-4 w-4" />
            Data export
          </div>
          <CardTitle>Download account data</CardTitle>
          <p className="text-sm leading-6 text-slate-400">
            Export profile, subscription, account labels, session history, and payment metadata. Credentials and secret token hashes are never included.
          </p>
          <Button variant="ghost" onClick={exportData}>
            Export JSON
          </Button>
        </Card>

        <Card className="space-y-4 border-rose-400/20 bg-rose-500/10">
          <div className="flex items-center gap-2 text-sm font-semibold text-rose-200">
            <Trash2 className="h-4 w-4" />
            Danger zone
          </div>
          <CardTitle>Delete workspace account</CardTitle>
          <p className="text-sm leading-6 text-rose-100/80">
            This removes your user, subscription, accounts, sessions, and related records from this workspace.
          </p>
          <Input value={deleteConfirm} onChange={(event) => setDeleteConfirm(event.target.value)} placeholder={`Type ${user?.username || "username"} to confirm`} />
          <Button variant="danger" disabled={!user || deleteConfirm !== user.username || loading} onClick={deleteAccount}>
            Delete account
          </Button>
        </Card>
      </div>
    </div>
  );
}
