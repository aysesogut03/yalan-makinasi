"""Özellik listesi: vision.py (canlı skor), server.py (kayıt) ve train.py (eğitim) ortak kullanır."""

# (ad, açıklama, sapma için alt sınır)
# Alt sınırlar, ~460 sn'lik etiketsiz kayıtta gözlenen genel değişkenliğin (sd) yaklaşık %60'ı.
# Amaç: kalibrasyon penceresi kısa/durağan olduğunda sd'yi olduğundan küçük sanıp
# sıradan dalgalanmayı "sapma" saymamak; ama gaze_dev gibi özellikleri de bastırmamak.
FEATURE_SPECS = [
    ("blink_rate", "göz kırpma /dk (30 sn)", 4.0),
    ("blink_ms", "ortalama kırpma süresi ms", 40.0),
    ("gaze_away", "bakış kaçırma sayısı (10 sn)", 1.0),
    ("au_events", "üst yüz mikro-ifade sayısı (10 sn)", 1.0),
    ("touch_count", "yüze dokunma sayısı (10 sn)", 1.0),
    ("head_events", "evet/hayır baş hareketi (10 sn)", 1.0),
    ("motion_mean", "ortalama baş/yüz hareketi (10 sn)", 0.05),
    ("head_std", "baş yaw+pitch oynaklığı (10 sn)", 0.012),
    ("gaze_dev", "bakışın merkezden ortalama sapması (10 sn)", 0.007),
    ("gaze_y_std", "dikey bakış oynaklığı (10 sn)", 0.015),
    ("ear_mean", "ortalama göz açıklığı (10 sn)", 0.012),
    ("brow_std", "kaş hareketi oynaklığı (10 sn)", 0.0035),
    ("mouth_std", "ağız açıklığı oynaklığı (10 sn)", 0.008),
    ("smile_std", "gülümseme/dudak köşesi oynaklığı (10 sn)", 0.005),
    ("furrow_std", "kaş arası (çatma) oynaklığı (10 sn)", 0.003),
]
FEATURES = [f[0] for f in FEATURE_SPECS]
FLOORS = [f[2] for f in FEATURE_SPECS]

# Kalibrasyon: kontrol soruları. Kişi DOĞRU cevaplar verir ve konuşur; yalanı da konuşarak
# söyleyeceği için baz çizgisi sessiz oturuşla değil, doğru konuşma davranışıyla alınmalı
# (konuşmak tek başına ağız/kaş/baş/göz davranışını değiştirir).
CALIBRATION_SECONDS = 45

# --- "ifade hareketliliği" skoru (model yokken) ---
# 3 kişilik etiketli kayıtta (kör test, 36 bölüm) yalan uydururken tutarlı olarak yükselen
# özellikler: smile_std (d=+2.6/+0.99/+1.41) ve furrow_std (+1.62/+0.64/+0.83). Ağırlıklar,
# 2 kişiden seçilip 3.'de test edildi (leave-one-person-out); her turda aynı çıktı.
# Diğer özellikler (göz açıklığı, hareket, kırpma, baş oynaklığı) kişiler arasında tutarsızdı.
# Bu bir "yalan olasılığı" değil, kişinin kendi kontrol-sorusu baz çizgisine göre ağız/kaş
# hareketliliğidir. Satır bazında zayıf: z≥1'de doğru konuşmada ~%10 yanlış alarm (kişi 2: %22),
# yalanda ~%43 yakalama.
EXPR_WEIGHTS = {"smile_std": 0.75, "furrow_std": 0.25}
EXPR_FULL_Z = 2.0         # birleşik z bu değerde skor 1.0 (z=1 → 0.5: "Yüksek" eşiği)
CALIB_MIN_WINDOW = 9.0    # kalibrasyon örneği için 10 sn'lik pencerenin en az bu kadarı dolu olmalı
