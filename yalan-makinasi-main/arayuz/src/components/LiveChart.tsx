import React, { useEffect, useRef } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';
import { OlcumData } from '../services/websocket';

interface LiveChartProps {
  dataStream: OlcumData[];
}

const COLORS = {
  hr: '#FB7C45',
  gsr: '#4F8CFF',
  resp: '#2DD4A7',
};

const gradientFill = (color: string) => (u: uPlot) => {
  const g = u.ctx.createLinearGradient(0, u.bbox.top, 0, u.bbox.top + u.bbox.height);
  g.addColorStop(0, color + '40');
  g.addColorStop(1, color + '00');
  return g;
};

const axisBase = {
  stroke: '#94a3b8',
  font: '11px Inter, system-ui, sans-serif',
  grid: { stroke: 'rgba(148,163,184,0.10)', width: 1 },
  ticks: { show: false },
};

export const LiveChart: React.FC<LiveChartProps> = ({ dataStream }) => {
  const wrapRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const uplotInstance = useRef<uPlot | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    const spline = (uPlot.paths as any).spline?.();

    const lineSeries = (label: string, color: string, scale: string): uPlot.Series => ({
      label,
      scale,
      stroke: color,
      width: 2.5,
      fill: gradientFill(color),
      points: { show: false },
      ...(spline ? { paths: spline } : {}),
    });

    const opts: uPlot.Options = {
      width: chartRef.current.clientWidth || 600,
      height: 280,
      legend: { show: false },
      cursor: {
        points: { size: 9, width: 2, fill: '#0f172a' },
        drag: { x: false, y: false },
      },
      scales: {
        x: { time: false },
        hr: { auto: true },
        gsr: { auto: true },
        resp: { auto: true },
      },
      axes: [
        { ...axisBase, scale: 'x', size: 36 },
        { ...axisBase, scale: 'hr', side: 3, size: 48 },
        { ...axisBase, scale: 'gsr', side: 1, size: 52, grid: { show: false } },
      ],
      series: [
        { label: 'Süre (sn)' },
        lineSeries('Nabız BPM', COLORS.hr, 'hr'),
        lineSeries('GSR mV', COLORS.gsr, 'gsr'),
        lineSeries('Solunum nefes/dk', COLORS.resp, 'resp'),
      ],
    };

    uplotInstance.current = new uPlot(opts, [[], [], [], []], chartRef.current);

    const ro = new ResizeObserver(() => {
      if (chartRef.current && uplotInstance.current) {
        uplotInstance.current.setSize({
          width: chartRef.current.clientWidth,
          height: 280,
        });
      }
    });
    if (wrapRef.current) ro.observe(wrapRef.current);

    return () => {
      ro.disconnect();
      uplotInstance.current?.destroy();
    };
  }, []);

  useEffect(() => {
    if (!uplotInstance.current || dataStream.length === 0) return;

    const xVals = dataStream.map((_, i) => i);
    const hrVals = dataStream.map((d) => d.heartRate);
    const gsrVals = dataStream.map((d) => d.gsr);
    const respVals = dataStream.map((d) => d.respiration);

    uplotInstance.current.setData([xVals, hrVals, gsrVals, respVals]);
  }, [dataStream]);

  const last = dataStream[dataStream.length - 1];
  const fmt = (v: number | undefined) =>
    typeof v === 'number' && !Number.isNaN(v) ? v.toFixed(1) : '--';

  const chips = [
    { label: 'Nabız', unit: 'BPM', value: fmt(last?.heartRate), color: COLORS.hr },
    { label: 'GSR', unit: 'mV', value: fmt(last?.gsr), color: COLORS.gsr },
    { label: 'Solunum', unit: 'nefes/dk', value: fmt(last?.respiration), color: COLORS.resp },
  ];

  const live = dataStream.length > 0;

  return (
    <div
      ref={wrapRef}
      className="relative overflow-hidden rounded-3xl border border-slate-700/50 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 p-6 shadow-xl shadow-slate-900/20"
    >
      {/* Arka plan ışıması */}
      <div className="pointer-events-none absolute -top-24 -right-24 h-64 w-64 rounded-full bg-blue-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -left-24 h-64 w-64 rounded-full bg-emerald-500/10 blur-3xl" />

      <div className="relative mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-white">Canlı sinyal zaman çizgisi</h3>
          <p className="mt-1 text-xs text-slate-400">
            Üç ayrı ölçek, ortak zaman ekseni. Kesikli çizgiler soru olaylarını gösterir.
          </p>
        </div>
        <span
          className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold ${
            live
              ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-300'
              : 'border-slate-600 bg-slate-800 text-slate-400'
          }`}
        >
          <span className="relative flex h-2 w-2">
            {live && (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            )}
            <span
              className={`relative inline-flex h-2 w-2 rounded-full ${
                live ? 'bg-emerald-400' : 'bg-slate-500'
              }`}
            />
          </span>
          {live ? 'CANLI' : 'BEKLENİYOR'}
        </span>
      </div>

      {/* Anlık değer rozetleri */}
      <div className="relative mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        {chips.map((c) => (
          <div
            key={c.label}
            className="flex items-center gap-3 rounded-2xl border border-white/5 bg-white/5 px-4 py-3 backdrop-blur"
          >
            <span
              className="h-9 w-1.5 rounded-full"
              style={{ backgroundColor: c.color, boxShadow: `0 0 12px ${c.color}99` }}
            />
            <div>
              <div className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
                {c.label}
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold tabular-nums text-white">{c.value}</span>
                <span className="text-xs text-slate-400">{c.unit}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div ref={chartRef} className="relative w-full overflow-hidden" />
    </div>
  );
};