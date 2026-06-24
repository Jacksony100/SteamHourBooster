"use client";

export type Bar = { value: number; win?: boolean | null };

/** Tiny inline line chart (e.g. ELO trend next to the headline number). */
export function Sparkline({ values, color = "#2e8bff", width = 96, height = 28 }: { values: number[]; color?: string; width?: number; height?: number }) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const pts = values
    .map((v, i) => `${((i / (values.length - 1)) * (width - 2) + 1).toFixed(1)},${(height - 2 - ((v - min) / span) * (height - 4)).toFixed(1)}`)
    .join(" ");
  const up = values[values.length - 1] >= values[0];
  return (
    <svg viewBox={`0 0 ${width} ${height}`} width={width} height={height} role="img" aria-label="ELO sparkline" className="inline-block align-middle">
      <polyline points={pts} fill="none" stroke={up ? "#3DF5A0" : color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

/** Per-match bar chart (e.g. K/D or ADR) with an average reference line. Pure SVG. */
export function PerfBars({
  points,
  label,
  threshold,
  fixed = 0,
  height = 132,
}: {
  points: Bar[];
  label: string;
  threshold?: number;       // values >= threshold are "good" (green) when no win flag
  fixed?: number;           // decimals for the average readout
  height?: number;
}) {
  const vals = points.map((p) => p.value).filter((v) => Number.isFinite(v));
  if (vals.length < 2) return null;

  const W = 640;
  const PAD = { t: 18, r: 44, b: 12, l: 10 };
  const innerW = W - PAD.l - PAD.r;
  const innerH = height - PAD.t - PAD.b;
  const baseline = PAD.t + innerH;
  const max = Math.max(...vals, threshold ?? 0) * 1.08 || 1;
  const n = points.length;
  const slot = innerW / n;
  const bw = Math.max(2, slot * 0.62);
  const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
  const avgY = baseline - (avg / max) * innerH;

  function color(p: Bar) {
    if (p.win === true) return "#3DF5A0";
    if (p.win === false) return "#FF5C7A";
    if (threshold != null) return p.value >= threshold ? "#3DF5A0" : "#5ba6ff";
    return "#5ba6ff";
  }

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <span className="text-xs uppercase tracking-wide text-slate-400">{label} · last {n}</span>
        <span className="text-xs text-slate-400">avg <span className="font-semibold text-white">{avg.toFixed(fixed)}</span></span>
      </div>
      <svg viewBox={`0 0 ${W} ${height}`} className="w-full" style={{ height: "auto" }} role="img" aria-label={`${label} per match, average ${avg.toFixed(fixed)}`}>
        <line x1={PAD.l} y1={baseline} x2={W - PAD.r} y2={baseline} stroke="rgba(255,255,255,0.08)" />
        {points.map((p, i) => {
          if (!Number.isFinite(p.value)) return null;
          const h = Math.max(1, (p.value / max) * innerH);
          const x = PAD.l + i * slot + (slot - bw) / 2;
          return <rect key={i} x={x} y={baseline - h} width={bw} height={h} rx="1.5" fill={color(p)} opacity={0.9} />;
        })}
        <line x1={PAD.l} y1={avgY} x2={W - PAD.r} y2={avgY} stroke="rgba(255,255,255,0.45)" strokeWidth="1" strokeDasharray="4 3" />
        <text x={W - PAD.r + 5} y={avgY + 3} fontSize="11" fill="#9daac2">{avg.toFixed(fixed)}</text>
      </svg>
    </div>
  );
}
