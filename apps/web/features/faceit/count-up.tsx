"use client";

import { useEffect, useRef, useState } from "react";

/** Animated count-up to a numeric value. Respects prefers-reduced-motion. */
export function CountUp({ value, decimals = 0, suffix = "", duration = 600 }: { value: number; decimals?: number; suffix?: string; duration?: number }) {
  const [display, setDisplay] = useState(value);
  const raf = useRef<number | null>(null);

  useEffect(() => {
    const reduce = typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduce || duration <= 0) {
      setDisplay(value);
      return;
    }
    const from = 0;
    let start: number | null = null;
    const step = (ts: number) => {
      if (start == null) start = ts;
      const p = Math.min(1, (ts - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(from + (value - from) * eased);
      if (p < 1) raf.current = requestAnimationFrame(step);
    };
    raf.current = requestAnimationFrame(step);
    return () => { if (raf.current) cancelAnimationFrame(raf.current); };
  }, [value, duration]);

  return <>{display.toFixed(decimals)}{suffix}</>;
}
