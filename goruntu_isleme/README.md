# Görüntü İşleme

Projenin 3. katmanı ([projenin ana README'si](../README.md)). Kameradan göz kırpma, bakış, baş hareketi, mimik ve yüze dokunma değerlerini çıkarır ve zaman damgalı JSON olarak yayınlar.

- Sorumlu: C grubu
- Durum: prototip çalışıyor (kamera → özellikler → canlı JSON); 3 kişilik kör testle ölçüldü; puanlamaya bağlanması bekliyor
- Son güncelleme: 1 Kasım 2026

> **Önemli sınır:** Bu katman yalan hükmü vermez. 3 kişilik kör testte görüntü değerleri yalanla yalnızca zayıf, kişiye bağlı bir ilişki gösterdi (6. bölüm). Skor, kişinin kendi baz çizgisine göre **ağız ve kaş hareketliliğini** söyler. Karar verme puanlamanın (5. katman) işidir.

## 1. Görev

Kamera görüntüsünü, diğer katmanların kullanabileceği zaman damgalı değerlere çevirmek.

| Görüntü işleme şunları yapar | Görüntü işleme şunları yapmaz |
|---|---|
| Yüzde 478 noktayı ve elleri izler, 15 özellik çıkarır | Sensör verisiyle birleştirmez, puanlama yapmaz: bu 5. katmanın işi |
| Her çıktıya bilgisayar saatine göre zaman damgası ekler (`t`, Unix zamanı) | "Yalan söylüyor" demez; yalnızca ölçülen davranışı bildirir |
| Kişinin kendi baz çizgisini kontrol sorularıyla çıkarır (kalibrasyon) | Veri tabanını yönetmez |
| Etiketli kayıt alıp değerlendirme araçlarını çalıştırır | Test kayıtlarını ve görüntüleri Git'e yüklemez |

## 2. Genel görünüm

```
Kamera ─► vision.py (MediaPipe) ─► features.py ─► server.py ─┬─► ws://<ip>:8000/ws   saniyede bir JSON
                                                             └─► GET /latest
```

Veri yukarı akar: bu katman, ana README'deki kuralla uyumlu olarak yalnızca çıktısını yayınlar ve kimin kullandığını bilmez. Sensörler bu katmana değil, `veri_hatti/`'na bağlanır.

## 3. Kurulum ve çalıştırma

Windows gerekir (kamera için DirectShow, panel yazı tipi için Segoe UI). Python 3.11 ile test edildi.

```powershell
cd goruntu_isleme
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python server.py --exposure -5 --gamma 2.2
```

OpenCV sürümü sabittir: pip'teki OpenCV 5.0 kamerayı indeksle açamıyor. Loş ortamda kamera 15 FPS'e düşer; `--exposure -5` pozlamayı kısıp 30 FPS verir, `--gamma 2.2` görüntüyü aydınlatır. Odayı aydınlatmak en sağlam çözümdür.

| Seçenek | Ne yapar |
|---|---|
| `--camera N`, `--port N` | kamera indeksi (0), sunucu portu (8000) |
| `--no-preview` | önizleme penceresi olmadan çalış |
| `--exposure N`, `--gamma G` | yukarıya bak |
| `--debug-hands` | el filtresinin elediği adayları gri kutuyla göster |
| `--guided`, `--pairs N` | rehberli kayıt (5. bölüm) |
| `--record` | özellikleri etiketli CSV'ye kaydet (`data/`) |

Pencere tuşları: `q` çık · `c` yeniden kalibre et · `f` tam ekran · `s` ekran görüntüsü kaydet.

## 4. Verdiği veri

Her saniye bir JSON, `ws://<ip>:8000/ws` üzerinden. Ekibin canlı akış kuralındaki gibi her mesajda `"tur"` alanı vardır (`"goruntu"`), böylece `olcum` ve `atim` mesajlarıyla karışmaz. Zaman, ana README'deki ortak saat kuralına uyar: `t` = `time.time()`.

```jsonc
{
  "tur": "goruntu",
  "t": 1792322522.96,
  "vision": {
    "face_detected": true,
    "blink_rate": 12,          // dakikadaki göz kırpma (son 30 sn)
    "blink_ms": 130,           // ortalama kırpma süresi
    "gaze_away": 0,            // son 10 sn'de bakış kaçırma sayısı
    "gaze_dir": "merkez",      // merkez | sag | sol | yukari | asagi
    "au_events": 2,            // son 10 sn'de üst yüz mikro-ifade sayısı
    "face_touch": false,       // şu an elle yüze dokunuyor mu
    "touch_region": null,      // agiz | burun | goz | cene | alin | yanak
    "head_gesture": null,      // "evet" | "hayir" | null
    "motion": 0.18,            // baş hareketi (yüz genişliği/sn)
    "head_yaw": 0.07, "head_pitch": 0.02
  },
  "vision_score": 0.31,        // 0..1; kalibrasyon bitene kadar null
  "score_mode": "expression",  // ağız ve kaş hareketliliği (baz çizgisine göre)
  "features": { "smile_std": 0.012, "furrow_std": 0.006 /* … 15 özelliğin ham değeri */ },
  "features_valid": true,      // 10 sn'lik pencere yeterince doluysa true
  "calibrating": false, "calibration_left": 0,
  "fps": 30.0
}
```

`face_detected: false` iken (yüz yok, el yüzü kapatıyor, yan dönük) ölçümler güncellenmez.

**Puanlama için not:** Özellikler 10 sn'lik pencerelerle hesaplanır ve her saniye güncellenir. "Soru sorulduktan sonraki birkaç saniye" analizi için `features` alanı ve `t` birlikte kullanılabilir. Ham kare değeri yayınlanmaz.

**Önerilen kayıt tipi (ekip onayı bekliyor):** Ana README'nin açık konuları arasında "görüntü işleme değerlerinin kayıt biçimi" var. `sozlesme/`'ye dokunmadık. Onaylanırsa sözleşmeye şuna benzer bir kayıt eklenebilir:

```python
@dataclass(frozen=True)
class GoruntuDegeri:
    t: float                  # Unix zamanı, bilgisayar saatine göre
    yuz_var: bool
    ifade_skoru: float | None # 0..1, kalibrasyon bitene kadar None
    ozellikler: dict[str, float]
```

**Eski prototipten kalanlar:** Sunucuda `POST /sensors` ve JSON'da `sensors`, `stress_score` alanları ilk prototipten kalmıştır. Ekip mimarisinde sensörler USB seri ile `veri_hatti/`'na bağlanır ve füzyonu puanlama yapar; bu alanlar kullanılmaz ve boş kalabilir.

## 5. Kalibrasyon, kayıt ve test

**Kalibrasyon (45 sn):** Kişiye basit kontrol soruları sorulur ve **doğru** cevaplar verir. Baz çizgisi sessiz oturuşla değil konuşma davranışıyla alınır, çünkü konuşmak tek başına ağız ve kaş hareketini değiştirir.

**Skor:** `0,75·z(smile_std) + 0,25·z(furrow_std)` (dudak köşesi ve kaş arası oynaklığı, kişinin kendi baz çizgisine göre). Seviyeler: Sakin (< 0,25), Artmış (< 0,5), Yüksek (≥ 0,5). Ayarlar `features.py` içinde.

**Rehberli kayıt:** `python server.py --guided` ekranın altında soru bandı gösterir, doğru/yalan etiketini zamanlamaya göre otomatik koyar ve skoru gizler (kör test). 45 sn kontrol + 12 bölüm (6 doğru, 6 yalan), yaklaşık 8 dk. Soru havuzu `guided.py` içinde; doğru/yalan ataması rastgele.

| Komut | Ne yapar |
|---|---|
| `python evaluate.py` | en yeni oturumu, diğer oturumlarla eğitilen modelle başka kişide test eder; şans olasılığı (p) verir |
| `python train.py` | etiketli kayıttan kişiye özel model eğitir; doğrulama yetersizse `model.json` yazmaz |

## 6. Sonuçlar ve sınırlar

Kör test: 3 kişi, 36 bölüm (18 doğru, 18 yalan). Skor ekranda gizliydi, sorular rastgele atandı.

| Skor ≥ 0,5 (saniye bazında) | Kişi 1 | Kişi 2 | Kişi 3 |
|---|---|---|---|
| Doğru konuşmada yanlış alarm | %0 | %22 | %3 |
| Yalan uydururken yakalama | %18 | %66 | %29 |
| Bölüm ortalamasıyla AUC | 1,00 | 0,75 | 0,83 |

- Bir kişiyle eğitilen model başkasında genellemedi (%50–67 doğruluk, şans %50).
- Tutarlı çıkan tek ipucu dudak köşesi oynaklığı (`smile_std`, d = +2,60 / +0,99 / +1,41). Göz açıklığı ve hareket kişiler arasında tutarsızdı.
- Bu ipucu yalanın kendisini değil, uydurma anlatırken daha canlı konuşmayı da ölçüyor olabilir.
- Sınırlar: 3 kişi, talimatla söylenen (kendiliğinden olmayan) yalan, tek oturum. Kesin kanıt değil.
- Kart testi (ana README) için en çok işe yarayacak değerler büyük olasılıkla göz kırpma ve baş hareketi gibi tepki ölçümleridir; bunlar henüz kart testiyle denenmedi.

## 7. Kişisel veri

Kameradan alınan ekran görüntüleri (`screenshots/`) ve deneklerin davranış kayıtları (`data/`) kişisel veridir. Ana README'nin 4. bölümündeki 6. kurala göre Git'e yüklenmez; bu klasördeki `.gitignore` ikisini de dışarıda bırakır. Başkasının kaydını paylaşmadan önce açık rızasını al.

## 8. Açık konular

- Görüntü işleme değerlerinin kayıt biçimi (4. bölümdeki öneri) ekipçe onaylanmalı.
- Puanlama, bu değerleri soru anına göre nasıl kullanacak: hangi özellikler, hangi pencere?
- Arayüz görüntü değerlerini göstermek isterse `ws://<ip>:8000/ws`'ye ayrıca bağlanmalı (`veri_hatti` akışı 8765'te).
- Otomatik test yok; `veri_hatti/tests/` gibi bir test klasörü eklenebilir.

## 9. Dosyalar

| Dosya | İçerik |
|---|---|
| `server.py` | kamera döngüsü, WebSocket/HTTP sunucusu, önizleme penceresi, kayıt |
| `vision.py` | yüz/göz/el analizi, özellik pencereleri, skor |
| `features.py` | 15 özelliğin listesi, sapma tabanları, skor ve kalibrasyon ayarları |
| `hud.py` | önizleme paneli ve rehberli kayıt bandı |
| `guided.py` | rehberli kayıt: soru havuzu, zamanlama, otomatik etiket |
| `train.py`, `evaluate.py` | kişiye özel model eğitimi ve kişiler arası test |
