import React from 'react';
import { Bell, Radio } from 'lucide-react';
import type { BaglantiDurumu } from '../services/websocket';

interface HeaderBarProps {
  activeTab: string;
  durum: BaglantiDurumu;
}

const DURUMLAR: Record<BaglantiDurumu, { rozet: string; baglanti: string; renk: string; nokta: string; ping: string }> = {
  bagli: {
    rozet: 'CANLI VERİ',
    baglanti: 'Veri hattı · bağlı',
    renk: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    nokta: 'bg-emerald-500',
    ping: 'bg-emerald-400',
  },
  baglaniyor: {
    rozet: 'BAĞLANIYOR',
    baglanti: 'Veri hattı · bağlanıyor',
    renk: 'border-amber-200 bg-amber-50 text-amber-700',
    nokta: 'bg-amber-500',
    ping: 'bg-amber-400',
  },
  kapali: {
    rozet: 'BEKLEMEDE',
    baglanti: 'Veri hattı · bağlı değil',
    renk: 'border-gray-200 bg-white text-gray-500',
    nokta: 'bg-gray-400',
    ping: '',
  },
};

const PAGE_META: Record<string, { title: string; hint: string }> = {
  'genel-bakis': { title: 'Genel Bakış', hint: 'Deney paneli' },
  'katilimcilar': { title: 'Katılımcılar', hint: 'Kayıtlı katılımcı listesi' },
  'yeni-oturum': { title: 'Yeni Oturum', hint: 'Oturum hazırlığı' },
  'canli-olcum': { title: 'Canlı Sinyal / Ölçüm', hint: 'Gerçek zamanlı akış' },
  'oturum-ozeti': { title: 'Oturum Özeti', hint: 'Sonuç görünümü' },
  'oturum-gecmisi': { title: 'Oturum Geçmişi', hint: 'Önceki oturumlar' },
  'ayarlar': { title: 'Ayarlar', hint: 'Sistem tercihleri' },
};

export const HeaderBar: React.FC<HeaderBarProps> = ({ activeTab, durum }) => {
  const meta = PAGE_META[activeTab] ?? { title: activeTab, hint: '' };
  const d = DURUMLAR[durum];

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between gap-4 border-b border-gray-200/70 bg-[#F8F7F2]/80 px-6 py-3.5 backdrop-blur-md sm:px-8">
      {/* Sol: yol çubuğu + başlık */}
      <div className="min-w-0">
        <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
          <span>Sinyal Hattı</span>
          <span className="text-gray-300">/</span>
          <span className="truncate text-brand-orange">{meta.hint}</span>
        </div>
        <h2 className="truncate text-lg font-extrabold tracking-tight text-brand-navy">
          {meta.title}
        </h2>
      </div>

      {/* Sağ: durum rozetleri */}
      <div className="flex shrink-0 items-center gap-3">
        <div className={`hidden items-center gap-2 rounded-full border px-3 py-1.5 text-[11px] font-bold sm:flex ${d.renk}`}>
          <span className="relative flex h-2 w-2">
            {d.ping && (
              <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-70 ${d.ping}`} />
            )}
            <span className={`relative inline-flex h-2 w-2 rounded-full ${d.nokta}`} />
          </span>
          {d.rozet}
        </div>

        <div className="hidden items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1.5 text-[11px] font-semibold text-gray-500 md:flex">
          <Radio size={13} className={durum === 'bagli' ? 'text-emerald-500' : 'text-gray-400'} />
          {d.baglanti}
        </div>

        <button
          type="button"
          aria-label="Bildirimler"
          className="flex h-9 w-9 items-center justify-center rounded-full border border-gray-200 bg-white text-gray-500 transition hover:border-gray-300 hover:text-brand-navy"
        >
          <Bell size={16} />
        </button>

        <div className="flex items-center gap-2 rounded-full border border-gray-200 bg-white py-1 pl-1 pr-3">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-brand-orange to-orange-400 text-[10px] font-black text-white">
            K
          </span>
          <span className="text-[11px] font-bold text-brand-navy">K-104</span>
        </div>
      </div>
    </header>
  );
};