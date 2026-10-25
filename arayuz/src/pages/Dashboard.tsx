import React, { useId } from 'react';

interface DashboardProps {
  onGoToMeasure: () => void;
  onGoToNewSession: () => void;
}

/* ---------- Küçük yardımcı bileşenler ---------- */

const Sparkline: React.FC<{ data: number[]; color: string }> = ({ data, color }) => {
  const id = useId().replace(/:/g, '');
  const w = 160;
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
    <svg
      viewBox={`0 0 ${w} ${h}`}
      width="100%"
      height={48}
      style={{ display: 'block', height: 48, width: '100%' }}
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.30" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${id})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
      <circle cx={last[0]} cy={last[1]} r="3" fill={color} />
    </svg>
  );
};

const iconProps = {
  width: 20,
  height: 20,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
  style: { width: 20, height: 20, flexShrink: 0 },
};

const IconLink = () => (
  <svg {...iconProps}>
    <path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7" />
    <path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7" />
  </svg>
);
const IconUser = () => (
  <svg {...iconProps}>
    <circle cx="12" cy="8" r="4" />
    <path d="M4 21a8 8 0 0 1 16 0" />
  </svg>
);
const IconCheck = () => (
  <svg {...iconProps}>
    <circle cx="12" cy="12" r="9" />
    <path d="m8 12 3 3 5-6" />
  </svg>
);

/* ---------- Simülasyon örnek verileri (yalnızca görsel) ---------- */

const HR = [68, 69, 71, 70, 72, 70, 69, 71, 73, 70, 69, 70];
const GSR = [1.42, 1.44, 1.43, 1.47, 1.49, 1.48, 1.5, 1.49, 1.51, 1.49, 1.5, 1.495];
const RESP = [14, 15, 14, 13, 14, 15, 14, 14, 13, 14, 14, 14];

export const Dashboard: React.FC<DashboardProps> = ({ onGoToMeasure, onGoToNewSession }) => {
  const metrics = [
    { label: 'BAĞLANTI DURUMU', value: 'Demo modu', icon: <IconLink />, tone: 'bg-amber-50 text-amber-600', dot: true },
    { label: 'AKTİF KATILIMCI', value: 'K-104', icon: <IconUser />, tone: 'bg-blue-50 text-blue-600' },
    { label: 'TAMAMLANAN OTURUM', value: '0', icon: <IconCheck />, tone: 'bg-emerald-50 text-emerald-600' },
  ];

  const sensors = [
    { name: 'Nabız', value: '70', unit: 'BPM', color: '#FB7C45', data: HR },
    { name: 'GSR', value: '1.495', unit: 'mV', color: '#4F8CFF', data: GSR },
    { name: 'Solunum', value: '14', unit: 'nefes/dk', color: '#2DD4A7', data: RESP },
  ];

  return (
    <div className="max-w-6xl space-y-6 animate-fadeUp">
      {/* Üst Başlık ve Rozet */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className="mb-1 block text-xs font-bold uppercase tracking-[0.18em] text-brand-orange">
            ARAŞTIRMA ARAYÜZÜ / 01
          </span>
          <h1 className="text-3xl font-black tracking-tight text-brand-navy sm:text-4xl">Deney paneli</h1>
        </div>
        <span className="inline-flex shrink-0 items-center gap-2 rounded-full border border-yellow-300/60 bg-brand-yellow/70 px-3 py-1.5 text-xs font-bold text-yellow-900">
          <span className="h-1.5 w-1.5 rounded-full bg-yellow-900/70" />
          ÖRNEK / SİMÜLASYON
        </span>
      </div>

      {/* Uyarı Bandı */}
      <div className="flex items-start gap-3 rounded-2xl border border-orange-200/70 bg-gradient-to-r from-orange-50 to-white p-4 text-xs leading-relaxed text-gray-700">
        <span className="mt-0.5 h-5 w-1 shrink-0 rounded-full bg-brand-orange" />
        <p>
          Bu sistem yalanı kesin olarak tespit etmez. Stres, hareket, sağlık durumu ve ortam gibi etkenler sinyalleri değiştirebilir.
        </p>
      </div>

      {/* Sinyal Hattı Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-navy via-[#17213d] to-brand-cardNav p-8 text-white shadow-xl shadow-brand-navy/25">
        {/* ızgara dokusu */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              'linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)',
            backgroundSize: '32px 32px',
          }}
        />
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-orange/20 blur-3xl" />

        {/* akan sinyal çizgisi */}
        <svg
          className="pointer-events-none absolute bottom-0 left-0 w-full opacity-60"
          style={{ height: 80, width: '100%' }}
          viewBox="0 0 600 80"
          width="100%"
          height={80}
          preserveAspectRatio="none"
        >
          <path
            className="pulse-line"
            d="M0,40 L90,40 L110,40 L125,10 L145,70 L160,40 L260,40 L280,40 L295,18 L312,62 L326,40 L430,40 L450,40 L465,8 L485,72 L500,40 L600,40"
            fill="none"
            stroke="#EE6C4D"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
        </svg>

        <div className="relative flex flex-wrap items-center justify-between gap-6">
          <div className="max-w-xl">
            <span className="mb-2 block text-xs font-bold uppercase tracking-[0.18em] text-orange-300">
              SİNYAL HATTI / DENEY PANELİ
            </span>
            <h2 className="mb-2 text-2xl font-bold sm:text-3xl">Sinyallerin ardındaki akış.</h2>
            <p className="text-xs leading-relaxed text-slate-300">
              Sensör görünümünden soru akışına: her adımı takip edin, verinin sınırlarını görün.
            </p>
          </div>
          <button
            onClick={onGoToNewSession}
            className="flex shrink-0 items-center gap-2 rounded-xl bg-brand-orange px-5 py-3 text-xs font-bold text-white shadow-glow transition hover:-translate-y-0.5 hover:bg-orange-500 active:translate-y-0"
          >
            Yeni oturum başlat ↗
          </button>
        </div>
      </div>

      {/* Metrik Kutuları */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 sm:gap-6">
        {metrics.map((m) => (
          <div
            key={m.label}
            className="group flex items-center gap-4 rounded-2xl border border-gray-100 bg-white p-5 shadow-card transition hover:-translate-y-0.5 hover:shadow-lg"
          >
            <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${m.tone}`}>
              {m.icon}
            </div>
            <div>
              <span className="mb-1 block text-[11px] font-bold uppercase tracking-wider text-gray-400">
                {m.label}
              </span>
              <p className="flex items-center gap-2 text-xl font-extrabold text-brand-navy">
                {m.dot && <span className="h-2 w-2 rounded-full bg-amber-400" />}
                {m.value}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Canlı Sensör Görünümü Kısayol Kartı */}
      <div className="space-y-5 rounded-3xl border border-gray-100 bg-white p-6 shadow-card">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-brand-navy">Canlı sensör görünümü · simülasyon</h3>
          <span className="rounded-full bg-gray-100 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-gray-500">
            Örnek veri
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {sensors.map((s) => (
            <div
              key={s.name}
              className="rounded-2xl border border-gray-100 bg-gray-50/60 p-4 transition hover:bg-white hover:shadow-card"
            >
              <div className="mb-1 flex items-center gap-2 text-sm text-gray-500">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: s.color }} />
                {s.name}
              </div>
              <div className="mb-2 flex items-baseline gap-1.5">
                <span className="text-3xl font-black tabular-nums text-brand-navy">{s.value}</span>
                <span className="text-xs font-semibold text-gray-400">{s.unit}</span>
              </div>
              <Sparkline data={s.data} color={s.color} />
            </div>
          ))}
        </div>

        <button
          onClick={onGoToMeasure}
          className="rounded-xl bg-brand-navy px-4 py-2.5 text-xs font-bold text-white transition hover:bg-brand-cardNav"
        >
          Ölçüm ekranını aç
        </button>
      </div>

      <footer className="pt-4 text-[11px] text-gray-400">
        Sinyal Hattı · Araştırma demosu · Tıbbi veya adli doğrulama aracı değildir.
      </footer>
    </div>
  );
};