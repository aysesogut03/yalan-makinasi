import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Play, Square, Activity, Droplets, Wind, HeartPulse } from 'lucide-react';
import { LiveChart } from '../components/LiveChart';
import { SensorCard } from '../components/SensorCard';
import { OlcumData } from '../services/websocket';

const MAX_POINTS = 120;

export const LiveMeasure: React.FC = () => {
  const [dataStream, setDataStream] = useState<OlcumData[]>([]);
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const tick = useRef(0);

  /* ===== VERİ KAYNAĞI: burayı kendi WebSocket/servis kodunla değiştir ===== */
  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => {
      tick.current += 1;
      const t = tick.current;
      const next = {
        heartRate: 70 + Math.sin(t / 6) * 3 + Math.random(),
        gsr: 1.49 + Math.sin(t / 10) * 0.05 + Math.random() * 0.01,
        respiration: 14 + Math.sin(t / 15) * 1.2,
      } as unknown as OlcumData;
      setDataStream((prev) => [...prev.slice(-(MAX_POINTS - 1)), next]);
      setElapsed((s) => s + 1);
    }, 1000);
    return () => clearInterval(id);
  }, [running]);
  /* ======================================================================== */

  const last = dataStream[dataStream.length - 1];

  const series = (pick: (d: OlcumData) => number) => dataStream.slice(-30).map(pick);

  const stats = useMemo(() => {
    const calc = (vals: number[]) => {
      if (!vals.length) return { min: '--', max: '--', avg: '--' };
      const min = Math.min(...vals);
      const max = Math.max(...vals);
      const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
      return { min: min.toFixed(1), max: max.toFixed(1), avg: avg.toFixed(1) };
    };
    return {
      Nabız: calc(dataStream.map((d) => d.heartRate)),
      GSR: calc(dataStream.map((d) => d.gsr)),
      Solunum: calc(dataStream.map((d) => d.respiration)),
    };
  }, [dataStream]);

  const mm = String(Math.floor(elapsed / 60)).padStart(2, '0');
  const ss = String(elapsed % 60).padStart(2, '0');

  return (
    <div className="max-w-6xl animate-fadeUp space-y-6">
      {/* Başlık + kontrol */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="mb-1 block text-xs font-bold uppercase tracking-[0.18em] text-brand-orange">
            ARAŞTIRMA ARAYÜZÜ / 04
          </span>
          <h1 className="text-3xl font-black tracking-tight text-brand-navy">Canlı ölçüm</h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="rounded-xl border border-gray-200 bg-white px-4 py-2 text-center shadow-card">
            <div className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Süre</div>
            <div className="font-mono text-lg font-black tabular-nums text-brand-navy">
              {mm}:{ss}
            </div>
          </div>
          <button
            onClick={() => setRunning((r) => !r)}
            className={`flex items-center gap-2 rounded-xl px-5 py-3 text-xs font-bold text-white transition hover:-translate-y-0.5 ${
              running ? 'bg-rose-500 hover:bg-rose-600' : 'bg-brand-orange shadow-glow hover:bg-orange-500'
            }`}
          >
            {running ? <Square size={14} /> : <Play size={14} />}
            {running ? 'Durdur' : 'Ölçümü başlat'}
          </button>
        </div>
      </div>

      {/* Sensör kartları */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <SensorCard
          label="Nabız"
          value={last ? last.heartRate.toFixed(0) : undefined}
          unit="BPM"
          color="#FB7C45"
          history={series((d) => d.heartRate)}
          icon={<HeartPulse size={18} />}
          status={running ? 'Canlı' : 'Beklemede'}
        />
        <SensorCard
          label="GSR"
          value={last ? last.gsr.toFixed(3) : undefined}
          unit="mV"
          color="#4F8CFF"
          history={series((d) => d.gsr)}
          icon={<Droplets size={18} />}
          status={running ? 'Canlı' : 'Beklemede'}
        />
        <SensorCard
          label="Solunum"
          value={last ? last.respiration.toFixed(0) : undefined}
          unit="nefes/dk"
          color="#2DD4A7"
          history={series((d) => d.respiration)}
          icon={<Wind size={18} />}
          status={running ? 'Canlı' : 'Beklemede'}
        />
      </div>

      {/* Ana grafik */}
      <LiveChart dataStream={dataStream} />

      {/* Özet istatistik */}
      <div className="rounded-3xl border border-gray-100 bg-white p-6 shadow-card">
        <div className="mb-4 flex items-center gap-2">
          <Activity size={16} className="text-brand-orange" />
          <h3 className="text-base font-bold text-brand-navy">Oturum özeti (anlık)</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-[11px] uppercase tracking-wider text-gray-400">
                <th className="pb-3 font-bold">Sinyal</th>
                <th className="pb-3 font-bold">Min</th>
                <th className="pb-3 font-bold">Ortalama</th>
                <th className="pb-3 font-bold">Maks</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(stats).map(([name, s]) => (
                <tr key={name} className="border-t border-gray-100">
                  <td className="py-3 font-semibold text-brand-navy">{name}</td>
                  <td className="py-3 tabular-nums text-gray-600">{s.min}</td>
                  <td className="py-3 tabular-nums font-bold text-brand-navy">{s.avg}</td>
                  <td className="py-3 tabular-nums text-gray-600">{s.max}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <p className="text-[11px] text-gray-400">
        Bu sistem yalanı kesin olarak tespit etmez. Değerler yalnızca araştırma amaçlıdır.
      </p>
    </div>
  );
};

export default LiveMeasure;