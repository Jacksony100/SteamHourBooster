"use client";

export type RadarSeries = { values: Record<string, number | null>; color: string; label?: string };

const AXES = ["Aim", "Damage", "HS%", "Entry", "Clutch", "Utility"];

/** Skill radar (0–100 per axis). Supports overlaying multiple players. Pure SVG. */
export function RadarChart({ series, size = 280 }: { series: RadarSeries[]; size?: number }) {
  if (!series.length) return null;
  const cx = size / 2;
  const cy = size / 2;
  const R = size / 2 - 38;
  const n = AXES.length;
  const angle = (i: number) => -Math.PI / 2 + (i * 2 * Math.PI) / n;
  const pt = (i: number, r: number) => [cx + r * Math.cos(angle(i)), cy + r * Math.sin(angle(i))];

  const rings = [0.25, 0.5, 0.75, 1];
  const polygon = (vals: Record<string, number | null>) =>
    AXES.map((ax, i) => {
      const v = vals[ax];
      const r = R * (v == null ? 0 : Math.max(0, Math.min(100, v)) / 100);
      const [x, y] = pt(i, r);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="mx-auto w-full max-w-[320px]" role="img" aria-label="Skill radar">
      {rings.map((rr, ri) => (
        <polygon
          key={ri}
          points={AXES.map((_, i) => pt(i, R * rr).map((c) => c.toFixed(1)).join(",")).join(" ")}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
        />
      ))}
      {AXES.map((ax, i) => {
        const [x, y] = pt(i, R);
        const [lx, ly] = pt(i, R + 16);
        return (
          <g key={ax}>
            <line x1={cx} y1={cy} x2={x} y2={y} stroke="rgba(255,255,255,0.08)" />
            <text x={lx} y={ly + 3} fontSize="11" fill="#9daac2" textAnchor={Math.abs(lx - cx) < 4 ? "middle" : lx > cx ? "start" : "end"}>
              {ax}
            </text>
          </g>
        );
      })}
      {series.map((s, si) => (
        <g key={si}>
          <polygon points={polygon(s.values)} fill={`${s.color}26`} stroke={s.color} strokeWidth="2" strokeLinejoin="round" />
          {AXES.map((ax, i) => {
            const v = s.values[ax];
            if (v == null) return null;
            const [x, y] = pt(i, R * (Math.max(0, Math.min(100, v)) / 100));
            return <circle key={ax} cx={x} cy={y} r="2.5" fill={s.color} />;
          })}
        </g>
      ))}
    </svg>
  );
}
