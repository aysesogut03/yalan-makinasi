"""Etiketli kayıtlardan (data/*.csv) kişiye özel model eğitir ve model.json yazar.

Kullanım:
    .venv\\Scripts\\python train.py            # data/*.csv hepsini kullanır
    .venv\\Scripts\\python train.py --force    # doğrulama zayıf olsa da modeli kaydet

Yöntem (az veriyle fazla uyumu önlemek için bilerek basit):
  * Bölümlerin ilk TRIM saniyesi atılır: özellikler 10 sn'lik pencere olduğundan o satırlar
    önceki bölümün davranışını da içerir (yanlış etiketli sayılır).
  * Özellik seçimi BÖLÜM ortalamaları üzerinden yapılır (yan yana saniyeler birbirine çok benzediği
    için satır bazında etki büyüklüğü şişer) ve sadece en ayıran K özellik kullanılır.
  * Doğrulama iç içedir (nested leave-one-segment-out): dışarıda bırakılan bölümü, KALAN bölümlerden
    özellik seçip model kurarak tahmin eder. Özellik seçimi doğrulamanın içindedir; yoksa
    "en iyi özelliği sonradan seçmek" sonucu şişirir.
  * Şans olasılığı (permütasyon p-değeri): bölüm etiketlerinin olası dağılımlarının kaçı, aynı
    işlemle en az bu kadar iyi sonuç verir.
Model, doğruluk ve p-değeri birlikte yeterli değilse KAYDEDİLMEZ.
"""
import csv
import glob
import itertools
import json
import sys

import numpy as np

from features import FEATURES, FEATURE_SPECS

TRIM = 8                # sn: her bölümün başından atılır (pencere kirlenmesi)
K = 2                   # kullanılacak özellik sayısı
MIN_SEGMENTS = 3        # her sınıf için en az bu kadar ayrı bölüm (6+ önerilir)
MIN_ROWS = 30           # her sınıf için (kırpmadan sonra) en az bu kadar saniyelik örnek
ACCEPT_ACC = 0.75       # iç içe bölüm doğruluğu bunun altındaysa kaydedilmez
ACCEPT_P = 0.10         # şans p-değeri bunun üstündeyse kaydedilmez
MAX_PERMS = 2000        # permütasyon sayısı üst sınırı (az bölümde hepsi denenir)
DRIFT_WARN = 0.4        # seçilen özellik zamanla bu kadar kayıyorsa uyar


def load():
    """Satırları ve bölümleri okur. Döner: X, y, seg (bölüm no), t_file (dosya başından sn)."""
    X, y, seg, tf = [], [], [], []
    seg_id = -1
    for path in sorted(glob.glob("data/*.csv")):
        prev_label, prev_t, seg_t0, t_first = None, None, None, None
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                t = float(row["t"])
                t_first = t if t_first is None else t_first
                if row["label"] not in ("truth", "lie"):
                    prev_label = None
                    continue
                if row["label"] != prev_label or (prev_t is not None and t - prev_t > 3):
                    seg_id += 1                      # yeni konuşma bölümü
                    seg_t0 = t
                prev_label, prev_t = row["label"], t
                if t - seg_t0 < TRIM:                # pencere kirlenmesi: bölüm başını at
                    continue
                X.append([float(row[k]) for k in FEATURES])
                y.append(1 if row["label"] == "lie" else 0)
                seg.append(seg_id)
                tf.append(t - t_first)
    return np.array(X), np.array(y), np.array(seg), np.array(tf)


def fit(X, y, lam=3.0):
    """L2 düzenlemeli, sınıf dengeli lojistik regresyon (Newton/IRLS). Döner: mean, std, w, b."""
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std[std < 1e-9] = 1.0                            # sabit özellik (hep 0) sorun çıkarmasın
    Z = np.hstack([(X - mean) / std, np.ones((len(X), 1))])
    n, d = Z.shape
    pos = y.sum()
    wt = np.where(y == 1, n / (2 * pos), n / (2 * (n - pos)))
    reg = lam * np.eye(d)
    reg[-1, -1] = 0                                  # sapma terimi (bias) düzenlenmez
    beta = np.zeros(d)
    for _ in range(30):
        p = 1 / (1 + np.exp(-np.clip(Z @ beta, -30, 30)))
        g = Z.T @ (wt * (p - y)) + reg @ beta
        H = (Z * (wt * p * (1 - p))[:, None]).T @ Z + reg + 1e-6 * np.eye(d)
        step = np.linalg.solve(H, g)
        beta -= step
        if np.abs(step).max() < 1e-6:
            break
    return mean, std, beta[:-1], float(beta[-1])


def predict(model, X):
    mean, std, w, b = model
    return 1 / (1 + np.exp(-np.clip(((X - mean) / std) @ w + b, -30, 30)))


def select(M, ys, k=K):
    """Bölüm ortalamaları (M) üzerinden sınıfları en çok ayıran k özelliği seçer. Döner: (idx, d)."""
    a, b = M[ys == 1], M[ys == 0]
    sd = np.sqrt((a.var(0) + b.var(0)) / 2) + 1e-12
    d = (a.mean(0) - b.mean(0)) / sd
    return np.argsort(-np.abs(d))[:k], d


def pipeline(X, seg, seg_y, segs, train_segs, test_seg):
    """Eğitim bölümlerinden özellik seç + modeli kur, test bölümünün ortalama olasılığını döndür."""
    M = np.array([X[seg == s].mean(0) for s in segs])
    tr_mask = np.isin(segs, train_segs)
    sel, _ = select(M[tr_mask], np.array([seg_y[s] for s in train_segs]))
    rows = np.isin(seg, train_segs)
    yr = np.array([seg_y[s] for s in seg[rows]])
    model = fit(X[rows][:, sel], yr)
    return float(predict(model, X[seg == test_seg][:, sel]).mean())


def nested_cv(X, seg, seg_y, segs):
    hits = []
    for h in segs:
        tr = [s for s in segs if s != h]
        if len({seg_y[s] for s in tr}) < 2:
            continue
        p = pipeline(X, seg, seg_y, segs, tr, h)
        hits.append((p > 0.5) == bool(seg_y[h]))
    return float(np.mean(hits)) if hits else float("nan")


def perm_p(X, seg, segs, seg_y, observed, rng):
    """Bölüm etiketlerini (sınıf sayısı korunarak) yeniden dağıt; ≥ gözlenen kadar iyi olanların oranı."""
    n_lie = sum(seg_y[s] for s in segs)
    combos = list(itertools.combinations(range(len(segs)), n_lie))
    if len(combos) > MAX_PERMS:
        combos = [tuple(rng.choice(len(segs), n_lie, replace=False)) for _ in range(MAX_PERMS)]
    better = 0
    for c in combos:
        sy = {s: (1 if i in c else 0) for i, s in enumerate(segs)}
        better += nested_cv(X, seg, sy, segs) >= observed - 1e-9
    return better / len(combos)


def main():
    force = "--force" in sys.argv
    X, y, seg, tf = load()
    if len(X) == 0:
        sys.exit("data/ içinde etiketli kayıt yok. Önce: python server.py --guided")
    segs = list(np.unique(seg))
    seg_y = {s: int(y[seg == s][0]) for s in segs}
    n_lie = sum(seg_y.values())
    n_truth = len(segs) - n_lie
    print(f"{len(X)} saniyelik örnek (her bölümün ilk {TRIM} sn'si atıldı) | "
          f"{n_truth} doğru bölüm ({int((y == 0).sum())} sn), {n_lie} yalan bölüm ({int((y == 1).sum())} sn)")
    if min(n_lie, n_truth) < MIN_SEGMENTS or min((y == 1).sum(), (y == 0).sum()) < MIN_ROWS:
        sys.exit(f"Yetersiz veri: her sınıftan en az {MIN_SEGMENTS} ayrı bölüm ve {MIN_ROWS} sn "
                 "(kırpmadan sonra) gerekli. Daha fazla kayıt al.")

    # --- bölüm ortalamalarına göre hangi özellik ayırıyor?
    M = np.array([X[seg == s].mean(0) for s in segs])
    ys = np.array([seg_y[s] for s in segs])
    sel, d = select(M, ys)
    print("\nÖzellik etkisi, BÖLÜM ortalamaları üzerinden (+ = yalanda yüksek, - = yalanda düşük):")
    for j in np.argsort(-np.abs(d))[:8]:
        mark = "◄ seçildi" if j in sel else ""
        print(f"  {FEATURES[j]:12s} {d[j]:+5.2f}  {FEATURE_SPECS[j][1]:48s} {mark}")

    # --- zamanla kayma kontrolü (yalan etkisiyle karışabilir)
    for j in sel:
        r = float(np.corrcoef(tf, X[:, j])[0, 1])
        if abs(r) >= DRIFT_WARN:
            print(f"  UYARI: {FEATURES[j]} oturum boyunca kayıyor (zamanla r={r:+.2f}); "
                  "etki kısmen yorgunluk/oturuş değişimi olabilir. Bölüm sırası karışık olmalı.")

    # --- iç içe bölüm bazında doğrulama + şans olasılığı
    acc = nested_cv(X, seg, seg_y, segs)
    p = perm_p(X, seg, segs, seg_y, acc, np.random.default_rng(0))
    k_ok = int(round(acc * len(segs)))
    print(f"\nİç içe doğrulama (görülmemiş bölümlerde, özellik seçimi dahil): {acc * 100:.0f}% "
          f"({k_ok}/{len(segs)} bölüm). Şans ≈ 50%.")
    print(f"Şans olasılığı (permütasyon p): {p:.3f}   (küçükse sonuç şansla açıklanamaz)")

    ok = acc >= ACCEPT_ACC and p <= ACCEPT_P
    if not ok and not force:
        print(f"\nModel KAYDEDİLMEDİ: kabul için doğruluk ≥ %{ACCEPT_ACC * 100:.0f} VE p ≤ {ACCEPT_P} gerekir.\n"
              "Daha çok bölüm kaydet (6+ çift), veya yöntem bu kişide yalanı ayırt etmiyor olabilir. "
              "Yine de kaydetmek için: python train.py --force")
        return

    # --- son model: seçilen K özellik, tüm satırlarla; diğer özelliklerin ağırlığı 0
    m_sel, s_sel, w_sel, b = fit(X[:, sel], y)
    mean, std = X.mean(axis=0), X.std(axis=0)
    std[std < 1e-9] = 1.0
    w = np.zeros(len(FEATURES))
    for i, j in enumerate(sel):
        mean[j], std[j], w[j] = m_sel[i], s_sel[i], w_sel[i]
    with open("model.json", "w", encoding="utf-8") as f:
        json.dump({"features": FEATURES, "mean": mean.tolist(), "std": std.tolist(),
                   "w": w.tolist(), "b": b, "selected": [FEATURES[j] for j in sel],
                   "nested_cv_accuracy": acc, "perm_p": p, "n_segments": len(segs)}, f, indent=1)
    print(f"\nmodel.json yazıldı (özellikler: {', '.join(FEATURES[j] for j in sel)}). "
          "Sunucuyu yeniden başlat; skor artık 'yalan olasılığı (model)'.")
    if not ok:
        print("UYARI: --force ile kaydedildi; doğrulama yetersizdi, olasılığa güvenme.")


if __name__ == "__main__":
    main()
