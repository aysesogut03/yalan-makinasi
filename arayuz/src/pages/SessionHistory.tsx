import React, { useEffect, useState } from 'react';
import { History, Calendar, User, Activity, AlertCircle, FileText } from 'lucide-react';
import { sessionService, participantService } from '../services/api';

interface Oturum {
  id: number;
  katilimci_id: number;
  test_adi?: string;
  notlar?: string;
  ortalama_bpm?: number;
  ortalama_gsr?: number;
  yalan_skoru?: number;
  tarih?: string;
}

interface Katilimci {
  id: number;
  ad_soyad: string;
}

export const SessionHistory: React.FC = () => {
  const [oturumlar, setOturumlar] = useState<Oturum[]>([]);
  const [katilimcilar, setKatilimcilar] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Hem katılımcıları hem de oturumları paralel çekiyoruz
        const [oturumRes, katilimciRes] = await Promise.all([
          sessionService.getSessions(),
          participantService.getParticipants(),
        ]);

        // Katılımcıları kolay erişim için ID -> Ad Soyad haritasına çeviriyoruz
        const katMap: Record<number, string> = {};
        katilimciRes.forEach((k: Katilimci) => {
          katMap[k.id] = k.ad_soyad;
        });

        setKatilimcilar(katMap);
        setOturumlar(oturumRes);
      } catch (err) {
        console.error('Oturum geçmişi yüklenirken hata oluştu:', err);
        setError('Oturum geçmişi verileri çekilemedi.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="max-w-6xl animate-fadeUp space-y-6">
      {/* Üst Başlık */}
      <div className="flex items-center justify-between">
        <div>
          <span className="mb-1 block text-xs font-bold uppercase tracking-[0.18em] text-brand-orange">
            ARAŞTIRMA ARAYÜZÜ / 05
          </span>
          <h1 className="text-3xl font-black tracking-tight text-brand-navy">Oturum Geçmişi</h1>
        </div>
        <div className="flex items-center gap-2 rounded-2xl border border-gray-100 bg-white px-4 py-2 shadow-card">
          <History size={16} className="text-brand-orange" />
          <span className="text-xs font-bold text-brand-navy">
            Toplam Kayıt: {oturumlar.length}
          </span>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-2xl border border-red-200 bg-red-50 p-4 text-xs font-bold text-red-600">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* Oturum Listesi Tablosu */}
      <div className="rounded-3xl border border-gray-100 bg-white p-6 shadow-card">
        {loading ? (
          <div className="py-12 text-center text-xs text-gray-400">
            Oturum geçmişi yükleniyor...
          </div>
        ) : oturumlar.length === 0 ? (
          <div className="py-12 text-center text-xs text-gray-400">
            Henüz kaydedilmiş bir oturum bulunamadı.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-[11px] uppercase tracking-wider text-gray-400">
                  <th className="pb-3 font-bold">ID</th>
                  <th className="pb-3 font-bold">Katılımcı</th>
                  <th className="pb-3 font-bold">Test Adı</th>
                  <th className="pb-3 font-bold">Ort. Nabız</th>
                  <th className="pb-3 font-bold">Ort. GSR</th>
                  <th className="pb-3 font-bold">Yalan Skoru</th>
                  <th className="pb-3 font-bold">Notlar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {oturumlar.map((o) => (
                  <tr key={o.id} className="transition hover:bg-gray-50/50">
                    <td className="py-4 font-mono text-xs font-bold text-gray-400">
                      #{String(o.id).padStart(3, '0')}
                    </td>
                    <td className="py-4 font-semibold text-brand-navy">
                      <div className="flex items-center gap-2">
                        <User size={14} className="text-gray-400" />
                        <span>{katilimcilar[o.katilimci_id] || `Katılımcı #${o.katilimci_id}`}</span>
                      </div>
                    </td>
                    <td className="py-4 font-medium text-gray-700">
                      {o.test_adi || 'Poligraf Biyosinyal Oturumu'}
                    </td>
                    <td className="py-4 font-mono font-bold text-brand-navy">
                      {o.ortalama_bpm ? `${o.ortalama_bpm} BPM` : '--'}
                    </td>
                    <td className="py-4 font-mono font-bold text-brand-navy">
                      {o.ortalama_gsr ? `${o.ortalama_gsr} mV` : '--'}
                    </td>
                    <td className="py-4">
                      <span className="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-700 border border-emerald-200">
                        %{o.yalan_skoru ?? 0}
                      </span>
                    </td>
                    <td className="py-4 text-xs text-gray-500 max-w-xs truncate">
                      {o.notlar || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionHistory;