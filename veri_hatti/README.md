# Veri Hattı

Projenin 2. katmanı ([PROJE.md](../PROJE.md)). Sensör verisinin ESP32'den diğer katmanların kullanabileceği hale gelmesini sağlar. 1. katmanın (ESP32) bilgisayara ne gönderdiği de burada tanımlıdır.

- Sorumlu: C grubu
- Durum: prototip çalışıyor (sahte ESP32 → okuyucu → kayıt dosyaları); gerçek ESP32 bekleniyor
- Son güncelleme: 18 Ekim 2026

## 1. Görev

ESP32'den gelen satırları, diğer katmanların doğrudan kullanabileceği zaman damgalı kayıtlara çevirmek.

| Veri hattı şunları yapar | Veri hattı şunları yapmaz |
|---|---|
| ESP32'den veriyi okur ve düzenli biçime çevirir | Değerleri temizlemez, filtrelemez, eksik veriyi doldurmaz: bu sinyal işlemenin işi |
| Her ölçüme bilgisayar saatine göre zaman damgası ekler | Puanlama yapmaz |
| Kayıp ya da bozuk veriyi fark eder ve bildirir | Veri tabanını yönetmez |
| Kayıtları diğer katmanlara teslim eder ve dosyaya kaydeder | |
| Donanım yokken gerçek ESP32 gibi davranan sahte veri üretir | |

## 2. Genel görünüm

```
ESP32 ya da sahte ESP32 ──satırlar──► OKUYUCU ──kayıtlar──► sinyal işleme, veri tabanı, ...
       (4. bölüm)                     (3. bölüm)  (5. bölüm)
```

Burada birbirinden bağımsız iki program var:

- **Sahte ESP32** (`simulator/`): Gerçek ESP32 gelene kadar onun yerini tutar.
- **Okuyucu** (`okuyucu/`): Veri hattının asıl işini yapar.

İkisi ortak kod paylaşmaz; tek ortak noktaları 4. bölümdeki satır biçimidir. Gerçek ESP32 kodu C++ ile yazılacağı için okuyucuyla zaten kod paylaşamaz. Okuyucu yalnızca satırlara güvendiği için gerçek ESP32 geldiğinde okuyucuda hiçbir şey değişmez.

Diğer katmanlar da bizim kodumuza değil, 5. bölümdeki kayıt biçimine bağlıdır.

## 3. Okuyucunun katmanları

| # | Katman | Ne yapar | Kural | İlk sınıf |
|---|---|---|---|---|
| 1 | Bağlantı | Kablodan satırı alır | `SatirKaynagi` | `SeriKaynak`: pyserial ile hem gerçek porta hem `socket://` adresine bağlanır |
| 2 | Ayrıştırma | Satırı parçalarına ayırır, ESP32 mesajına çevirir. Bozuk satırı reddeder. | `Ayristirici` | `ProtokolV1Ayristirici` |
| 3 | Dönüştürme | ESP32 mesajını kayda çevirir: kayıp kontrolü, birim çevirme, bilgisayar saati | `Donusturucu` | `MesajDonusturucu`; yardımcıları `SiraTakipcisi`, `BirimCevirici`, `ZamanEslestirici` |
| 4 | Dağıtım | Kaydı teslim eder | `VeriAlici` (`sozlesme/` içinde) | `OturumKaydedici` (CSV), `KonsolAlici` (ekrana özet) |

Bunlara iki parça daha eşlik eder:

- **`VeriHatti`:** Dört katmanı sırayla çalıştırır.
- **`__main__.py`:** Parçaları oluşturup birbirine bağlayan kurulum noktasıdır.

Bir satırın katmanlardan geçişi:

```
1  "S,1042,20840,1475,-412,215,16120,-35,12,4"                    metin
2  OlcumMesaji(seq=1042, ms=20840, gsr=1475, ax=-412, ...)        ESP32'nin dili
3  Olcum(t=1792281600.123, gsr_mv=1475, ax_g=-0.02515, ...)       diğer katmanların dili
4  olcumler.csv dosyasına bir satır
```

Okuyucuda iki ayrı veri tipi ailesi vardır:

- **Mesajlar** (`OlcumMesaji`, `AtimMesaji`, `BilgiMesaji`, `HataMesaji`): ESP32'nin dili. Ham sayılar ve ESP32 zamanı. Yalnızca okuyucunun içinde kullanılır.
- **Kayıtlar** (`Olcum`, `Atim`, `Olay`, `CihazBilgisi`, `HamSatir`): Diğer katmanların dili. Birimli değerler ve bilgisayar saati. Diğer katmanlar da kullanacağı için `sozlesme/` paketinde durur.

Veri hattının yaptığı çeviri, tam olarak mesajdan kayda geçiştir.

**Zaman eşleştirme:** İlk satır geldiğinde ESP32 zamanı ile bilgisayar saati eşleştirilir. Sonraki her satır için `t = t0 + (esp_ms − ms0) / 1000` hesaplanır. Satırın geliş anı değil ESP32'nin kendi zamanı kullanılır, çünkü USB satırları gruplar halinde ve gecikmeyle getirir; ESP32'nin zamanı ise ölçümün gerçekten alındığı andır. ESP32 yeniden başlarsa (yeni bir `I` satırı gelirse ya da sıra numarası geri giderse) eşleştirme sıfırdan yapılır. ESP32 saatinin kayması 15 dakikalık bir testte birkaç on milisaniye mertebesinde kalır. Bu değer gerçek kartla ölçülecek; gerekirse yeni bir `ZamanEslestirici` yazılır.

**Okuyucunun verdiği diğer kararlar:**

- **`I` satırı gelmezse:** Okuyucu akışın ortasından bağlandıysa (ESP32 yeniden başlamadıysa) `I` satırı hiç gelmez. Bu durumda veri kaybolmasın diye protokolün varsayılan aralıklarıyla (±2 g, ±250 °/s) çevirmeye devam edilir ve `olaylar.csv`'ye bir kez `hata` olayı yazılır.
- **Bozuk satır:** Atılır ve nedeniyle birlikte `olaylar.csv`'ye `bozuk` olayı olarak yazılır. Bağlanma anında ilk satırın ortası yakalanırsa bir tane bozuk satır görülmesi normaldir.
- **Hata veren alıcı:** Bir alıcı hata verirse (örneğin başka bir grubun alıcısı) diğer alıcılar çalışmaya devam eder; test kaydı durmaz. Hata ekrana bir kez yazılır.
- **Ondalık basamaklar:** Zaman 3 (ms), ivme 5, dönüş hızı 4 basamağa yuvarlanır. Daha fazlası, sensörün en küçük adımından küçük olduğu için anlamsızdır.

**Bir şey değişince ne değişir:**

| Değişiklik | Değişen | Değişmeyen |
|---|---|---|
| Gerçek ESP32 geldi | Çalıştırırken verilen adres | Hiçbir kod |
| Kablosuz bağlantıya geçildi | Yeni bir kaynak sınıfı ve kurulum | Ayrıştırma, dönüştürme, dağıtım |
| A canlı veri istiyor | Yeni bir alıcı sınıfı ve kurulum | Geri kalan her şey |
| Protokol v2 | Yeni bir ayrıştırıcı ve sahte ESP32'nin `protokol.py`'si | Dönüştürme, dağıtım |
| CSV yerine başka bir dosya biçimi | `OturumKaydedici` | Geri kalan her şey |

## 4. ESP32 satırları (protokol v1)

### Bağlantı

| Durum | Bağlantı |
|---|---|
| Gerçek ESP32 | USB seri, 115200 baud, 8N1 |
| Sahte ESP32 | Aynı bilgisayarda TCP, adres `socket://127.0.0.1:7600` |

Okuyucu her iki durumda da aynı kodla bağlanır; değişen tek şey adrestir.

### Satır kuralları

- Her mesaj tek bir satırdır. Satır `\n` ile biter, yalnızca ASCII karakter kullanılır.
- Alanlar virgülle ayrılır, aralarına boşluk konmaz.
- ESP32'den gelen her mesaj `TÜR,seq,ms,...` biçimindedir:
  - `TÜR` tek bir harftir.
  - `seq` sıra numarasıdır. ESP32 açılınca 0'dan başlar ve bütün mesaj türleri aynı sayacı kullanır; her mesajda 1 artar. Sayıda bir boşluk varsa arada mesaj kaybolmuştur.
  - `ms`, ESP32 açıldığından beri geçen milisaniyedir.
- Kurala uymayan satırı okuyucu atar ve "bozuk satır" olarak kaydeder.

### ESP32'den bilgisayara giden mesajlar

| Tür | Ne zaman | Biçim | Örnek |
|---|---|---|---|
| `I` bilgi | Açılışta bir kez | `I,seq,ms,v=..,hz=..,acc=..,gyro=..` | `I,0,312,v=1,hz=50,acc=2,gyro=250` |
| `S` ölçüm | Saniyede `hz` kez | `S,seq,ms,gsr,ax,ay,az,gx,gy,gz` | `S,1042,20840,1475,-412,215,16120,-35,12,4` |
| `B` atım | Her kalp atımında | `B,seq,ms` | `B,1043,20851` |
| `E` hata | Bir sorun olunca | `E,seq,ms,KOD` | `E,1044,20860,MPU_YOK` |

**`I` alanları**

| Alan | Anlamı |
|---|---|
| `v` | Protokol sürümü |
| `hz` | Saniyedeki ölçüm sayısı |
| `acc` | İvmeölçerin ölçüm aralığı, ± g |
| `gyro` | Dönüş ölçerin ölçüm aralığı, ± derece/saniye |

`I` mesajı ESP32'nin yeniden başladığını da gösterir. Birçok ESP32 kartı, seri port açıldığında kendini yeniden başlatır. Okuyucu `I` mesajını görünce `seq` ve `ms` değerlerinin sıfırlandığını anlar.

**`S` alanları**

| Alan | Birim | Aralık | Açıklama |
|---|---|---|---|
| `gsr` | mV | 0–3300 | GSR modülünün çıkış voltajı. ESP32'nin kendi ADC kalibrasyonuyla okunur. |
| `ax`, `ay`, `az` | ham | −32768…32767 | MPU6050 ivme. ±2 g aralığında 16384 = 1 g. |
| `gx`, `gy`, `gz` | ham | −32768…32767 | MPU6050 dönüş hızı. ±250 °/s aralığında 131 = 1 °/s. |

`B` mesajındaki `ms` değeri, atımın gerçekleştiği andır. Gönderildiği an değildir, çünkü ESP32 atımı kesmeyle (interrupt) yakalar.

**`E` kodları**

| Kod | Anlamı |
|---|---|
| `MPU_YOK` | MPU6050 yanıt vermiyor |
| `NABIZ_YOK` | 2 saniyedir atım gelmedi; sensör yerinden çıkmış olabilir |

Gerektikçe yeni kodlar eklenir.

### Bilgisayardan ESP32'ye giden mesajlar

| Tür | Biçim | Örnek | Açıklama |
|---|---|---|---|
| `D` ekran | `D,satır,metin` | `D,0,Tahmin: 7` | Küçük ekranın `satır` numaralı satırına (0–7) `metin` yazılır. Metin en fazla 21 karakter olabilir ve yalnızca ASCII içerir; Türkçe karakter kullanılmaz. |

## 5. Diğer katmanlara verilen veri

### Kayıt: her test için bir klasör

Okuyucu her test için `kayitlar/` altında, testin başladığı tarih ve saatle adlandırılmış bir klasör açar. Örnek: `kayitlar/2026-10-18_14-30-05/`.

| Dosya | İçerik | Kim kullanır |
|---|---|---|
| `oturum.json` | Başlangıç zamanı, protokol sürümü, kaynak (gerçek ya da sahte ESP32), `hz`, GSR kalibrasyon değeri | Herkes |
| `olcumler.csv` | Bilgisayar saatine çevrilmiş ölçümler, birimleriyle | Sinyal işleme, veri tabanı |
| `atimlar.csv` | Her kalp atımının zamanı | Sinyal işleme, veri tabanı |
| `olaylar.csv` | Kayıp ve bozuk satırlar, hatalar, yeniden başlamalar, bağlantı kopmaları | Sinyal işleme: güvenilmez aralıkları ayıklamak için |
| `ham.log` | ESP32'den gelen her satır, olduğu gibi ve geliş zamanıyla | Veri hattı: testi yeniden oynatmak için |

**`olcumler.csv` sütunları**

| Sütun | Birim | Açıklama |
|---|---|---|
| `t` | s (Unix zamanı) | Ölçümün alındığı an, bilgisayar saatine göre |
| `seq` | — | ESP32 sıra numarası |
| `esp_ms` | ms | ESP32 zamanı |
| `gsr_mv` | mV | GSR çıkış voltajı |
| `ax_g`, `ay_g`, `az_g` | g | İvme |
| `gx_dps`, `gy_dps`, `gz_dps` | °/s | Dönüş hızı |

**`atimlar.csv` sütunları:** `t`, `seq`, `esp_ms`

**`olaylar.csv` sütunları:** `t`, `tur`, `ayrinti`. `tur` şunlardan biridir: `kayip`, `bozuk`, `hata`, `yeniden_baslama`, `baglanti`.

Örnek `olcumler.csv` satırı:

```
t,seq,esp_ms,gsr_mv,ax_g,ay_g,az_g,gx_dps,gy_dps,gz_dps
1792281600.123,1042,20840,1475,-0.02515,0.01312,0.98389,-0.2672,0.0916,0.0305
```

### Canlı akış

Testi canlı izleyen katmanlar (arayüz ve canlı sinyal işleme) aynı kayıtları canlı olarak da alır:

- Python'da `sozlesme/`'deki `VeriAlici` kuralıyla.
- Başka bir dilde ya da ayrı bir programda, CSV sütunlarıyla aynı adları taşıyan JSON mesajlarıyla. Her mesaj ayrıca hangi tür veri olduğunu gösteren bir `tur` alanı taşır.

```
{"tur": "olcum", "t": 1792281600.123, "seq": 1042, "esp_ms": 20840, "gsr_mv": 1475, "ax_g": -0.02515, ...}
{"tur": "atim",  "t": 1792281600.134, "seq": 1043, "esp_ms": 20851}
{"tur": "olay",  "t": 1792281600.200, "olay": "kayip", "ayrinti": "2 satır"}
```

Python alıcıları bugün de çalışır: alıcı `okuyucu/__main__.py`'deki `alicilar` listesine eklenir. JSON yayını henüz yazılmadı; tekniği, arayüzün türüne göre A grubuyla birlikte belirlenecek.

**Örnek alıcı (Python).** `VeriAlici` kuralına uymak için iki metot yeter: `al` ve `kapat`. Alıcı her türden kaydı alır, yalnızca ilgilendiklerini kullanır ve gerisini yok sayar:

```python
from sozlesme import Olcum

class GsrToplayici:
    def __init__(self):
        self.degerler = []

    def al(self, kayit):
        if isinstance(kayit, Olcum):        # yalnızca ölçümlerle ilgilen
            self.degerler.append((kayit.t, kayit.gsr_mv))

    def kapat(self):
        pass
```

`al` metodu uzun sürmemelidir, çünkü kayıtlar saniyede 50'den fazla kez gelir. Uzun bir işi (örneğin veri tabanına yazmayı) alıcı kendi içinde biriktirerek ya da ayrı bir iş parçacığında yapmalıdır.

### Birim çevirme

| Değer | Kim çevirir | Nasıl |
|---|---|---|
| İvme → g | Veri hattı | `ham / (32768 / acc)`. ±2 g için `ham / 16384`. |
| Dönüş → °/s | Veri hattı | ±250 °/s için `ham / 131` (MPU6050 veri sayfası) |
| GSR voltajı → mV | ESP32 | ESP32'nin kendi ADC kalibrasyonuyla |
| GSR mV → direnç ya da iletkenlik | Sinyal işleme | Seeed formülünden uyarlanacak. Formül 10 bit Arduino için yazılmış; gerçek sensörle doğrulanmalı. Seeed formülüne göre terleme arttıkça okunan değer düşer; bu da doğrulanacak. Kalibrasyon değeri `oturum.json` dosyasında. |

## 6. Sahte ESP32

Gerçek ESP32 gelene kadar onun yerini tutar. 4. bölümdeki satırları gerçek zamanda üretir: açılışta bir `I`, her 20 ms'de bir `S`, her kalp atımında bir `B` satırı. Sayılar basit dalgalardan gelir: GSR yavaşça iner çıkar, ivme nefesle salınır, nabız dakikada yaklaşık 75'tir. Stres tepkisi taklit edilmez.

Her yeni bağlantıda sıfırdan başlar. Birçok gerçek ESP32 kartı da seri port açılınca yeniden başladığı için bu davranış bilerek seçildi.

Akış kısaca şöyle: `sensorler` ölçer → `cihaz` zamanını belirler → `protokol` satırı yazar → `tcp` gönderir. `__main__` hepsini birbirine bağlar.

| Dosya | Cihazdaki karşılığı | Ne yapar |
|---|---|---|
| `simulator/kurallar.py` | Parça şartnamesi | Parçaların uyması gereken kurallar. Çalışan kod içermez. |
| `simulator/sensorler.py` | Sensörler | GSR, ivmeölçer ve nabız için sayı üretir |
| `simulator/protokol.py` | Mesaj yazma kuralı | Sayıları protokol satırlarına çevirir |
| `simulator/cihaz.py` | ESP32'nin beyni | Hangi satırın ne zaman gönderileceğine karar verir (Arduino'daki setup/loop yapısı) |
| `simulator/tcp.py` | USB kablosu | Satırları okuyucuya iletir |
| `simulator/__main__.py` | Montaj | Parçaları oluşturup bağlar ve çalıştırır |
| `tests/test_simulator.py` | Kalite kontrol | Satırların protokole uyduğunu denetler |

## 7. Klasör yapısı ve çalıştırma

```
veri_hatti/
├── okuyucu/            VERİ HATTININ ASIL İŞİ: ESP32 satırlarını diğer katmanların anlayacağı kayıtlara çevirir
│   ├── baglanti/
│   │   └── seri_kaynak.py         kablodan (şimdilik sahte ESP32'den) gelen satırları alır
│   ├── ayristirma/
│   │   └── protokol_v1.py         satırı parçalarına ayırır, kurala uyuyor mu diye kontrol eder
│   ├── donusturme/
│   │   ├── birim_cevirici.py      ham sayıları birime çevirir (16384 → 1 g)
│   │   ├── zaman_eslestirici.py   ESP32'nin saatini bilgisayarın saatine çevirir
│   │   ├── sira_takipcisi.py      kaybolan satır var mı, ESP32 yeniden mi başladı, ona bakar
│   │   └── donusturucu.py         bu üçünü kullanarak asıl çeviriyi yapar
│   ├── dagitim/
│   │   ├── oturum_kaydedici.py    sonucu kayitlar/ klasöründeki dosyalara yazar
│   │   └── konsol_alici.py        çalışırken ekrana saniyede bir özet basar
│   ├── mesajlar.py      ESP32'nin dili: ayrıştırmanın çıktısı, dönüştürmenin girdisi
│   ├── kurallar.py      alt katmanların uyması gereken kurallar
│   ├── hat.py           satırı sırayla dört alt katmandan geçiren "bant"
│   └── __main__.py      başlangıç dosyası: parçaları kurar ve çalıştırır
│
├── simulator/          SAHTE ESP32: kart gelene kadar onun yerine veri üretir
│   ├── sensorler.py     sahte GSR, ivmeölçer ve nabız değerleri üretir
│   ├── cihaz.py         ESP32'nin "beyni": hangi satırı ne zaman göndereceğine karar verir
│   ├── protokol.py      sayıları "S,1042,20840,..." gibi satırlara yazar
│   ├── tcp.py           USB kablosunun yerini tutar: satırları okuyucuya iletir
│   ├── kurallar.py      parçaların uyması gereken kurallar
│   └── __main__.py      başlangıç dosyası: parçaları kurar ve çalıştırır
│
├── sozlesme/           DİĞER GRUPLARLA ORTAK SÖZLÜK: onlara verdiğimiz verinin biçimi
│   ├── kayitlar.py      Olcum, Atim, Olay gibi kayıt tipleri (CSV sütunları bunlar)
│   └── kurallar.py      "kayıt alan her program al() ve kapat() metotlarına sahip olmalı" kuralı
│
├── tests/              OTOMATİK KONTROLLER: her parça doğru çalışıyor mu?
│   └── test_*.py        her dosyanın adı, hangi parçayı denetlediğini söyler
│
├── README.md           bu belge
├── requirements.txt    okuyucunun ihtiyaç duyduğu dış kütüphane (pyserial)
├── kayitlar/           okuyucunun yazdığı test kayıtları (git'e girmez)
└── .venv/              bu klasöre ait Python ortamı (git'e girmez)
```

**Bağımlılık kuralı:** Alt katman klasörleri birbirini içe aktarmaz. Yalnızca `okuyucu/kurallar.py`, `okuyucu/mesajlar.py` ve `sozlesme/` kullanılır. Hepsini bilen tek yer `okuyucu/__main__.py` dosyasıdır. Bu sayede bir alt katmanı değiştirmek, diğerlerini bozmaz.

Aynı harita kodun içinde de var. Her `.py` dosyasının en üstünde üç bölümlük tek bir açıklama bulunur:

```python
# OKUYUCU: Veri hattının asıl işi. ...                    (dosyanın bulunduğu katmanın görevi)
#
# BU DOSYA (okuyucu/ayristirma/protokol_v1.py): ...       (yukarıdaki haritadaki kısa cümle)
#
# AYRINTI: ...                                            (biraz daha ayrıntı)
```

Kodun içinde bunun dışında yorum yoktur. Klasörlerin `__init__.py` dosyalarında aynı biçimde "BU KLASÖR" yazar.

### Kurulum (bir kez)

Gereksinim: Python 3.10 ya da daha yenisi. Sahte ESP32 ve testler ek kütüphane kullanmaz; okuyucu `pyserial` kullanır. `pyserial`, bilgisayarın genel Python'una değil bu klasöre ait bir ortama (`.venv`) kurulur. Komutlar `veri_hatti` klasöründen çalıştırılır:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip install -r requirements.txt
```

### Çalıştırma

İki terminal açın:

```
python3 -m simulator              # 1. terminal: sahte ESP32, 127.0.0.1:7600 kapısını açar
.venv/bin/python -m okuyucu       # 2. terminal: okuyucu, sahte ESP32'ye bağlanır
```

Okuyucu ekrana saniyede bir özet basar ve kayıtları `kayitlar/<tarih_saat>/` klasörüne yazar. Ctrl+C ile durdurulur:

```
Bağlandı: socket://127.0.0.1:7600
Kayıt klasörü: kayitlar/2026-10-18_17-17-34  (durdurmak için Ctrl+C)
[olay] baglanti: okuma başladı
[cihaz] protokol v1, 50 Hz, ±2 g, ±250 °/s
17:17:35  ölçüm  50  atım 1  GSR 1503 mV  ivme z +0.995 g
17:17:36  ölçüm  50  atım 1  GSR 1502 mV  ivme z +0.991 g
```

Gerçek ESP32 gelince yalnızca adres değişir:

```
.venv/bin/python -m okuyucu --adres /dev/cu.usbserial-0001    # macOS (ls /dev/cu.* ile bulunur)
.venv\Scripts\python -m okuyucu --adres COM3                  # Windows (Aygıt Yöneticisi'nde görünür)
.venv/bin/python -m okuyucu --help                            # bütün ayarlar
```

Diğer komutlar:

```
python3 -m simulator --help       # sahte ESP32'nin ayarları (nabız, nefes, kapı ...)
nc 127.0.0.1 7600                 # sahte ESP32'nin gönderdiği ham satırları gözle görmek için
.venv/bin/python -m unittest -v   # bütün testler (pyserial olmadan çalıştırılırsa uçtan uca test atlanır)
```

## 8. Elektrikçilere notlar (öneri)

- GSR'yi ESP32'nin ADC1 pinlerinden birine bağlayın. ADC2 pinleri Wi-Fi ile paylaşılıyor.
- Grove modüllerini 3,3 V ile besleyin; 5 V ile beslenirse çıkışları ESP32'nin girişine fazla gelebilir. Nabız sensörü 3,0–5,25 V aralığında, GSR sensörü 3,3 V ya da 5 V ile çalışır.
- MPU6050 ile ekran aynı I2C hattını kullanır. Adresleri genellikle MPU6050 için `0x68`, ekran için `0x3C`'dir.
- Nabız sensörünün çıkışı, kesme (interrupt) destekleyen bir dijital pine bağlanmalı.

## 9. Adımlar

1. Sahte ESP32 ve testleri **(bitti)**
2. `sozlesme/`: kayıt tipleri ve `VeriAlici` **(bitti)**
3. `okuyucu/mesajlar.py` ve `okuyucu/kurallar.py` **(bitti)**
4. `ayristirma/` ve testleri **(bitti)**
5. `donusturme/` ve testleri **(bitti)**
6. `dagitim/`, `baglanti/`, `hat.py` ve `__main__.py`; `pyserial` kurulumu **(bitti)**
7. Uçtan uca test: sahte ESP32 → okuyucu → CSV **(bitti)**
8. Daha sonra:
   - Ekran komutu (`D`)
   - Canlı yayın (A grubuyla birlikte)
   - `ham.log`'dan tekrar oynatma
   - Gerçek ESP32 kodu (kart gelince)

## 10. Açık konular

- ESP32 kodunu kimin yazacağı: veri hattı mı, elektrikçiler mi, birlikte mi?
- Bağlantı türü: USB öneriliyor; kesinleşmedi.
- Canlı yayının tekniği: arayüz türüne göre A grubuyla belirlenecek.
- Ham veriyi veri tabanına kimin yazacağı: veri hattı mı, B mi?
- GSR formülü ve değerin terlemeyle hangi yönde değiştiği: gerçek sensörle doğrulanacak.
- `sozlesme/` paketinin ortak depodaki yeri. Ortak depo açılana kadar `veri_hatti/` içinde başlar.
