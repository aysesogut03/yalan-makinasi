# Arayüz Katmanı (7. Katman) — Sinyal Hattı Operatör Paneli

Bu belge, **Yalan Makinesi (Biyosinyal Analiz Sistemi)** projesinin **7. Katmanı olan Arayüz (A Grubu)** bileşenini, mimarisini, veri akışını ve kurulum adımlarını açıklar.

---

## 1. Genel Bakış ve Sorumluluklar

Arayüz katmanı, sistemin operatör tarafından yönetildiği ve canlı biyosinyal ölçümlerinin anlık olarak izlendiği React + TypeScript + Vite tabanlı web paneller topluluğudur.

### Temel Sorumluluklar:
* **Canlı Biyosinyal İzleme:** GSR (cilt iletkenliği), Nabız (BPM) ve Solunum frekanslarını `uPlot` zaman çizgisi grafiğiyle 50 Hz/1 Hz periyotlarında canlı görselleştirme.
* **Test ve Oturum Yönetimi:** Katılımcı kayıtları, kalibrasyon süreçleri ve kart testi/soru akışlarının operatör tarafından yönlendirilmesi.
* **Veri Hattı Entegrasyonu:** C Grubu'nun sunduğu `sozlesme/` kurallarına uygun WebSocket sunucularına (`ws://localhost:8765` / `ws://localhost:8000`) baglanarak ölçüm ve atım kayıtlarını tüketme.

---

## 2. Klasör Yapısı

```text
yalan-makinasi-main/
├── arayuz/
│   ├── node_modules/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── HeaderBar.tsx       # Üst durum bilgi çubuğu
│   │   │   ├── LiveChart.tsx       # uPlot canlı sinyal zaman çizgisi
│   │   │   ├── SensorCard.tsx      # Metrik gösterge kartları
│   │   │   └── Sidebar.tsx         # Sol navigasyon menüsü
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx       # Genel Bakış ve hızlı deney paneli
│   │   │   ├── LiveMeasure.tsx     # Canlı Sinyal/Ölçüm, soru akışı ve kontrol alanı
│   │   │   ├── NewSession.tsx      # Yeni Oturum hazırlığı ve soru ekleme ekranı
│   │   │   └── Participants.tsx   # Katılımcı kayıt ve yönetimi
│   │   ├── services/
│   │   │   ├── sinyalisleme.ts     # Nabız/Solunum tahmin ve sinyal algoritmaları
│   │   │   └── websocket.ts        # C Grubu Veri Hattı WebSocket istemcisi
│   │   ├── App.tsx                 # Ana sayfa düzeni ve sekme yönetimi
│   │   ├── index.css               # Tailwind CSS & uPlot stil tanımları
│   │   ├── main.tsx                # Uygulama giriş noktası
│   │   └── vite-env.d.ts           # Vite ve TypeScript modül tanımları
│   ├── index.html                  # Ana HTML şablonu
│   ├── package.json                # Proje bağımlılıkları ve betikleri
│   ├── package-lock.json
│   ├── postcss.config.cjs          # PostCSS yapılandırması
│   ├── README.md                   # Arayüz belgelendirme dosyası
│   ├── tailwind.config.js          # Tailwind renk paleti ve tema ayarları
│   └── vite.config.ts              # Vite derleyici ayarları
└── veri_hatti/                     # C Grubu Veri Hattı ve Simülatör Katmanı
    ├── okuyucu/
    ├── simulator/
    ├── sozlesme/
    ├── tests/
    ├── kisanot.png
    ├── README.md
    └── requirements.txt
```

## 3. Kullanılan Teknolojiler

| Mimarî Katman | Teknoloji / Kütüphane | Kullanım Amacı |
|---|---|---|
| **Çerçeve (Framework)** | React 18 + TypeScript | Tip güvenliği yüksek bileşen mimarisi |
| **Derleyici (Build Tool)** | Vite 5 | Hızlı modül sıcak yükleme (HMR) |
| **Grafik Motoru** | `uPlot` | 50 Hz canlı veri akışında yüksek performanslı tuval (canvas) çizimi |
| **Stil / Tasarım** | Tailwind CSS 3 | Orijinal tasarıma birebir uyumlu UI kartları ve renk paletleri |
| **İkonlar** | `lucide-react` | Menü ve durum vektör göstergeleri |
| **İletişim Protocolü** | WebSocket (WS API) | Veri Hattı (2. Katman) ile anlık çift yönlü veri transferi |

---

## 4. Veri Akışı ve Sözleşme Uyumluğu (`sozlesme/`)

Arayüz katmanı, **SOLID** ilkelerine ve katman sözleşmesine sıkı sıkıya bağlıdır:

```
[ ESP32 / Simülatör ] ──► [ Veri Hattı (Python WS) ] ──(JSON)──► [ src/services/websocket.ts ]
                                                                             │
                                                                             ▼
[ uPlot Canlı Grafik ] ◄── [ src/pages/LiveMeasure.tsx ] ◄── [ useOlcumStream() Hook ]
```

### WebSocket Veri Formatı (`OlcumData`):
```typescript
export interface OlcumData {
  timestamp: number;    // Unix zaman damgası (time.time())
  heartRate: number;    // Nabız (BPM)
  gsr: number;          // Deri İletkenliği (mV)
  respiration: number;  // Solunum hızı (nefes/dk)
  temperature?: number; // Cilt Sıcaklığı (°C)
  movement?: number;    // Kıpırdama / İvme (g)
}
```

---

## 5. Kurulum ve Çalıştırma Adımları

VS Code terminalinde projenin iç `arayuz` klasöründe olduğunuza emin olun:

```powershell
# 1. Arayüz klasörüne geçiş yapın
cd yalan-makinasi-main\arayuz

# 2. Gerekli paketleri ve bağımlılıkları yükleyin
npm install

# 3. Geliştirici sunucusunu (Dev Server) başlatın
npm run dev
```

Başarılı kurulumun ardından tarayıcınızda **`http://localhost:5173`** adresine giderek Arayüz Paneline erişebilirsiniz.

---

## 6. Otomatik Simülasyon (Fallback) Modu

Veri Hattı (`veri_hatti`) veya ESP32 donanımı henüz aktif değilse, Arayüz katmanı kilitlenmez. `LiveMeasure.tsx` bileşeni otomatik olarak **Demo / Simülasyon Verisi** moduna geçerek test imkânı sunar. C Grubu Python sunucusu ayağa kalktığında sistem otomatik olarak canlı veriye bağlanır.