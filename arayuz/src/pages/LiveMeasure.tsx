import React, { useEffect, useMemo, useState } from 'react';
import { Play, Square, Activity, Droplets, Wind, HeartPulse } from 'lucide-react';
import { SensorCard } from '../components/SensorCard';
import { BaglantiDurumu, useOlcumStream } from '../services/websocket';
import { sessionService } from '../services/api';

interface LiveMeasureProps {
  onDurum?: (durum: BaglantiDurumu) => void;
}

export const LiveMeasure: React.FC<LiveMeasureProps> = ({ onDurum }) => {
  const [running, setRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [kayitMesaji, setKayitMesaji] = useState('');
  const { data: rawStream, status, clear } = useOlcumStream(running);

  // Gelen canlı veriyi güvenli formata dönüştürme
  const dataStream = useMemo(() => {
    if (!Array.isArray(rawStream)) return [];
    return rawStream.map((d: any) => ({
      timestamp: d?.timestamp || Date.now(),
      heartRate: Number(d?.heartRate ?? d?.ppg ?? 0),
      gsr: Number(d?.gsr ?? 0),
      respiration: Number(d?.respiration ?? 0),
    }));
  }, [rawStream]);

  useEffect(() => {
    onDurum?.(status);
  }, [status, onDurum]);

  useEffect(() => () => onDurum?.('kapali'), [onDurum]);

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [running]);

  const last = dataStream[dataStream.length - 1];

  const kartDurumu = !running
    ? 'Beklemede'
    : status !== 'bagli'
      ? 'Bağlanıyor'
      : last
        ? 'Canlı'
        : 'Hesaplanıyor';

  const series = (pick: (d: any) => number) => dataStream.slice(-30).map(pick);

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

  const sonucuKaydet = async () => {
    const kayitId = sessionStorage.getItem('aktifOturumId');
    if (!kayitId) {
      setKayitMesaji('Kayıt için önce Yeni Oturum ekranından "Ölçüme geç" ile başlayın.');
      return;
    }
    if (dataStream.length === 0) {
      setKayitMesaji('Kaydedilecek ölçüm verisi oluşmadı.');
      return;
    }
    const ortalama = (vals: number[]) => vals.reduce((a, b) => a + b, 0) / vals.length;
    try {
      await sessionService.finishSession(kayitId, {
        ortalama_bpm: Math.round(ortalama(dataStream.map((d) => d.heartRate)) * 10) / 10,
        ortalama_gsr: Math.round(ortalama(dataStream.map((d) => d.gsr)) * 10) / 10,
        sure_sn: elapsed,
      });
      sessionStorage.removeItem('aktifOturumId');
      setKayitMesaji('Oturum sonuçları kaydedildi. Oturum Geçmişi sayfasında görebilirsiniz.');
    } catch (err) {
      console.error('Oturum sonucu kaydedilemedi:', err);
      setKayitMesaji('Oturum sonuçları kaydedilemedi. Backend sunucusunun açık olduğundan emin olun.');
    }
  };

  const toggle = () => {
    if (running) {
      void sonucuKaydet();
    } else {
      clear();
      setElapsed(0);
      setKayitMesaji('');
    }
    setRunning((r) => !r);
  };

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
          <h1 className="text-3xl font-black tracking-tight text-brand-navy">Canlı Ölçüm</h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="rounded-xl border border-gray-200 bg-white px-4 py-2 text-center shadow-card">
            <div className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Süre</div>
            <div className="font-mono text-lg font-black tabular-nums text-brand-navy">
              {mm}:{ss}
            </div>
          </div>
          <button
            onClick={toggle}
            className={`flex items-center gap-2 rounded-xl px-5 py-3 text-xs font-bold text-white transition hover:-translate-y-0.5 cursor-pointer ${
              running ? 'bg-rose-500 hover:bg-rose-600' : 'bg-brand-orange shadow-glow hover:bg-orange-500'
            }`}
          >
            {running ? <Square size={14} /> : <Play size={14} />}
            {running ? 'Durdur' : 'Ölçümü Başlat'}
          </button>
        </div>
      </div>

      {running && !last && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs font-medium text-amber-800">
          {status === 'bagli'
            ? 'Veri hattına bağlandı. Biyosinyal verileri aktarılıyor…'
            : 'Veri hattına bağlanılıyor…'}
        </div>
      )}

      {kayitMesaji && (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs font-medium text-emerald-800">
          {kayitMesaji}
        </div>
      )}

      {/* Sensör kartları */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <SensorCard
          label="Nabız"
          value={last ? last.heartRate.toFixed(0) : undefined}
          unit="BPM"
          color="#FB7C45"
          history={series((d) => d.heartRate)}
          icon={<HeartPulse size={18} />}
          status={kartDurumu}
        />
        <SensorCard
          label="GSR"
          value={last ? last.gsr.toFixed(1) : undefined}
          unit="mV"
          color="#4F8CFF"
          history={series((d) => d.gsr)}
          icon={<Droplets size={18} />}
          status={kartDurumu}
        />
        <SensorCard
          label="Solunum"
          value={last ? last.respiration.toFixed(0) : undefined}
          unit="nefes/dk"
          color="#2DD4A7"
          history={series((d) => d.respiration)}
          icon={<Wind size={18} />}
          status={kartDurumu}
        />
      </div>

      {/* Özet İstatistik Tablosu */}
      <div className="rounded-3xl border border-gray-100 bg-white p-6 shadow-card">
        <div className="mb-4 flex items-center gap-2">
          <Activity size={16} className="text-brand-orange" />
          <h3 className="text-base font-bold text-brand-navy">Oturum Özeti (Anlık)</h3>
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