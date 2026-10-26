import React from 'react';
import { Activity, Users, FilePlus, PlayCircle, FileText, History, Settings } from 'lucide-react';
import type { BaglantiDurumu } from '../services/websocket';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  durum: BaglantiDurumu;
}

const ROZETLER: Record<BaglantiDurumu, { uzun: string; kisa: string; renk: string; nokta: string }> = {
  bagli: { uzun: 'CANLI VERİ', kisa: 'CANLI', renk: 'bg-emerald-400 text-emerald-950', nokta: 'bg-emerald-950/70' },
  baglaniyor: { uzun: 'BAĞLANIYOR', kisa: 'BAĞL', renk: 'bg-brand-yellow text-yellow-950', nokta: 'bg-yellow-950/70' },
  kapali: { uzun: 'BEKLEMEDE', kisa: 'BEKLE', renk: 'bg-slate-600 text-slate-100', nokta: 'bg-slate-300' },
};

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, durum }) => {
  const rozet = ROZETLER[durum];
  const menuItems = [
    { id: 'genel-bakis', label: 'Genel Bakış', icon: Activity },
    { id: 'katilimcilar', label: 'Katılımcılar', icon: Users },
    { id: 'yeni-oturum', label: 'Yeni Oturum', icon: FilePlus },
    { id: 'canli-olcum', label: 'Canlı Sinyal / Ölçüm', icon: PlayCircle },
    { id: 'oturum-ozeti', label: 'Oturum Özeti', icon: FileText },
    { id: 'oturum-gecmisi', label: 'Oturum Geçmişi', icon: History },
    { id: 'ayarlar', label: 'Ayarlar', icon: Settings },
  ];

  return (
    <aside className="sticky top-0 flex h-screen w-20 shrink-0 select-none flex-col justify-between overflow-hidden bg-gradient-to-b from-brand-navy via-[#111a30] to-[#0d1426] p-4 text-white lg:w-64 lg:p-6">
      {/* arka plan ışıması */}
      <div className="pointer-events-none absolute -left-20 -top-20 h-56 w-56 rounded-full bg-brand-orange/15 blur-3xl" />

      <div className="relative">
        {/* Logo */}
        <div className="mb-8 flex items-center justify-center gap-3 lg:justify-start">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-orange to-orange-400 text-lg font-bold text-white shadow-glow">
            ~
          </div>
          <div className="hidden lg:block">
            <h1 className="text-sm font-bold leading-tight text-white">Sinyal Hattı</h1>
            <p className="text-[11px] text-slate-400">Biyosinyal deney paneli</p>
          </div>
        </div>

        <p className="mb-3 hidden px-2 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500 lg:block">
          Menü
        </p>

        {/* Menü */}
        <nav className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                title={item.label}
                className={`group relative flex w-full items-center justify-center gap-3 rounded-xl px-3 py-3 text-xs font-semibold transition-all lg:justify-start lg:px-4 ${
                  isActive
                    ? 'bg-white/10 text-white shadow-inner ring-1 ring-white/10'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white'
                }`}
              >
                {isActive && (
                  <span className="absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-full bg-brand-orange shadow-[0_0_12px_rgba(238,108,77,0.9)]" />
                )}
                <Icon
                  size={18}
                  className={`shrink-0 transition ${
                    isActive ? 'text-brand-orange' : 'group-hover:text-slate-200'
                  }`}
                />
                <span className="hidden truncate lg:inline">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Alt Rozet */}
      <div className="relative border-t border-white/10 pt-5 text-xs text-slate-400">
        <div className="mb-3 flex justify-center lg:justify-start">
          <span className={`inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[10px] font-extrabold uppercase tracking-wider ${rozet.renk}`}>
            <span className={`h-1.5 w-1.5 rounded-full ${rozet.nokta}`} />
            <span className="hidden lg:inline">{rozet.uzun}</span>
            <span className="lg:hidden">{rozet.kisa}</span>
          </span>
        </div>
        <p className="hidden text-[11px] leading-relaxed text-slate-400 lg:block">
          Ölçüm verisi ESP32'den veri hattı üzerinden canlı gelir. Araştırma prototipi.
        </p>
      </div>
    </aside>
  );
};