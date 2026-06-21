"use client";

import { useEffect, useState } from "react";
import { Info } from "lucide-react";

import { api } from "@/lib/api";

type SystemMode = {
  environment: string;
  steam_test_mode: boolean;
  steam_integration_mode: "demo" | "official";
  real_steam_enabled: boolean;
  official_steam_configured: boolean;
  password_login_allowed: boolean;
  billing_provider: string;
  demo_mode: boolean;
  checkout_disabled_reason: string | null;
};

export function SystemModeBanner() {
  const [mode, setMode] = useState<SystemMode | null>(null);

  useEffect(() => {
    api<SystemMode>("/api/v1/system/mode")
      .then(setMode)
      .catch(() => undefined);
  }, []);

  if (!mode) return null;
  if (!mode.demo_mode && mode.official_steam_configured) return null;
  const isOfficialUnavailable = mode.steam_integration_mode === "official" && !mode.official_steam_configured;

  return (
    <div className="mb-5 flex flex-wrap items-start gap-3 rounded-2xl border border-sky-300/20 bg-sky-300/10 px-4 py-3 text-sm text-sky-50 shadow-glow backdrop-blur-xl">
      <Info className="mt-0.5 h-4 w-4 shrink-0 text-sky-200" />
      <div>
        <div className="font-bold">Demo Mode</div>
        <p className="mt-1 leading-6 text-sky-100/85">
          {isOfficialUnavailable
            ? "Official Steam linking is selected, but it is not configured in this build. Account and session actions stay unavailable until official integration is configured."
            : "Real Steam sessions are disabled in this build. Preview accounts and sessions use the safe demo adapter."}
          {mode.checkout_disabled_reason ? ` ${mode.checkout_disabled_reason}` : ""}
        </p>
      </div>
    </div>
  );
}
