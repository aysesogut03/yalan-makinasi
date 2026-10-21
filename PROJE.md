# Yalan Makinesi: Yazılım Mimarisi

Bu belge yazılımın hangi katmanlardan oluştuğunu, her katmanı kimin yaptığını ve katmanların birbirine ne verdiğini anlatır. Projenin amacı, donanımı ve test yöntemi için *Yalan Makinesi Proje Planı*'na, parçalar için *Yalan Makinesi Sensör Listesi*'ne bakın.

- Durum: taslak, ekip onayı bekliyor
- Hazırlayan: C grubu, veri hattı
- Son güncelleme: 22 Ekim 2026

## 1. Ekip

| Grup | Kişi | Görev |
|---|---|---|
| Elektrik | 2 | Sensör devreleri, kablolama, güç beslemesi, kutu |
| A | 2 | Sinyal işleme ve arayüz |
| B | 1 | Test akışı ve puanlama, veri tabanı |
| C | 2 | Veri hattı ve görüntü işleme |

## 2. Katmanlar

```
┌──────────────────────── 7. Arayüz ─────────────────────────┐  gösterir, testi yönetir
├──────────────── 5. Test akışı ve puanlama ─────────────────┤  karar verir
├───── 4. Sinyal işleme ─────┬──── 3. Görüntü işleme ────────┤  anlamlı değer çıkarır
├───── 2. Veri hattı ────────┤                               │  veriyi alır, çevirir
├───── 1. ESP32 ve sensörler ┴──── Kamera ───────────────────┤  ölçer
└────────────────────────────────────────────────────────────┘
  6. Veri tabanı: yan katman, herkesin ürettiğini kaydeder
  sozlesme/: bütün katmanların bağlandığı ortak kayıt tipleri ve kurallar
```

| # | Katman | Sorumlu | Ne yapar |
|---|---|---|---|
| 1 | ESP32 ve sensörler | Elektrik + veri hattı | Sensörleri okur, ölçümleri satır satır bilgisayara gönderir |
| 2 | Veri hattı | C | ESP32 satırlarını, diğer katmanların kullanacağı zaman damgalı kayıtlara çevirir |
| 3 | Görüntü işleme | C | Kameradan göz kırpma, bakış, baş hareketi ve mimik değerlerini çıkarır |
| 4 | Sinyal işleme | A | Ham kayıtlardan terleme tepkisi, nabız, nefes hızı, nefes tutma ve kıpırdama hesaplar |
| 5 | Test akışı ve puanlama | B | Kalibrasyonu ve kart testini yürütür, tepkileri karşılaştırır, tahmini üretir |
| 6 | Veri tabanı | B | Her testi kaydeder, önceki testleri geri verir |
| 7 | Arayüz | A | Canlı grafikler, test yönetimi, "soru soruldu" işareti, sonuç ekranı |

**Katman kişi değil, sorumluluktur.** B iki katmana (5 ve 6), A da iki katmana (4 ve 7) bakar. Yine de her katmanın kodu ayrı durur: puanlama değişince veri tabanı kodu bozulmamalıdır.

### Test akışı ve puanlama (5. katman) ne yapar?

Testi yöneten ve "kişi hangi kartı seçti" kararını veren katmandır; projenin beyni. Üç işi vardır:

1. **Testi yönetir.** Başta kişinin sakin haldeki normal değerlerini kaydeder (kalibrasyon). Sonra kart testini yürütür: kartları karışık sırayla sorar, her birini en az 3 kez tekrarlar, sorular arasında 20–25 saniye bekler (Proje Planı, 5. bölüm).
2. **Puanlar.** Her sorudan sonraki birkaç saniyede değerlerin kişinin normalinden ne kadar saptığını hesaplar ve sinyalleri (terleme, nabız, nefes, göz kırpma) tek bir puanda birleştirir.
3. **Sonucu üretir.** Her kartın tekrarlarının ortalamasını alır ve en yüksek puanlı kartı tahmin olarak verir. Kişinin gerçekte seçtiği kart da kaydedilir; böylece cihazın isabet oranı ölçülür.

Ham sinyalle uğraşmaz: tepkiyi hesaplamak sinyal işlemenin işidir, puanlama yalnızca karşılaştırır ve karar verir. Sorudan sonraki birkaç saniyeye doğru bakabilmesi için soru anı ile ölçümlerin aynı saatte olması gerekir (4. bölüm, ortak saat). Kimden ne aldığı ve kime ne verdiği 3. bölümde.

## 3. Kim kimden ne alır, kime ne verir

| Katman | Alır | Verir |
|---|---|---|
| 1. ESP32 ve sensörler | Veri hattından: küçük ekran komutları | Veri hattına: protokol satırları |
| 2. Veri hattı | ESP32'den: protokol satırları. Puanlamadan: ekranda gösterilecek sonuç | Sinyal işlemeye ve veri tabanına: ölçüm, atım ve olay kayıtları. ESP32'ye: ekran komutları |
| 3. Görüntü işleme | Kameradan: görüntü | Puanlamaya ve veri tabanına (istenirse arayüze): zaman damgalı yüz değerleri |
| 4. Sinyal işleme | Veri hattından: ham kayıtlar | Puanlamaya, arayüze ve veri tabanına: işlenmiş değerler |
| 5. Test akışı ve puanlama | Sinyal işlemeden ve görüntü işlemeden: değerler. Arayüzden: soru zamanları, test komutları. Veri tabanından: önceki testler | Arayüze ve veri hattına: sonuç. Veri tabanına: test bilgileri ve sonuç |
| 6. Veri tabanı | Herkesten | Puanlamaya: önceki testler |
| 7. Arayüz | Sinyal işlemeden ve puanlamadan: değerler, sonuç | Puanlamaya: soru zamanları, test komutları |

```
Sensörler ─► ESP32 ─(USB)─► Veri hattı ─┬─► Sinyal işleme ─┬─► Arayüz: canlı grafik
                                        │                  └─► Puanlama ─► Sonuç ─► Arayüz, küçük ekran
                                        └─► Veri tabanı
Kamera ─► Görüntü işleme ─► Puanlama
Arayüz ─► soru zamanları ─► Puanlama
Bütün kayıtlar ve sonuç ─► Veri tabanı
```

## 4. Katmanlar arası kurallar

1. **Veri yukarı akar, komutlar aşağı iner.** Ölçümler sensörden arayüze doğru gider. Test başlatma ya da küçük ekrana yazma gibi komutlar ters yönde iner.
2. **Alt katman üst katmanı tanımaz.** Örneğin veri hattı, kayıtlarını kimin kullandığını bilmez; yalnızca kendisine verilen alıcılara teslim eder.
3. **Katmanlar birbirinin koduna değil, ortak sözleşmeye bağlanır** (5. bölüm). Bir katmanın içi değiştiğinde, sözleşme aynı kaldıkça diğerleri bozulmaz.
4. **Ortak saat.** Herkes zamanı bilgisayar saatine göre, Unix zamanı olarak yazar: 1 Ocak 1970'ten beri geçen saniye, ondalıklı. Python'da bu değeri `time.time()` verir. Kamera kareleri ve soru işaretleri de aynı saati kullanır; puanlama "soru sorulduktan sonraki birkaç saniyede ne oldu" diye ancak böyle bakabilir.
5. **Sözleşmedeki her değişiklik ekip onayıyla yapılır** ve sözleşmenin sürüm numarası artırılır.
6. **Test kayıtları kişisel veridir.** Git'e yüklenmez, ekip dışına çıkarılmaz (Proje Planı, 8. bölüm).

## 5. Ortak sözleşme ve bağımlılık enjeksiyonu

Bütün katmanlar SOLID ilkelerine ve bağımlılık enjeksiyonuna göre yazılır. Amaç, bir yerdeki değişikliğin diğer katmanları bozmamasıdır.

- **Ortak sözleşme (`sozlesme/`):** Katmanlar arasında taşınan kayıtların tipleri (`Olcum`, `Atim`, `Olay`...) ve küçük kurallardan oluşur. Örnek kural: "kayıt alan her nesnenin `al(kayit)` metodu vardır". Hiçbir katman başka bir katmanın sınıflarını doğrudan kullanmaz; yalnızca `sozlesme/`'yi kullanır.
- **Bağımlılık enjeksiyonu:** Bir katman ihtiyaç duyduğu parçayı kendisi oluşturmaz, parça ona dışarıdan verilir. Örnek: sinyal işleme kayıtları bir kural üzerinden alır. Kayıtlar veri hattından canlı da gelse, bir CSV kaydından da okunsa sinyal işlemenin kodu değişmez. Bu sayede A grubu donanım gelmeden, sahte ESP32'nin ürettiği kayıtlarla çalışmaya başlayabilir.
- **Kurulum noktası:** Parçaları oluşturup birbirine bağlayan tek yer, ana uygulamanın başlangıç dosyasıdır. Diğer dosyalar birbirini yalnızca sözleşme üzerinden tanır.

## 6. Örnek: bir sorunun yolculuğu

Soru: "Seçtiğin kart 7 mi?"

1. Kişinin parmağı terler, GSR sensörünün çıkış voltajı değişir. *(1. ESP32 ve sensörler)*
2. ESP32 voltajı okur, zamanını ekler, `S,...` satırı olarak gönderir. *(1)*
3. Veri hattı satırı `t=1792281600.123, gsr_mv=1475, ...` gibi bir ölçüm kaydına çevirir. *(2. Veri hattı)*
4. Sinyal işleme kaydı temizler ve "terleme tepkisi: +0,8" hesaplar. *(4. Sinyal işleme)*
5. Soru sorulduğu an operatör arayüzde butona basar: `soru=7, t=...`. *(7. Arayüz)*
6. Görüntü işleme aynı anda "iki kez göz kırptı" bilgisini çıkarır. *(3. Görüntü işleme)*
7. Puanlama, 7 sorulduktan sonraki tepkinin diğer kartlardan büyük olduğunu görür ve tahmini "7" olarak verir. *(5. Test akışı ve puanlama)*
8. Her şey veri tabanına kaydedilir; sonuç arayüzde ve küçük ekranda görünür. *(6, 7 ve 2)*

3. adımdaki zaman yanlış olursa 7. adımda tepki yanlış soruya yazılır. Ortak saat kuralı bu yüzden zorunludur.

## 7. Veri tabanına ne kaydedilir

Proje Planı'nın 6. bölümüne göre:

- Test edilen kişi ve kalibrasyon değerleri
- Sorular ve her sorunun sorulduğu an
- Sensörlerden ve kameradan gelen ölçümler
- Yazılımın verdiği sonuç ve kart testinde kişinin gerçekten seçtiği kart

Öneri olarak bunlara sinyal işlemenin hesapladığı değerler de eklenebilir.

Ham ölçümler de saklanır, yalnızca sonuçlar değil. Sinyal işleme yöntemi ileride değişirse eski testler yeni yöntemle yeniden hesaplanıp isabetin artıp artmadığına bakılabilir. İleride yapay zekâ denenirse bu kayıtlar eğitim verisi olur.

## 8. Klasör yapısı (öneri)

Her katman ortak git deposunda kendi klasöründe durur:

```
yalanmakinesi/
  PROJE.md            bu belge
  sozlesme/           ortak kayıt tipleri ve kurallar (herkes)
  veri_hatti/         2. Veri hattı (C)
  goruntu_isleme/     3. Görüntü işleme (C)
  sinyal_isleme/      4. Sinyal işleme (A)
  puanlama/           5. Test akışı ve puanlama (B)
  veri_tabani/        6. Veri tabanı (B)
  arayuz/             7. Arayüz (A)
```

- Her katman klasöründe, o katmanı anlatan bir `README.md` bulunur.
- Klasör adlarında tire yerine alt çizgi kullanılır, çünkü Python tireli klasörleri içe aktaramaz.

## 9. Teknik kararlar

| Konu | Karar | Durum |
|---|---|---|
| Bilgisayar tarafı dili | Python 3.10 ya da daha yenisi | Veri hattında kullanılıyor; ekip geneli için öneri |
| ESP32 dili | C++ (Arduino) | Öneri |
| ESP32 ile bilgisayar arası bağlantı | USB seri | Öneri; kesinleşmedi |
| Kod paylaşımı | Ortak git deposu | Kararlaştırıldı, açılacak |

## 10. Açık konular

- Arayüzün türü: masaüstü, web ya da mobil. Canlı veri yayınının tekniği buna bağlı.
- `sozlesme/` paketini kimin yöneteceği.
- Ana uygulamayı, yani kurulum noktasını kimin yazacağı. Arayüz en doğal aday.
- ESP32 kodunu kimin yazacağı: veri hattı mı, elektrikçiler mi, birlikte mi?
- Ham veriyi veri tabanına kimin yazacağı: veri hattı mı, B mi?
- Görüntü işleme değerlerinin kayıt biçimi.

## 11. Katman belgeleri

| Katman | Belge |
|---|---|
| 1. ESP32 ve sensörler, 2. Veri hattı | [veri_hatti/README.md](veri_hatti/README.md) |
| Diğerleri | Her grup kendi klasöründe yazacak |
