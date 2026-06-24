"use client";

import { useId, useState } from "react";
import { motion } from "framer-motion";

import type { EloPoint } from "./types";

const W = 640;
const PAD = { t: 20, r: 50, b: 20, l: 10 };

type Geom = { x: (i: number, n: number) => number; y: (elo: number) => number; innerH: number; height: number };

function makeGeom(height: number, min: number, max: number): Geom {
  const innerW = W - PAD.l - PAD.r;
  const innerH = height - PAD.t - PAD.b;
  return {
    innerH,
    height,
    x: (i, n) => (n <= 1 ? PAD.l + innerW / 2 : PAD.l + (i / (n - 1)) * innerW),
    y: (elo) => (max === min ? PAD.t + innerH / 2 : PAD.t + (1 - (elo - min) / (max - min)) * innerH),
  };
}

function linePath(points: EloPoint[], g: Geom): string {
  const n = points.length;
  return points.map((p, i) => `${i ? "L" : "M"}${g.x(i, n).toFixed(1)},${g.y(p.elo).toFixed(1)}`).join(" ");
}

function DeltaBadge({ delta }: { delta: number }) {
  if (delta === 0) return <span className="text-xs text-slate-500">±0</span>;
  const up = delta > 0;
  return (
    <span
      className="rounded-md px-1.5 py-0.5 text-xs font-semibold"
      style={up ? { background: "rgba(61,245,160,.14)", color: "#3DF5A0" } : { background: "rgba(255,92,122,.14)", color: "#FF5C7A" }}
    >
      {up ? "▲" : "▼"} {Math.abs(delta)}
    </span>
  );
}

function ApproxTag() {
  return (
    <span className="rounded-md px-1.5 py-0.5 text-[10px] font-medium text-slate-400" style={{ background: "rgba(255,255,255,0.06)" }} title="Reconstructed from recent win/loss (±25 per match). Endpoint is exact; intermediate values are estimated.">
      ≈ approx
    </span>
  );
}

/** Single-player ELO trend: animated area + line with an interactive hover tooltip. */
export function EloChart({ points, height = 184, color = "#2e8bff", approx = false }: { points: EloPoint[]; height?: number; color?: string; approx?: boolean }) {
  const gid = useId().replace(/:/g, "");
  const [hover, setHover] = useState<number | null>(null);
  const n = points.length;
  if (n === 0) return null;

  const elos = points.map((p) => p.elo);
  const min = Math.min(...elos);
  const max = Math.max(...elos);
  const g = makeGeom(height, min, max);
  const baseline = PAD.t + g.innerH;
  const line = linePath(points, g);
  const area = `${line} L${g.x(n - 1, n).toFixed(1)},${baseline.toFixed(1)} L${g.x(0, n).toFixed(1)},${baseline.toFixed(1)} Z`;

  const last = points[n - 1].elo;
  const delta = last - points[0].elo;
  const active = hover ?? n - 1;
  const ap = points[active];
  const ax = g.x(active, n);
  const ay = g.y(ap.elo);
  const flip = ax > W * 0.62;
  // Prefer above the point; if there's no room near the top rail, drop below it.
  const ttY = ay - 38 >= PAD.t ? ay - 38 : Math.min(ay + 10, baseline - 34);

  function onMove(e: React.MouseEvent<SVGRectElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    if (rect.width === 0) return;
    const ratio = (e.clientX - rect.left) / rect.width;
    setHover(Math.max(0, Math.min(n - 1, Math.round(ratio * (n - 1)))));
  }

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <span className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
          ELO trend · last {n}
          {approx && <ApproxTag />}
        </span>
        <span className="flex items-center gap-2">
          <span className="font-display text-lg font-bold text-white">{last}</span>
          <DeltaBadge delta={delta} />
        </span>
      </div>
      <svg viewBox={`0 0 ${W} ${height}`} className="w-full" style={{ height: "auto" }} role="img" aria-label={`ELO trend over the last ${n} matches, currently ${last}`}>
        <defs>
          <linearGradient id={`fill-${gid}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.34" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* top / bottom rails */}
        <line x1={PAD.l} y1={PAD.t} x2={W - PAD.r} y2={PAD.t} stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
        <line x1={PAD.l} y1={baseline} x2={W - PAD.r} y2={baseline} stroke="rgba(255,255,255,0.06)" strokeWidth="1" />

        {n > 1 && <motion.path d={area} fill={`url(#fill-${gid})`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }} />}
        {n > 1 && (
          <motion.path
            d={line}
            fill="none"
            stroke={color}
            strokeWidth="2.5"
            strokeLinejoin="round"
            strokeLinecap="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 0.7, ease: "easeOut" }}
          />
        )}

        {/* axis value labels */}
        <text x={W - PAD.r + 6} y={PAD.t + 4} fontSize="11" fill="#7c8ba5">{max}</text>
        <text x={W - PAD.r + 6} y={baseline} fontSize="11" fill="#7c8ba5">{min}</text>

        {/* hover guide + active dot */}
        <line x1={ax} y1={PAD.t} x2={ax} y2={baseline} stroke="rgba(255,255,255,0.18)" strokeWidth="1" strokeDasharray="3 3" />
        <circle cx={ax} cy={ay} r="4.5" fill={color} stroke="#05070d" strokeWidth="2" />

        {/* tooltip */}
        <g transform={`translate(${flip ? ax - 96 : ax + 8}, ${ttY})`} pointerEvents="none">
          <rect width="88" height="34" rx="7" fill="rgba(8,11,18,0.92)" stroke="rgba(255,255,255,0.12)" />
          <text x="8" y="15" fontSize="12" fontWeight="700" fill="#eaf0fa">{ap.elo} ELO</text>
          <text x="8" y="28" fontSize="10" fill="#9daac2">{ap.date ?? "—"}</text>
        </g>

        {/* mouse capture over the plotting area */}
        <rect
          x={PAD.l}
          y={PAD.t}
          width={W - PAD.l - PAD.r}
          height={g.innerH}
          fill="transparent"
          style={{ cursor: "crosshair" }}
          onMouseMove={onMove}
          onMouseLeave={() => setHover(null)}
        />
      </svg>
    </div>
  );
}

export type Series = { points: EloPoint[]; color: string; label: string };

/** Multi-player ELO overlay (2–5). Each series spans the full width (normalised by recency). */
export function EloCompareChart({ series, height = 200, approx = false }: { series: Series[]; height?: number; approx?: boolean }) {
  const all = series.flatMap((s) => s.points.map((p) => p.elo));
  if (all.length === 0) return null;
  const min = Math.min(...all);
  const max = Math.max(...all);
  const g = makeGeom(height, min, max);
  const baseline = PAD.t + g.innerH;
  const drawable = series.filter((s) => s.points.length > 0);

  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center gap-x-4 gap-y-1">
        <span className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
          ELO trend
          {approx && <ApproxTag />}
        </span>
        {series.map((s) => (
          <span key={s.label} className="flex items-center gap-1.5 text-xs">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
            <span className="font-medium text-white">{s.label}</span>
            {s.points.length > 0 && <span className="text-slate-400">{s.points[s.points.length - 1].elo}</span>}
          </span>
        ))}
      </div>
      <svg viewBox={`0 0 ${W} ${height}`} className="w-full" style={{ height: "auto" }} role="img" aria-label={`ELO trend comparison of ${series.map((s) => s.label).join(", ")}`}>
        <line x1={PAD.l} y1={PAD.t} x2={W - PAD.r} y2={PAD.t} stroke="rgba(255,255,255,0.06)" />
        <line x1={PAD.l} y1={baseline} x2={W - PAD.r} y2={baseline} stroke="rgba(255,255,255,0.06)" />
        <text x={W - PAD.r + 6} y={PAD.t + 4} fontSize="11" fill="#7c8ba5">{max}</text>
        <text x={W - PAD.r + 6} y={baseline} fontSize="11" fill="#7c8ba5">{min}</text>

        {drawable.map((s, si) => {
          const n = s.points.length;
          const end = s.points[n - 1];
          return (
            <g key={s.label}>
              {n > 1 && (
                <motion.path
                  d={linePath(s.points, g)}
                  fill="none"
                  stroke={s.color}
                  strokeWidth="2.5"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 0.7, ease: "easeOut", delay: si * 0.1 }}
                />
              )}
              <circle cx={g.x(n - 1, n)} cy={g.y(end.elo)} r="4" fill={s.color} stroke="#05070d" strokeWidth="2">
                <title>{`${s.label}: ${end.elo} ELO`}</title>
              </circle>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
