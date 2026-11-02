import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { HeaderBar } from './components/HeaderBar';
import { Dashboard } from './pages/Dashboard';
import { Participants } from './pages/Participants';
import { NewSession } from './pages/NewSession';
import { LiveMeasure } from './pages/LiveMeasure';
import { SessionHistory } from './pages/SessionHistory';
import { SessionSummary } from './pages/SessionSummary';
import { Login } from './pages/Login';
import { authService } from './services/api';
import type { BaglantiDurumu } from './services/websocket';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('genel-bakis');
  const [durum, setDurum] = useState<BaglantiDurumu>('kapali');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  // Sayfa ilk yüklendiğinde token kontrolü
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    } else {
      setIsAuthenticated(false);
    }
  }, []);

  // Çıkış Yap Fonksiyonu
  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
  };

  // Canlı ölçüm ekranına güvenli geçiş fonksiyonu
  const handleGoToMeasure = () => {
    setActiveTab('canli-olcum');
  };

  // Yeni oturum ekranına güvenli geçiş fonksiyonu
  const handleGoToNewSession = () => {
    setActiveTab('yeni-oturum');
  };

  // Oturum kapalıysa doğrudan Giriş Ekranını göster
  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  // Oturum açıksa Ana Uygulama Arayüzünü göster
  return (
    <div className="flex min-h-screen bg-[#F8F7F2]">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} durum={durum} />

      <div className="flex min-w-0 flex-1 flex-col">
        {/* HeaderBar'a onLogout fonksiyonunu gönderiyoruz */}
        <HeaderBar activeTab={activeTab} durum={durum} onLogout={handleLogout} />

        <main className="flex-1 overflow-y-auto p-6 sm:p-8">
          {activeTab === 'genel-bakis' && (
            <Dashboard
              onGoToMeasure={handleGoToMeasure}
              onGoToNewSession={handleGoToNewSession}
            />
          )}

          {activeTab === 'katilimcilar' && <Participants />}

          {activeTab === 'yeni-oturum' && (
            <NewSession onGoToMeasure={handleGoToMeasure} />
          )}

          {activeTab === 'canli-olcum' && (
            <LiveMeasure onDurum={setDurum} />
          )}

          {activeTab === 'oturum-ozeti' && <SessionSummary />}

          {activeTab === 'oturum-gecmisi' && <SessionHistory />}

          {activeTab === 'ayarlar' && (
            <div className="mx-auto mt-12 max-w-xl animate-fadeUp rounded-3xl border border-gray-100 bg-white p-12 text-center shadow-card">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-orange-50 text-xl text-brand-orange">
                ⏳
              </div>
              <h3 className="mb-1 text-base font-bold text-brand-navy">Sayfa Hazırlanıyor</h3>
              <p className="text-xs leading-relaxed text-gray-400">
                Ayarlar sekmesi entegre edilmektedir.
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;