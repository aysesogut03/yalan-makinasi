import React, { useEffect, useMemo, useState } from 'react';
import { Search, UserPlus, X } from 'lucide-react';
import { participantService } from '../services/api';

export type Katilimci = {
  id: number;
  ad_soyad: string;
  yas: number;
  cinsiyet: string;
  test_sayisi: number;
  status?: 'Aktif' | 'Tamamlandı' | 'Beklemede';
  last?: string;
};

const badge: Record<string, string> = {
  Aktif: 'bg-emerald-50 text-emerald-600 ring-emerald-200',
  Tamamlandı: 'bg-blue-50 text-blue-600 ring-blue-200',
  Beklemede: 'bg-amber-50 text-amber-600 ring-amber-200',
};

export const Participants: React.FC = () => {
  const [katilimcilar, setKatilimcilar] = useState<Katilimci[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [q, setQ] = useState('');

  // Modal ve Form State'leri
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [adSoyad, setAdSoyad] = useState('');
  const [yas, setYas] = useState<number | ''>('');
  const [cinsiyet, setCinsiyet] = useState('Erkek');
  const [submitting, setSubmitting] = useState(false);

  // 1. Backend API'den Katılımcı Verilerini Çekme
  const fetchKatilimcilar = () => {
    setLoading(true);
    participantService
      .getAll()
      .then((data) => {
        setKatilimcilar(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Katılımcılar çekilirken hata:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchKatilimcilar();
  }, []);

  // 2. Yeni Katılımcı Ekleme Fonksiyonu
  const handleAddParticipant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adSoyad || !yas) return;

    setSubmitting(true);
    try {
      await participantService.create({
        ad_soyad: adSoyad,
        yas: Number(yas),
        cinsiyet: cinsiyet,
      });

      // Formu sıfırla ve modalı kapat
      setAdSoyad('');
      setYas('');
      setCinsiyet('Erkek');
      setIsModalOpen(false);

      // Listeyi backend'den yeniden güncelle
      fetchKatilimcilar();
    } catch (error) {
      console.error('Katılımcı eklenirken hata oluştu:', error);
    } finally {
      setSubmitting(false);
    }
  };

  // Arama Filtresi
  const rows = useMemo(() => {
    return katilimcilar.filter((r) =>
      r.ad_soyad.toLowerCase().includes(q.toLowerCase())
    );
  }, [q, katilimcilar]);

  return (
    <div className="max-w-6xl animate-fadeUp space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="mb-1 block text-xs font-bold uppercase tracking-[0.18em] text-brand-orange">
            ARAŞTIRMA ARAYÜZÜ / 02
          </span>
          <h1 className="text-3xl font-black tracking-tight text-brand-navy">Katılımcılar</h1>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-brand-navy px-4 py-3 text-xs font-bold text-white transition hover:bg-brand-cardNav"
        >
          <UserPlus size={14} /> Katılımcı ekle
        </button>
      </div>

      {/* Özet kutuları */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          ['Toplam katılımcı', katilimcilar.length],
          ['Aktif', katilimcilar.filter((r) => r.status === 'Aktif').length || katilimcilar.length],
          ['Tamamlanan oturum', katilimcilar.reduce((a, r) => a + (r.test_sayisi || 0), 0)],
        ].map(([l, v]) => (
          <div key={l as string} className="rounded-2xl border border-gray-100 bg-white p-5 shadow-card">
            <span className="block text-[11px] font-bold uppercase tracking-wider text-gray-400">{l}</span>
            <p className="mt-1 text-3xl font-black text-brand-navy">{v}</p>
          </div>
        ))}
      </div>

      {/* Tablo */}
      <div className="rounded-3xl border border-gray-100 bg-white p-6 shadow-card">
        <div className="relative mb-4 max-w-xs">
          <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Katılımcı ara..."
            className="w-full rounded-xl border border-gray-200 bg-gray-50/60 py-2.5 pl-10 pr-4 text-sm outline-none transition focus:border-brand-orange focus:bg-white focus:ring-4 focus:ring-brand-orange/10"
          />
        </div>

        <div className="overflow-x-auto">
          {loading ? (
            <div className="py-8 text-center text-xs text-gray-400">Veriler yükleniyor...</div>
          ) : (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-[11px] uppercase tracking-wider text-gray-400">
                  <th className="pb-3 font-bold">Katılımcı</th>
                  <th className="pb-3 font-bold">Oturum Sayısı</th>
                  <th className="pb-3 font-bold">Yaş / Cinsiyet</th>
                  <th className="pb-3 font-bold">Durum</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} className="border-t border-gray-100 transition hover:bg-gray-50/70">
                    <td className="py-3.5">
                      <div className="flex items-center gap-3">
                        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-brand-orange to-orange-400 text-[10px] font-black text-white">
                          K-{r.id}
                        </span>
                        <span className="font-bold text-brand-navy">{r.ad_soyad}</span>
                      </div>
                    </td>
                    <td className="py-3.5 tabular-nums text-gray-600">{r.test_sayisi}</td>
                    <td className="py-3.5 text-gray-500">{r.yas} / {r.cinsiyet}</td>
                    <td className="py-3.5">
                      <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold ring-1 ${badge[r.status || 'Aktif']}`}>
                        {r.status || 'Aktif'}
                      </span>
                    </td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-xs text-gray-400">
                      Sonuç bulunamadı.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* KATILIMCI EKLEME MODALI */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl animate-fadeIn">
            <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-4">
              <h2 className="text-xl font-bold text-brand-navy">Yeni Katılımcı Ekle</h2>
              <button
                onClick={() => setIsModalOpen(false)}
                className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleAddParticipant} className="space-y-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-1">
                  Ad Soyad
                </label>
                <input
                  type="text"
                  required
                  value={adSoyad}
                  onChange={(e) => setAdSoyad(e.target.value)}
                  placeholder="Örn: Ali Yılmaz"
                  className="w-full rounded-xl border border-gray-200 bg-gray-50/60 p-3 text-sm outline-none transition focus:border-brand-orange focus:bg-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-1">
                    Yaş
                  </label>
                  <input
                    type="number"
                    required
                    min={1}
                    max={120}
                    value={yas}
                    onChange={(e) => setYas(e.target.value ? Number(e.target.value) : '')}
                    placeholder="25"
                    className="w-full rounded-xl border border-gray-200 bg-gray-50/60 p-3 text-sm outline-none transition focus:border-brand-orange focus:bg-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-1">
                    Cinsiyet
                  </label>
                  <select
                    value={cinsiyet}
                    onChange={(e) => setCinsiyet(e.target.value)}
                    className="w-full rounded-xl border border-gray-200 bg-gray-50/60 p-3 text-sm outline-none transition focus:border-brand-orange focus:bg-white"
                  >
                    <option value="Erkek">Erkek</option>
                    <option value="Kadın">Kadın</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-xl border border-gray-200 px-4 py-2.5 text-xs font-bold text-gray-600 transition hover:bg-gray-50"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="rounded-xl bg-brand-orange px-5 py-2.5 text-xs font-bold text-white transition hover:bg-orange-600 disabled:opacity-50"
                >
                  {submitting ? 'Kaydediliyor...' : 'Kaydet'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Participants;