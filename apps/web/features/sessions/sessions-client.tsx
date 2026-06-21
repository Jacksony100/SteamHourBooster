"use client";

import { useEffect, useState } from "react";
import { Square } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui-kit/empty-state";
import { ErrorState } from "@/components/ui-kit/error-state";
import { LoadingSkeleton } from "@/components/ui-kit/loading-skeleton";
import { StatusBadge } from "@/components/ui-kit/status-badge";
import { listSessions, stopSession, type ActivitySession } from "@/lib/accounts";
import type { StatusTone } from "@/lib/design-tokens";

function errMessage(e: unknown) {
  return e instanceof Error ? e.message : "Request failed";
}

const ACTIVE = new Set(["starting", "running", "stopping"]);
const TONE: Record<string, StatusTone> = { running: "session", starting: "session", stopping: "warning", stopped: "offline", error: "error", failed: "error" };

export function SessionsClient() {
  const [sessions, setSessions] = useState<ActivitySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    listSessions()
      .then(setSessions)
      .catch((e) => setError(errMessage(e)))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function stop(id: number) {
    try {
      await stopSession(id);
      toast.success("Session stopped");
      load();
    } catch (e) {
      toast.error(errMessage(e));
    }
  }

  if (loading) return <LoadingSkeleton className="h-40 w-full" />;
  if (error) return <ErrorState title="Could not load sessions" description={error} actionLabel="Retry" onAction={load} />;
  if (sessions.length === 0) {
    return (
      <EmptyState
        title="No sessions yet"
        description="Start a transparent demo session from the dashboard once an account is online with games selected."
        actionLabel="Go to dashboard"
        onAction={() => {
          window.location.href = "/dashboard";
        }}
      />
    );
  }

  return (
    <div className="space-y-3">
      {sessions.map((session) => (
        <div key={session.id} className="premium-card flex flex-wrap items-center gap-4 rounded-xl p-4">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-white">Session #{session.id}</span>
              <StatusBadge tone={TONE[session.status] ?? "offline"}>{session.status}</StatusBadge>
            </div>
            <div className="truncate text-xs text-slate-400">
              Account {session.account_id} · {session.selected_games.length} games
              {session.started_at && ` · started ${new Date(session.started_at).toLocaleString()}`}
              {session.error_message && ` · ${session.error_message}`}
            </div>
          </div>
          {ACTIVE.has(session.status) && (
            <Button variant="danger" onClick={() => stop(session.id)}>
              <Square className="h-4 w-4" />
              Stop
            </Button>
          )}
        </div>
      ))}
    </div>
  );
}
