export const designTokens = {
  color: {
    background: "#05070D",
    backgroundElevated: "#080B12",
    surface: "rgba(255,255,255,0.06)",
    surfaceStrong: "rgba(255,255,255,0.10)",
    border: "rgba(255,255,255,0.12)",
    borderStrong: "rgba(255,255,255,0.20)",
    text: "#EAF0FA",
    muted: "#9DAAC2",
    mutedDim: "#7C8BA5",
    primary: "#2E8BFF",
    primaryStrong: "#1E6FE0",
    primarySoft: "#5BA6FF",
    success: "#3DF5A0",
    warning: "#F5B83D",
    danger: "#FF5C7A",
    violet: "#8B5CF6",
    violetSoft: "#B79CFF"
  },
  gradient: {
    cta: "linear-gradient(135deg, #2E8BFF, #1E6FE0)",
    brand: "linear-gradient(120deg, #5BA6FF, #8B5CF6 55%, #3DF5A0)",
    icon: "linear-gradient(135deg, #2E8BFF, #8B5CF6)"
  },
  font: {
    display: "'Satoshi', 'General Sans', system-ui, sans-serif",
    body: "'General Sans', system-ui, -apple-system, sans-serif"
  },
  radius: {
    sm: "8px",
    md: "12px",
    lg: "16px",
    xl: "22px"
  },
  shadow: {
    glass: "0 28px 90px rgba(0,0,0,0.34)",
    card3d: "inset 0 1px 0 rgba(255,255,255,0.12), 0 18px 55px rgba(0,0,0,0.28)",
    primaryGlow: "0 0 40px rgba(56,189,248,0.26)",
    successGlow: "0 0 30px rgba(70,242,166,0.22)",
    dangerGlow: "0 0 30px rgba(251,63,122,0.24)"
  },
  motion: {
    reveal: "180ms ease-out",
    hover: "140ms ease",
    press: "80ms ease",
    modal: "180ms ease-out",
    shimmer: "1.6s linear infinite"
  }
} as const;

export type StatusTone = "online" | "offline" | "session" | "warning" | "error" | "admin" | "success";
