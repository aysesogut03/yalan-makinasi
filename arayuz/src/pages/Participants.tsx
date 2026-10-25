import React, { useMemo, useState } from 'react';
import { Search, UserPlus } from 'lucide-react';

type Row = { code: string; sessions: number; last: string; status: 'Aktif' | 'Tamamlandı' | 'Beklemede' };

const ROWS: Row[] = [
  { code: 'K-101', sessions: 2, last: '12 Eki 2026', status: 'Tamamlandı' },
  { code: 'K-102', sessions: 1, last: '14 Eki 2026', status: 'Tamamlandı' },
  { code: 'K-103', sessions: 0, last: '-', status: 'Beklemede' },
  { code: 'K-104', sessions: 0, last: '-', status: 'Aktif' },
];

const badge: Record<Row['status'], string> = {
  Aktif: 'bg-emerald-50 text-emerald-600 ring-emerald-200',
  Tamamlandı: 'bg-blue-50 text-blue-600 ring-blue-200',
  Beklemede: 'bg-amber-50 text-amber-600 ring-amber-200',
};

export const Participants: React.FC = () => {
  const [q, setQ] = useState('');
  const rows = useMemo(() => ROWS.filter((r) => r.code.toLowerCase().includes(q.toLowerCase())), [q]);

  return (
    <div className="max-w-6xl animate-fadeUp space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="mb-1 block text-xs font-bold uppercase tracking-[0.18em] text-brand-orange">
            ARAŞTIRMA ARAYÜZÜ / 02
          </span>
          <h1 className="text-3xl font-black tracking-tight text-brand-navy">Katılımcılar</h1>
        </div>
        <button className="flex items-center gap-2 rounded-xl bg-brand-navy px-4 py-3 text-xs font-bold text-white transition hover:bg-brand-cardNav">
          <UserPlus size={14} /> Katılımcı ekle
        </button>
      </div>

      {/* Özet kutuları */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          ['Toplam katılımcı', ROWS.length],
          ['Aktif', ROWS.filter((r) => r.status === 'Aktif').length],
          ['Tamamlanan oturum', ROWS.reduce((a, r) => a + r.sessions, 0)],
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
            placeholder="Kod ara..."
            className="w-full rounded-xl border border-gray-200 bg-gray-50/60 py-2.5 pl-10 pr-4 text-sm outline-none transition focus:border-brand-orange focus:bg-white focus:ring-4 focus:ring-brand-orange/10"
          />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-[11px] uppercase tracking-wider text-gray-400">
                <th className="pb-3 font-bold">Katılımcı</th>
                <th className="pb-3 font-bold">Oturum</th>
                <th className="pb-3 font-bold">Son ölçüm</th>
                <th className="pb-3 font-bold">Durum</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.code} className="border-t border-gray-100 transition hover:bg-gray-50/70">
                  <td className="py-3.5">
                    <div className="flex items-center gap-3">
                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-brand-orange to-orange-400 text-[10px] font-black text-white">
                        {r.code.slice(-2)}
                      </span>
                      <span className="font-bold text-brand-navy">{r.code}</span>
                    </div>
                  </td>
                  <td className="py-3.5 tabular-nums text-gray-600">{r.sessions}</td>
                  <td className="py-3.5 text-gray-500">{r.last}</td>
                  <td className="py-3.5">
                    <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold ring-1 ${badge[r.status]}`}>
                      {r.status}
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
        </div>
      </div>
    </div>
  );
};

export default Participants;