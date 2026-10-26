import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { HeaderBar } from './components/HeaderBar';
import { Dashboard } from './pages/Dashboard';
import { Participants } from './pages/Participants';
import { NewSession } from './pages/NewSession';
import { LiveMeasure } from './pages/LiveMeasure';
import type { BaglantiDurumu } from './services/websocket';

export function App() {
  const [activeTab, setActiveTab] = useState('genel-bakis');
  const [durum, setDurum] = useState<BaglantiDurumu>('kapali');

  return (
    <div className="flex min-h-screen">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} durum={durum} />

      <div className="flex min-w-0 flex-1 flex-col">
        <HeaderBar activeTab={activeTab} durum={durum} />

        <main className="flex-1 overflow-y-auto p-6 sm:p-8">
          {activeTab === 'genel-bakis' && (
            <Dashboard
              onGoToMeasure={() => setActiveTab('canli-olcum')}
              onGoToNewSession={() => setActiveTab('yeni-oturum')}
            />
          )}
          {activeTab === 'katilimcilar' && <Participants />}
          {activeTab === 'yeni-oturum' && (
            <NewSession onGoToMeasure={() => setActiveTab('canli-olcum')} />
          )}
          {activeTab === 'canli-olcum' && <LiveMeasure onDurum={setDurum} />}

          {['oturum-ozeti', 'oturum-gecmisi', 'ayarlar'].includes(activeTab) && (
            <div className="mx-auto mt-12 max-w-xl animate-fadeUp rounded-3xl border border-gray-100 bg-white p-12 text-center shadow-card">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-50 text-xl text-brand-orange">
                ⏳
              </div>
              <h3 className="mb-1 text-base font-bold text-brand-navy">Sayfa Hazırlanıyor</h3>
              <p className="text-xs leading-relaxed text-gray-400">
                {activeTab} sekmesi C Grubu veri hattı kontratı ile entegre edilmektedir.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;