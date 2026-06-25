"use client";

import { useEffect, useState } from "react";

import { EmptyState } from "@/components/ui-kit/empty-state";
import { ErrorState } from "@/components/ui-kit/error-state";
import { LoadingSkeleton } from "@/components/ui-kit/loading-skeleton";
import { listSessions, sessionEvents, type SessionEvent } from "@/lib/accounts";

function errMessage(e: unknown) {
  return e instanceof Error ? e.message : "Request failed";
}

export function LogsClient() {
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSessions()
      .then(async (sessions) => {
        // Aggregate events from the most recent sessions (bounded fan-out).
        const recent = sessions.slice(0, 5);
        const batches = await Promise.all(recent.map((s) => sessionEvents(s.id).catch(() => [])));
        const merged = batches.flat().sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        setEvents(merged.slice(0, 100));
      })
      .catch((e) => setError(errMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSkeleton className="h-48 w-full" />;
  if (error) return <ErrorState title="Could not load logs" description={error} />;
  if (events.length === 0) return <EmptyState title="No activity yet" description="Session events will appear here once you start a demo session." />;

  return (
    <ol className="relative space-y-3 border-l border-shb-border pl-5">
      {events.map((event, i) => (
        <li key={`${event.id ?? "e"}-${i}`} className="relative">
          <span className="absolute -left-[1.42rem] top-1.5 h-2.5 w-2.5 rounded-full bg-sky-400 shadow-glow" />
          <div className="premium-card rounded-lg p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-semibold text-white">{event.event_type ?? "event"}</span>
              <span className="text-xs text-slate-500">{new Date(event.created_at).toLocaleString()}</span>
            </div>
            <div className="text-xs text-slate-400">{event.message}</div>
          </div>
        </li>
      ))}
    </ol>
  );
}
