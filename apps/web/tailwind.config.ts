import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./features/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        graphite: "#111827",
        navy: "#050814",
        electric: "#38bdf8",
        mint: "#46f2a6",
        shb: {
          bg: "var(--shb-bg)",
          "bg-2": "var(--shb-bg-2)",
          "bg-soft": "var(--shb-bg-soft)",
          surface: "var(--shb-surface)",
          "surface-strong": "var(--shb-surface-strong)",
          border: "var(--shb-border)",
          "border-strong": "var(--shb-border-strong)",
          text: "rgb(var(--shb-text-rgb) / <alpha-value>)",
          muted: "rgb(var(--shb-muted-rgb) / <alpha-value>)",
          primary: "rgb(var(--shb-primary-rgb) / <alpha-value>)",
          "primary-strong": "rgb(var(--shb-primary-strong-rgb) / <alpha-value>)",
          success: "rgb(var(--shb-success-rgb) / <alpha-value>)",
          warning: "rgb(var(--shb-warning-rgb) / <alpha-value>)",
          danger: "rgb(var(--shb-danger-rgb) / <alpha-value>)",
          violet: "rgb(var(--shb-violet-rgb) / <alpha-value>)"
        }
      },
      borderRadius: {
        sm: "0.5rem",
        md: "0.75rem",
        lg: "1rem",
        xl: "1.375rem"
      },
      boxShadow: {
        glow: "0 0 36px rgba(56, 189, 248, 0.22)",
        glass: "var(--shb-shadow-glass)",
        "card-3d": "var(--shb-shadow-card-3d)",
        "glow-primary": "var(--shb-glow-primary)",
        "glow-success": "var(--shb-glow-success)",
        "glow-danger": "var(--shb-glow-danger)"
      },
      backgroundImage: {
        "app-grid":
          "linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.028) 1px, transparent 1px)",
        "liquid-panel": "linear-gradient(180deg, rgba(255,255,255,0.10), rgba(255,255,255,0.045))",
        "primary-cta": "linear-gradient(135deg, #38bdf8, #2563eb 52%, #46f2a6)"
      },
      keyframes: {
        reveal: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" }
        },
        "soft-pulse": {
          "0%, 100%": { opacity: "0.72" },
          "50%": { opacity: "1" }
        },
        "drawer-in": {
          "0%": { opacity: "0", transform: "translateX(18px)" },
          "100%": { opacity: "1", transform: "translateX(0)" }
        }
      },
      animation: {
        reveal: "reveal 180ms ease-out both",
        shimmer: "shimmer 1.6s linear infinite",
        "soft-pulse": "soft-pulse 1.8s ease-in-out infinite",
        "drawer-in": "drawer-in 180ms ease-out both"
      }
    }
  },
  plugins: []
};

export default config;
