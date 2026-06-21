import * as React from "react";
import { Gamepad2, KeyRound, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui-kit/status-badge";
import { cn } from "@/lib/utils";
import type { StatusTone } from "@/lib/design-tokens";

export interface AccountCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  steamId?: string | null;
  status?: StatusTone;
  selectedGamesCount?: number;
  activeSessionLabel?: string;
  lastActivity?: string;
  onOpen?: () => void;
  onGames?: () => void;
  onStartSession?: () => void;
  onDelete?: () => void;
}

export function AccountCard({
  label,
  steamId,
  status = "offline",
  selectedGamesCount = 0,
  activeSessionLabel,
  lastActivity,
  onOpen,
  onGames,
  onStartSession,
  onDelete,
  className,
  ...props
}: AccountCardProps) {
  return (
    <Card className={cn("premium-card interactive-card rounded-xl p-5", className)} {...props}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="truncate text-lg font-black text-shb-text">{label}</h3>
          <p className="mt-1 text-xs text-shb-muted">SteamID64: {steamId || "not connected"}</p>
        </div>
        <StatusBadge tone={status}>{status}</StatusBadge>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-md border border-white/10 bg-white/5 p-3">
          <div className="text-xs uppercase tracking-[0.14em] text-shb-muted">Games</div>
          <div className="mt-1 text-xl font-black">{selectedGamesCount}</div>
        </div>
        <div className="rounded-md border border-white/10 bg-white/5 p-3">
          <div className="text-xs uppercase tracking-[0.14em] text-shb-muted">Session</div>
          <div className="mt-1 truncate text-sm font-bold">{activeSessionLabel || "Idle"}</div>
        </div>
      </div>

      {lastActivity && <p className="mt-4 text-xs text-shb-muted">Last activity: {lastActivity}</p>}

      <div className="mt-5 flex flex-wrap gap-2">
        {onOpen && <Button onClick={onOpen}>Details</Button>}
        {onGames && (
          <Button variant="ghost" onClick={onGames}>
            <Gamepad2 className="h-4 w-4" />
            Games
          </Button>
        )}
        {onStartSession && (
          <Button variant="success" onClick={onStartSession}>
            <KeyRound className="h-4 w-4" />
            Start
          </Button>
        )}
        {onDelete && (
          <Button variant="danger" onClick={onDelete} aria-label={`Delete ${label}`}>
            <Trash2 className="h-4 w-4" />
          </Button>
        )}
      </div>
    </Card>
  );
}
