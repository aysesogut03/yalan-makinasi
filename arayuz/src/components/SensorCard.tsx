import React, { useId } from 'react';

interface SensorCardProps {
  label: string;
  value?: number | string;
  unit?: string;
  color?: string;
  history?: number[];
  status?: string;
  icon?: React.ReactNode;
}

const Spark: React.FC<{ data: number[]; color: string }> = ({ data, color }) => {
  const id = useId().replace(/:/g, '');
  if (data.length < 2) return <div className="h-12" />;

  const w = 200;
  const h = 48;
  const pad = 4;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => [
    (i / (data.length - 1)) * w,
    pad + (1 - (v - min) / range) * (h - pad * 2),
  ]);
  const line = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
  const area = `${line} L${w},${h} L0,${h} Z`;
  const last = pts[pts.length - 1];

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-12 w-full" preserveAspectRatio="none">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.30" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${id})`} />
      <path
        d={line}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
      <circle cx={last[0]} cy={last[1]} r="3" fill={color} />
    </svg>
  );
};

export const SensorCard: React.FC<SensorCardProps> = ({
  label,
  value,
  unit,
  color = '#EE6C4D',
  history = [],
  status,
  icon,
}) => {
  const hasValue = value !== undefined && value !== null && value !== '';

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-gray-100 bg-white p-5 shadow-card transition hover:-translate-y-0.5 hover:shadow-lg">
      {/* üst renk şeridi */}
      <span
        className="absolute inset-x-0 top-0 h-1"
        style={{ background: `linear-gradient(90deg, ${color}, ${color}33)` }}
      />

      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <span
            className="flex h-9 w-9 items-center justify-center rounded-xl"
            style={{ backgroundColor: color + '1A', color }}
          >
            {icon ?? <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />}
          </span>
          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
            {label}
          </span>
        </div>

        {status && (
          <span
            className="rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide"
            style={{ backgroundColor: color + '1A', color }}
          >
            {status}
          </span>
        )}
      </div>

      <div className="mb-2 flex items-baseline gap-1.5">
        <span className="text-3xl font-black tabular-nums text-brand-navy">
          {hasValue ? value : '--'}
        </span>
        {unit && <span className="text-xs font-semibold text-gray-400">{unit}</span>}
      </div>

      <Spark data={history} color={color} />
    </div>
  );
};

export default SensorCard;