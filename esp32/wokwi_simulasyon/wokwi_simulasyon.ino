// WOKWI SİMÜLASYONU: Elektrikçilerin devresi (ESP32, ekran, 3 düğme).
// Seri porta veri hattının protokolünü (v1) yazar: veri_hatti/README.md, 4. bölüm.
// Gerçek kart gelince yalnızca düğme okumaları sensör okumalarıyla değişir;
// satırları yazan kısım (VERİ HATTI PROTOKOLÜ) aynı kalır.

#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>

// --- EKRAN VE PİN TANIMLAMALARI ---
#define TFT_CS   5
#define TFT_DC   2
#define TFT_RST  4

// Wokwi Potansiyometre Pinleri
#define GSR_PIN    34 // 1. Pot (Stres)
#define BREATH_PIN 35 // 2. Pot (Nefes hızı, dakikada 6-30)
#define BPM_PIN    32 // 3. Pot (Nabız)

// --- VERİ HATTI PROTOKOLÜ (v1) AYARLARI ---
#define OLCUM_HZ   50       // Saniyedeki ölçüm (S satırı) sayısı
#define IVME_1G    16384.0  // MPU6050, ±2 g aralığında 1 g
#define GYRO_1DPS  131.0    // MPU6050, ±250 °/s aralığında 1 °/s
#define TABAN_EGIM 8.0      // Karına bantlı sensörün duruştaki eğimi (derece)
#define NEFES_EGIM 1.5      // Bir nefeste eğimin ne kadar değiştiği (derece)

// --- EKRAN YENİLEME ARALIKLARI ---
// Ekrana yazı çizmek yavaştır (bir kez ~170 ms). Her döngüde çizilirse ESP32
// saniyede 50 yerine 5 ölçüm gönderebilir; bu yüzden ekran daha seyrek yenilenir.
#define EKRAN_ARALIGI_MS 300 // Yazılar ve barlar: değer değişince, en sık bu aralıkla
#define DALGA_ARALIGI_MS 100 // Solunum dalgasına bu aralıkla bir nokta eklenir

Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);

// --- ÇİZİM VE HESAPLAMA DEĞİŞKENLERİ ---
int xPos = 0;
int prevBreathY = 55;

unsigned long startTime = 0;
bool isCalibrated = false;
int baseBpm = 0;
int baseGsr = 0;

// --- PROTOKOL DEĞİŞKENLERİ ---
unsigned long seq = 0;        // Her satırda 1 artan sıra numarası
unsigned long sonAtimMs = 0;  // Son kalp atımının zamanı
unsigned long sonDonguMs = 0; // Bir önceki döngünün zamanı
float nefesFazi = 0;          // Nefes dalgasının neresindeyiz (radyan)

// --- EKRAN YENİLEME DEĞİŞKENLERİ ---
int sonCizilenBpm = -1;        // Ekranda en son yazılan nabız
int sonCizilenGsr = -1;        // Ekranda en son yazılan stres yüzdesi
unsigned long sonEkranMs = 0;  // Yazıların en son çizildiği an
unsigned long sonDalgaMs = 0;  // Dalgaya en son nokta eklenen an

// --- VERİ HATTI PROTOKOLÜ: SATIR GÖNDERME ---
void bilgiGonder() {
  Serial.printf("I,%lu,%lu,v=1,hz=%d,acc=2,gyro=250\n", seq++, millis(), OLCUM_HZ);
}

void olcumGonder(int gsrMv, int nefesDk) {
  // Gerçek kartta ivme ve dönüş MPU6050'den okunur; burada nefes dalgasından hesaplanır
  float egim = radians(TABAN_EGIM + NEFES_EGIM * sin(nefesFazi));
  float egimHizi = NEFES_EGIM * 2 * PI * (nefesDk / 60.0) * cos(nefesFazi);
  int ax = round(sin(egim) * IVME_1G);
  int az = round(cos(egim) * IVME_1G);
  int gy = round(egimHizi * GYRO_1DPS);
  Serial.printf("S,%lu,%lu,%d,%d,0,%d,0,%d,0\n", seq++, millis(), gsrMv, ax, az, gy);
}

void atimlariGonder(int bpm) {
  // Gerçek kartta atım nabız sensöründen yakalanır; burada düğmedeki hızla üretilir
  unsigned long aralik = 60000UL / bpm;
  unsigned long simdi = millis();
  if (simdi - sonAtimMs > 2 * aralik) sonAtimMs = simdi - aralik;
  while (simdi - sonAtimMs >= aralik) {
    sonAtimMs += aralik;
    Serial.printf("B,%lu,%lu\n", seq++, sonAtimMs);
  }
}

void donguyuBekle(unsigned long donguBasi) {
  // Döngü 20 ms'de bir döner (saniyede 50 ölçüm); çizim süresi de buna dahildir
  while (millis() - donguBasi < 1000 / OLCUM_HZ) delay(1);
}

void setup() {
  Serial.begin(115200);

  // --- EKRAN BAŞLATMA ---
  tft.begin();
  tft.setRotation(1); 
  tft.fillScreen(ILI9341_BLACK);
  
  // --- STATİK ARAYÜZ ÇİZİMİ ---
  tft.setTextColor(ILI9341_WHITE);
  tft.setTextSize(2);
  
  tft.drawLine(0, 105, 320, 105, ILI9341_WHITE); // Dalga ayırıcı çizgi
  
  tft.setCursor(10, 115);
  tft.print("NABIZ:");
  tft.drawRect(10, 135, 300, 20, ILI9341_WHITE); 
  
  tft.setCursor(10, 165);
  tft.print("STRES:"); 
  tft.drawRect(10, 185, 300, 20, ILI9341_WHITE); 

  startTime = millis();
  sonDonguMs = startTime;
  bilgiGonder();
}

void loop() {
  unsigned long simdi = millis();

  // --- 1. SENSÖR (POTANSİYOMETRE) OKUMALARI ---
  int gsrValue = analogRead(GSR_PIN);
  int breathValue = analogRead(BREATH_PIN);
  int bpmValue = analogRead(BPM_PIN);

  // Değerleri anlamlı verilere dönüştürme (Haritalama)
  int currentGsrPercent = map(gsrValue, 0, 4095, 0, 100);
  int currentBpm = map(bpmValue, 0, 4095, 60, 180);
  int currentNefesDk = map(breathValue, 0, 4095, 6, 30);
  int gsrMv = map(gsrValue, 0, 4095, 0, 3300); // Gerçek kartta: analogReadMilliVolts(GSR_PIN)

  // Nefes dalgası: düğme hızı ayarlar, karın bu hızla iner kalkar
  nefesFazi += 2 * PI * (currentNefesDk / 60.0) * ((simdi - sonDonguMs) / 1000.0);
  if (nefesFazi > 2 * PI) nefesFazi -= 2 * PI;
  sonDonguMs = simdi;
  int breathY = 52 - (int)(40 * sin(nefesFazi));

  // --- VERİ HATTINA GÖNDERİM (kalibrasyon sırasında da sürer) ---
  olcumGonder(gsrMv, currentNefesDk);
  atimlariGonder(currentBpm);

  // Sınırlandırmalar (Ekrana taşmamaları için)
  if(breathY > 95) breathY = 95;
  if(breathY < 10) breathY = 10;

  // --- 2. KALİBRASYON AŞAMASI (İlk 5 Saniye) ---
  if (!isCalibrated) {
    if (millis() - startTime < 5000) {
      tft.setTextColor(ILI9341_YELLOW, ILI9341_BLACK);
      tft.setTextSize(3);
      tft.setCursor(30, 40);
      tft.print("KALIBRASYON...");
      
      baseBpm = currentBpm;
      baseGsr = currentGsrPercent;
      delay(50);
      return; 
    } else {
      isCalibrated = true;
      tft.fillRect(0, 30, 320, 50, ILI9341_BLACK); // Yazıyı sil
    }
  }

  // --- 3. SOLUNUM DALGASI ÇİZİMİ (100 ms'de bir nokta) ---
  if (simdi - sonDalgaMs >= DALGA_ARALIGI_MS) {
    sonDalgaMs = simdi;
    tft.drawLine(xPos + 1, 0, xPos + 1, 104, ILI9341_BLACK);
    tft.drawLine(xPos + 2, 0, xPos + 2, 104, ILI9341_BLACK);
    tft.drawLine(xPos + 3, 0, xPos + 3, 104, ILI9341_BLACK);

    if (xPos == 0) {
      tft.drawPixel(xPos, breathY, ILI9341_GREEN);
    } else {
      tft.drawLine(xPos - 1, prevBreathY, xPos, breathY, ILI9341_GREEN);
    }
    prevBreathY = breathY;

    xPos += 2;
    if (xPos >= 319) xPos = 0;
  }

  // Yazılar ve barlar yalnızca değer değişince, en sık 300 ms'de bir yeniden çizilir
  bool degisti = currentBpm != sonCizilenBpm || currentGsrPercent != sonCizilenGsr;
  if (!degisti || simdi - sonEkranMs < EKRAN_ARALIGI_MS) {
    donguyuBekle(simdi);
    return;
  }
  sonCizilenBpm = currentBpm;
  sonCizilenGsr = currentGsrPercent;
  sonEkranMs = simdi;

  // --- 4. YALAN TESPİT ALGORİTMASI ---
  uint16_t stresColor = ILI9341_GREEN; 
  String durumText = "NORMAL   "; 
  int stresBarLength = map(currentGsrPercent, 0, 100, 0, 296);

  if (currentBpm > (baseBpm * 1.20) || currentGsrPercent > (baseGsr + 25)) {
    stresColor = ILI9341_RED;   
    durumText = "YALAN !!!";
    stresBarLength = 296;       
  } 
  else if (currentBpm > (baseBpm * 1.10) || currentGsrPercent > (baseGsr + 10)) {
    stresColor = ILI9341_YELLOW; 
    durumText = "YUKSEK   ";
  } 

  // Durum Metnini Ekrana Yazdır
  tft.setTextSize(2);
  tft.setTextColor(stresColor, ILI9341_BLACK);
  tft.setCursor(95, 165); 
  tft.print(durumText);

  // --- 5. BAR ÇİZİMLERİ ---
  int bpmBarLength = map(currentBpm, 60, 180, 0, 296);
  if (bpmBarLength > 296) bpmBarLength = 296;
  if (bpmBarLength < 0) bpmBarLength = 0;

  // Nabız Barı
  tft.fillRect(12, 137, bpmBarLength, 16, ILI9341_CYAN);
  tft.fillRect(12 + bpmBarLength, 137, 296 - bpmBarLength, 16, ILI9341_BLACK); 

  // Stres Barı
  tft.fillRect(12, 187, stresBarLength, 16, stresColor);
  tft.fillRect(12 + stresBarLength, 187, 296 - stresBarLength, 16, ILI9341_BLACK); 

  // --- 6. SAYISAL VERİLER ---
  tft.setTextColor(ILI9341_WHITE, ILI9341_BLACK); 
  tft.setCursor(10, 215);
  
  tft.print("BPM:");
  tft.print(currentBpm);
  tft.print("("); tft.print(baseBpm); tft.print(")  "); 
  
  tft.print("GSR:%");
  tft.print(currentGsrPercent);
  tft.print("    "); 

  // --- 7. DÖNGÜ HIZI ---
  donguyuBekle(simdi);
}