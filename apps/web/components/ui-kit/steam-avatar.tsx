"use client";

import { useState } from "react";

type SteamAvatarProps = {
  src?: string | null;
  personaName?: string | null;
  size?: number;
  /** persona_state from Steam: 0 offline, 1+ online. */
  online?: boolean;
  className?: string;
};

/**
 * Steam profile avatar with an initials fallback when the profile is private,
 * unavailable, or the image fails to load. Optionally shows a presence dot.
 */
export function SteamAvatar({ src, personaName, size = 40, online, className = "" }: SteamAvatarProps) {
  const [failed, setFailed] = useState(false);
  const initial = (personaName || "?").trim().charAt(0).toUpperCase() || "?";

  return (
    <span className={`relative inline-flex shrink-0 ${className}`} style={{ width: size, height: size }}>
      {src && !failed ? (
        // eslint-disable-next-line @next/next/no-img-element -- onError fallback needs a raw <img>.
        <img
          src={src}
          alt={personaName || "Steam avatar"}
          width={size}
          height={size}
          loading="lazy"
          onError={() => setFailed(true)}
          className="rounded-lg border border-white/10 object-cover"
          style={{ width: size, height: size }}
        />
      ) : (
        <span
          className="flex items-center justify-center rounded-lg border border-white/10 font-display font-semibold text-white/80"
          style={{
            width: size,
            height: size,
            background: "linear-gradient(135deg, #2E8BFF, #8B5CF6)",
            fontSize: size * 0.42,
          }}
          aria-label={personaName || "Steam avatar"}
        >
          {initial}
        </span>
      )}
      {typeof online === "boolean" && (
        <span
          className="absolute -bottom-0.5 -right-0.5 rounded-full border-2"
          style={{
            width: size * 0.3,
            height: size * 0.3,
            borderColor: "var(--shb-bg)",
            background: online ? "var(--shb-success)" : "var(--shb-muted)",
          }}
        />
      )}
    </span>
  );
}
