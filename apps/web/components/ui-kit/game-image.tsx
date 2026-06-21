"use client";

import { useState } from "react";

type GameImageProps = {
  appId: number;
  name?: string;
  src?: string | null;
  /** Aspect ratio of the art: "header" (460x215), "capsule" (616x353), "library" (600x900). */
  variant?: "header" | "capsule" | "library";
  className?: string;
};

const RATIO: Record<NonNullable<GameImageProps["variant"]>, string> = {
  header: "460 / 215",
  capsule: "616 / 353",
  library: "600 / 900",
};

// Deterministic accent so the fallback gradient is stable per game.
function seedHue(appId: number) {
  return (appId * 47) % 360;
}

/**
 * Steam game artwork with a graceful fallback. If the Steam CDN returns 404
 * (older apps lack some sizes) we render a branded gradient tile with the game
 * initial instead of a broken image.
 */
export function GameImage({ appId, name = "", src, variant = "header", className = "" }: GameImageProps) {
  const [failed, setFailed] = useState(false);
  const hue = seedHue(appId);
  const initial = (name || "?").trim().charAt(0).toUpperCase() || "?";

  if (!src || failed) {
    return (
      <div
        className={`relative flex items-center justify-center overflow-hidden rounded-xl border border-white/10 ${className}`}
        style={{
          aspectRatio: RATIO[variant],
          background: `linear-gradient(135deg, hsl(${hue} 70% 22%), hsl(${(hue + 40) % 360} 65% 14%))`,
        }}
        aria-label={name ? `${name} (artwork unavailable)` : "Game artwork unavailable"}
      >
        <span className="font-display text-3xl font-bold text-white/80">{initial}</span>
        <span className="absolute bottom-1.5 right-2 text-[10px] font-medium text-white/40">#{appId}</span>
      </div>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element -- onError 404 fallback needs a raw <img>.
    <img
      src={src}
      alt={name || `Steam app ${appId}`}
      loading="lazy"
      onError={() => setFailed(true)}
      className={`rounded-xl border border-white/10 object-cover ${className}`}
      style={{ aspectRatio: RATIO[variant], width: "100%" }}
    />
  );
}
