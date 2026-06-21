import * as React from "react";
import { Clock3, Square } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui-kit/status-badge";
import { cn } from "@/lib/utils";
import type { StatusTone } from "@/lib/design-tokens";

export interface SessionCardProps extends React.HTMLAttributes<HTMLDivElement> {
  accountLabel: string;
  status?: StatusTone;
  uptime?: string;
  games?: string[];
  workerState?: string;
  logs?: string[];
  onStop?: () => void;
}

export function SessionCard({ accountLabel, status = "session", uptime, games = [], workerState, logs = [], onStop, className, ...props }: SessionCardProps) {
  return (
    <Card className={cn("premium-card rounded-xl p-5", className)} {...props}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-black text-shb-text">{accountLabel}</h3>
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-shb-muted">
            {uptime && (
              <span className="inline-flex items-center gap-1">
                <Clock3 className="h-3.5 w-3.5" />
                {uptime}
              </span>
            )}
            {workerState && <span>Worker: {workerState}</span>}
          </div>
        </div>
        <StatusBadge tone={status}>{status}</StatusBadge>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {games.length ? games.map((game) => <span key={game} className="rounded-md border border-white/10 bg-white/5 px-2.5 py-1 text-xs text-slate-200">{game}</span>) : <span className="text-sm text-shb-muted">No games selected</span>}
      </div>

      {logs.length > 0 && (
        <div className="mt-4 rounded-md border border-white/10 bg-black/20 p-3 text-xs leading-5 text-shb-muted">
          {logs.slice(0, 3).map((log) => <div key={log}>{log}</div>)}
        </div>
      )}

      {onStop && (
        <Button className="mt-5" variant="danger" onClick={onStop}>
          <Square className="h-4 w-4" />
          Stop session
        </Button>
      )}
    </Card>
  );
}
