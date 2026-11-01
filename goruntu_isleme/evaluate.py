"""Modeli BAŞKA bir oturumda/kişide bölüm bazında test eder (genelleme testi).

Kullanım:
    .venv\\Scripts\\python evaluate.py                                   # test: en yeni oturum, eğitim: diğer etiketli oturumlar
    .venv\\Scripts\\python evaluate.py --train data/a.csv --test data/b.csv

Üç sonuç verir:
  1. HAM: eğitim oturumlarında seçilen özellikler+model, test kişisine olduğu gibi uygulanır.
  2. NORMALİZE: her oturumun özellikleri, o oturumun ilk kontrol-soruları (doğru cevaplar) baz çizgisine
     göre ölçeklenir (kişiler arası yüz boyutu/mesafe/konuşma tarzı farkını azaltmak için).
  3. KENDİ İÇİNDE: test oturumunun kendi verisiyle iç içe bölüm doğrulaması (yöntem bu kişide işe yarıyor mu).
Her biri için şans olasılığı (permütasyon p) verilir. Tahmin eşiği 0.5, bölümün ortalama olasılığı kullanılır.
"""
import argparse
import csv
import glob
import itertools
import sys

import numpy as np

import train as T
from features import CALIBRATION_SECONDS, FEATURES, FLOORS


def load_file(path):
    """Döner: dict(rows=(X, y, seg), base=X_baseline). Bölüm başı T.TRIM sn atılır."""
    R = list(csv.DictReader(open(path, encoding="utf-8")))
    if not R:
        return None
    t = np.array([float(r["t"]) for r in R])
    X = np.array([[float(r[k]) for k in FEATURES] for r in R])
    lab = [r["label"] for r in R]
    base_mask = np.array([l == "baseline" for l in lab])
    if not base_mask.any():                      # eski kayıtlarda: dosyanın ilk CALIBRATION_SECONDS sn'si
        base_mask = (t - t[0]) < CALIBRATION_SECONDS
    Xl, yl, sl = [], [], []
    seg_id, prev, prev_t, seg_t0 = -1, None, None, None
    for i, l in enumerate(lab):
        if l not in ("truth", "lie"):
            prev = None
            continue
        if l != prev or (prev_t is not None and t[i] - prev_t > 3):
            seg_id += 1
            seg_t0 = t[i]
        prev, prev_t = l, t[i]
        if t[i] - seg_t0 < T.TRIM:
            continue
        Xl.append(X[i]); yl.append(1 if l == "lie" else 0); sl.append(seg_id)
    if not Xl:
        return None
    return dict(path=path, X=np.array(Xl), y=np.array(yl), seg=np.array(sl),
                base=X[base_mask] if base_mask.sum() >= 5 else None)


def normalize(s):
    """Oturumun kendi kontrol-soruları baz çizgisine göre z-skoru."""
    if s["base"] is None:
        return None
    mean, sd = s["base"].mean(0), np.maximum(s["base"].std(0), 0.5 * np.array(FLOORS))
    return dict(s, X=(s["X"] - mean) / sd)


def stack(sessions):
    X = np.vstack([s["X"] for s in sessions])
    y = np.concatenate([s["y"] for s in sessions])
    seg, off = [], 0
    for s in sessions:
        seg.append(s["seg"] + off)
        off += s["seg"].max() + 1
    return X, y, np.concatenate(seg)


def fit_pipeline(X, y, seg):
    segs = list(np.unique(seg))
    M = np.array([X[seg == s].mean(0) for s in segs])
    ys = np.array([int(y[seg == s][0]) for s in segs])
    sel, d = T.select(M, ys)
    return sel, T.fit(X[:, sel], y), d


def binom_p(k, n):
    """P(≥k doğru | n bölüm, tesadüf %50)."""
    from math import comb
    return sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n


def perm_p_fixed(probs, ytrue):
    """Tahminler sabit; test bölüm etiketlerini (sınıf sayısı korunarak) karıştır. ≥ gözlenen doğruluk oranı."""
    pred = np.array(probs) > 0.5
    n, n_lie = len(ytrue), int(sum(ytrue))
    obs = np.mean(pred == np.array(ytrue, bool))
    combos = list(itertools.combinations(range(n), n_lie))
    better = sum(np.mean(pred == np.isin(np.arange(n), c)) >= obs - 1e-9 for c in combos)
    return better / len(combos)


def report(title, train_X, train_y, train_seg, test, extra_note=""):
    sel, model, d = fit_pipeline(train_X, train_y, train_seg)
    segs = list(np.unique(test["seg"]))
    probs, ytrue = [], []
    for s in segs:
        m = test["seg"] == s
        probs.append(float(T.predict(model, test["X"][m][:, sel]).mean()))
        ytrue.append(int(test["y"][m][0]))
    hits = [(p > 0.5) == bool(y) for p, y in zip(probs, ytrue)]
    k, n = sum(hits), len(hits)
    print(f"\n=== {title} ===  (eğitimde seçilen özellikler: {', '.join(FEATURES[j] for j in sel)})")
    for i, (p, y, h) in enumerate(zip(probs, ytrue, hits), 1):
        print(f"   bölüm {i:2d}  gerçek={'YALAN' if y else 'doğru':5s}  model olasılığı={p:.2f}  "
              f"tahmin={'YALAN' if p > 0.5 else 'doğru':5s}  {'✓' if h else '✗'}")
    print(f"   -> {k}/{n} bölüm doğru (%{100 * k / n:.0f}).  Şans p: binom={binom_p(k, n):.3f}, "
          f"permütasyon={perm_p_fixed(probs, ytrue):.3f}  {extra_note}")
    return k / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", nargs="*", help="eğitim CSV'leri (varsayılan: test dışındaki etiketli oturumlar)")
    ap.add_argument("--test", help="test CSV (varsayılan: en yeni oturum)")
    a = ap.parse_args()
    files = sorted(glob.glob("data/*.csv"))
    test_path = a.test or (files[-1] if files else None)
    if not test_path:
        sys.exit("data/ içinde oturum yok.")
    train_paths = a.train if a.train else [f for f in files if f != test_path]
    test = load_file(test_path)
    train_sessions = [s for s in (load_file(p) for p in train_paths) if s is not None]
    if test is None:
        sys.exit(f"{test_path} içinde etiketli (truth/lie) bölüm yok.")
    if not train_sessions:
        sys.exit("Etiketli eğitim oturumu yok.")
    nseg = len(np.unique(test["seg"]))
    print(f"TEST: {test_path}  ({nseg} bölüm, {len(test['y'])} sn, kırpmadan sonra)")
    print(f"EĞİTİM: {', '.join(s['path'] for s in train_sessions)}")
    if nseg < 6:
        print(f"UYARI: test oturumunda sadece {nseg} bölüm var; sonuç çok belirsiz olur.")

    tX, ty, tseg = stack(train_sessions)
    if len(set(ty)) < 2:         # tek sınıfla eğitilen model anlamsız; sınıf ağırlığında sıfıra bölme olur
        sys.exit("Eğitim oturumlarında hem doğru hem yalan bölüm gerekli.")
    report("1) HAM özellikler, eğitim kişisinden test kişisine", tX, ty, tseg, test)

    ns_train = [normalize(s) for s in train_sessions]
    ns_test = normalize(test)
    if ns_test is not None and all(s is not None for s in ns_train):
        nX, ny, nseg_ = stack(ns_train)
        report("2) NORMALİZE (oturumun kendi kontrol baz çizgisine göre)", nX, ny, nseg_, ns_test)
    else:
        print("\n(2) atlandı: bir oturumda yeterli kontrol/baz çizgisi satırı yok.")

    # 3) test kişisinin kendi verisi: iç içe bölüm doğrulaması (yöntem bu kişide işe yarıyor mu)
    segs = list(np.unique(test["seg"]))
    seg_y = {s: int(test["y"][test["seg"] == s][0]) for s in segs}
    n_lie = sum(seg_y.values())
    print("\n=== 3) KENDİ İÇİNDE: test kişisinin verisiyle iç içe bölüm doğrulaması ===")
    if min(n_lie, len(segs) - n_lie) < 3:
        print("   atlandı: her sınıftan en az 3 bölüm gerekli.")
    else:
        acc = T.nested_cv(test["X"], test["seg"], seg_y, segs)
        p = T.perm_p(test["X"], test["seg"], segs, seg_y, acc, np.random.default_rng(0))
        sel, _, d = fit_pipeline(test["X"], test["y"], test["seg"])
        print(f"   -> %{acc * 100:.0f} ({int(round(acc * len(segs)))}/{len(segs)}), şans p={p:.3f}; "
              f"bu kişide en ayıran özellikler: "
              + ", ".join(f"{FEATURES[j]} d={d[j]:+.1f}" for j in np.argsort(-np.abs(d))[:3]))

    print("\nYorum için: 1) ve 2) 'kişiden kişiye geçiyor mu', 3) 'yöntem bu kişide ayırt ediyor mu' sorusunu yanıtlar.")
    print("Bölüm sayısı az olduğundan p-değerleri kaba; tek bir oturum kesin kanıt sayılmaz.")


if __name__ == "__main__":
    main()
