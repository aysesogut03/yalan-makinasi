import React, { useEffect, useState } from 'react';
import { Activity, HeartPulse, Droplets, Wind, AlertTriangle, FileText, CheckCircle2 } from 'lucide-react';
import { sessionService, participantService } from '../services/api';

interface Oturum {
  id: number;
  katilimci_id: number;
  test_adi?: string;
  notlar?: string;
  ortalama_bpm?: number;
  ortalama_gsr?: number;
  yalan_skoru?: number;
}

export const SessionSummary: React.FC = () => {
  const [lastSession, setLastSession] = useState<Oturum | null>(null);
  const [katilimciAdi, setKatilimciAdi] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [oturumlar, katilimcilar] = await Promise.all([
          sessionService.getSessions(),
          participantService.getParticipants(),
        ]);

        if (oturumlar.length > 0) {
          // En son tamamlanan/kaydedilen oturumu al
          const sonOturum = oturumlar[oturumlar.length - 1];
          setLastSession(sonOturum);

          const kat = katilimcilar.find((k: any) => k.id === sonOturum.katilimci_id);
          if (kat) {
            setKatilimciAdi(kat.ad_soyad);
          }
        }
      } catch (err) {
        console.error('Oturum özeti yüklenirken hata:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="py-12 text-center text-xs text-gray-400">Oturum verileri analiz ediliyor...</div>;
  }

  if (!lastSession) {
    return (
      <div className="mx-auto mt-12 max-w-xl text-center rounded-3xl border border-gray-100 bg-white p-12 shadow-card">
        <Activity className="mx-auto mb-3 text-brand-orange" size={32} />
        <h3 className="text-base font-bold text-brand-navy">Tamamlanmış Oturum Bulunamadı</h3>
        <p className="mt-1 text-xs text-gray-400">
          Özet analizini görüntülemek için önce yeni bir test oturumu başlatıp kaydedin.
        </p>
      </div>
    );
  }

  const yalanSkoru = lastSession.yalan_skoru ?? 0;
  const yuksekRisk = yalanSkoru > 50;

  return (
    <div className="max-w-6xl animate-fadeUp space-y-6">
      {/* Başlık */}
      <div className="flex items-start justify-between">
        <div>
          <span className="mb-1 block text-xs font-bold uppercase tracking-[0.18em] text-brand-orange">
            ARAŞTIRMA ARAYÜZÜ / 03
          </span>
          <h1 className="text-3xl font-black tracking-tight text-brand-navy">Oturum Özeti ve Analiz</h1>
        </div>
        <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700 border border-emerald-200">
          Oturum #{String(lastSession.id).padStart(3, '0')} · Tamamlandı
        </span>
      </div>

      {/* Katılımcı Bilgisi & Risk Skoru Kartı */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="rounded-3xl border border-gray-100 bg-white p-6 shadow-card space-y-2 lg:col-span-2">
          <div className="flex items-center gap-2 text-xs font-bold text-gray-400 uppercase tracking-wider">
            <FileText size={16} className="text-brand-orange" /> Oturum Bilgileri
          </div>
          <h2 className="text-2xl font-black text-brand-navy">{lastSession.test_adi || 'Poligraf Biyosinyal Oturumu'}</h2>
          <p className="text-xs text-gray-500">
            <strong>Katılımcı:</strong> {katilimciAdi || `Katılımcı #${lastSession.katilimci_id}`}
          </p>
          <p className="text-xs text-gray-500 pt-2 border-t border-gray-100">
            <strong>Gözlem Notları:</strong> {lastSession.notlar || 'Herhangi bir özel not girilmedi.'}
          </p>
        </div>

        <div className={`rounded-3xl border p-6 shadow-card flex flex-col justify-between ${
          yuksekRisk ? 'bg-rose-50/60 border-rose-200' : 'bg-emerald-50/60 border-emerald-200'
        }`}>
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-gray-500">Olası Tepki Skoru</span>
              {yuksekRisk ? (
                <AlertTriangle size={18} className="text-rose-500" />
              ) : (
                <CheckCircle2 size={18} className="text-emerald-500" />
              )}
            </div>
            <div className="mt-2 text-4xl font-black tabular-nums text-brand-navy">
              %{yalanSkoru}
            </div>
          </div>
          <p className="mt-4 text-[11px] leading-relaxed text-gray-600">
            {yuksekRisk
              ? 'Soru anlarında fizyolojik sinyallerde (GSR / Nabız) belirgin anomali ve sapmalar tespit edildi.'
              : 'Fizyolojik sinyal değerleri referans aralığında ve stabil seyretti.'}
          </p>
        </div>
      </div>

      {/* Biyosinyal Ortalamaları */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-gray-100 bg-white p-5 shadow-card">
          <div className="mb-2 flex items-center gap-2 text-xs font-bold text-gray-400">
            <HeartPulse size={16} className="text-[#FB7C45]" /> Ortalama Nabız
          </div>
          <div className="text-3xl font-black tabular-nums text-brand-navy">
            {lastSession.ortalama_bpm || '--'} <span className="text-xs text-gray-400 font-semibold">BPM</span>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-100 bg-white p-5 shadow-card">
          <div className="mb-2 flex items-center gap-2 text-xs font-bold text-gray-400">
            <Droplets size={16} className="text-[#4F8CFF]" /> Ortalama GSR
          </div>
          <div className="text-3xl font-black tabular-nums text-brand-navy">
            {lastSession.ortalama_gsr || '--'} <span className="text-xs text-gray-400 font-semibold">mV</span>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-100 bg-white p-5 shadow-card">
          <div className="mb-2 flex items-center gap-2 text-xs font-bold text-gray-400">
            <Wind size={16} className="text-[#2DD4A7]" /> Solunum Durumu
          </div>
          <div className="text-3xl font-black tabular-nums text-brand-navy">
            Stabil <span className="text-xs text-gray-400 font-semibold">14/dk</span>
          </div>
        </div>
      </div>

      <footer className="pt-2 text-[11px] text-gray-400">
        Sinyal Hattı · Araştırma demosu · Tıbbi veya adli kesinlik taşımaz.
      </footer>
    </div>
  );
};

export default SessionSummary;