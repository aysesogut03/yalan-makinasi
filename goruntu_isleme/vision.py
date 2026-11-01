"""Görüntü analiz modülü: göz kırpma, bakış, baş pozu, hareket, mikro-ifade, el ve yüze dokunma.

Tüm mesafeler yüz genişliğine bölünür, böylece kameraya yakın/uzak durmak sonucu bozmaz.
"""
import json
import time
from collections import deque
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from features import (CALIB_MIN_WINDOW, CALIBRATION_SECONDS, EXPR_FULL_Z, EXPR_WEIGHTS,
                      FEATURES, FLOORS)

MODEL_PATH = Path(__file__).with_name("model.json")

# MediaPipe FaceMesh landmark indeksleri
EYE_L = [33, 160, 158, 133, 153, 144]    # p1..p6 (EAR formülü sırası)
EYE_R = [362, 385, 387, 263, 373, 380]
IRIS_A, IRIS_B = 468, 473
FINGERTIPS = [4, 8, 12, 16, 20]
# yüze dokunma bölgeleri: (ad, face-mesh indeksi)
TOUCH_POINTS = [("agiz", 13), ("burun", 1), ("goz", 159), ("goz", 386),
                ("cene", 152), ("alin", 10), ("yanak", 50), ("yanak", 280)]


def _d(a, b):
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


def _ear(p, idx):
    """Eye Aspect Ratio: göz açıklığı. Kapanınca düşer."""
    q = [p[i] for i in idx]
    return (_d(q[1], q[5]) + _d(q[2], q[4])) / (2.0 * _d(q[0], q[3]) + 1e-9)


class SpikeDetector:
    """Bir özellikteki ani ve kısa sapmaları (mikro-ifade adayı) yakalar."""

    def __init__(self, fps=30):
        self.mean = None
        self.dev = 1e-3
        self.active = False
        self.start = 0.0
        self.peak = 0.0
        self.a = 0.02

    def update(self, x, t):
        """Olay bittiyse (süre, yön) döndürür, yoksa None."""
        if self.mean is None:
            self.mean = x
            return None
        z = (x - self.mean) / max(self.dev, 2e-3)
        event = None
        if not self.active:
            if abs(z) > 4.0:
                self.active, self.start, self.peak = True, t, z
        else:
            if abs(z) > abs(self.peak):
                self.peak = z
            if abs(z) < 1.5:
                dur = t - self.start
                if 0.08 <= dur <= 0.5:          # mikro-ifade süresi (tek kare titreşimi değil)
                    event = (dur, 1 if self.peak > 0 else -1)
                self.active = False
            elif t - self.start > 0.5:         # uzun sürdü: mikro değil, normal ifade
                self.active = False
        if not self.active:                     # taban çizgisini sadece sakinken güncelle
            self.mean += self.a * (x - self.mean)
            self.dev += self.a * (abs(x - self.mean) - self.dev)
        return event


# (özellik, yön) -> etiket
LABELS = {
    ("brow", 1): "kas_kaldirma", ("brow", -1): "kas_indirme",
    ("furrow", 1): "kas_gevseme", ("furrow", -1): "kas_catma",
    ("mouth_open", 1): "agiz_acma", ("mouth_open", -1): "dudak_sikma",
    ("mouth_w", 1): "dudak_germe", ("mouth_w", -1): "dudak_buzme",
    ("smile", 1): "gulumseme", ("smile", -1): "agiz_kosesi_dusme",
}


class VisionAnalyzer:
    def __init__(self):
        self.mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True,
            min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=2, model_complexity=0,
            min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mirrored = True            # server ayarlar; sağ/sol etiketini etkiler
        self.t0 = time.time()
        self.fps = 0.0
        # yüze dokunma
        self.last = None                # (noktalar, yüz genişliği, zaman) güvenilir son yüz
        self.hand_pts = []
        self.rejected_hands = []
        self.debug_hands = False
        self.hand_streak = 0
        self.touch_now = None
        self.touch_since = None
        self.touch_counted = False
        self.touch_events = deque()     # (zaman, bölge)
        # baş hareketi (evet/hayır)
        self.head_hist = deque()
        self.head_events = deque()      # (zaman, "evet"/"hayir")
        self.last_gesture_t = 0.0
        # pencere özellikleri / skor
        self.feat_hist = deque()
        self.last_blink_ms = 150.0      # henüz kırpma ölçülmediyse tipik değer
        self.smooth = None
        self.model = self._load_model()
        # bakış / kırpma ek ölçümleri
        self.gaze_y = 0.5
        self.gy_base = None
        self.gaze_dir = "merkez"
        self.blink_durs = deque()       # (zaman, ms)
        self._last_t = None
        # göz kırpma
        self.ear_open = 0.28
        self.closed_frames = 0
        self.closed_since = 0.0
        self.blinks = deque()           # kırpma zamanları
        # bakış
        self.away = False
        self.away_since = 0.0
        self.away_events = deque()
        # hareket
        self.prev_center = None
        self.motion = 0.0
        # mikro-ifade
        self.spikes = {k: SpikeDetector() for k in
                       ("brow", "furrow", "mouth_open", "mouth_w", "smile")}
        self.micro_events = deque()     # (zaman, etiket)
        # anlık değerler
        self.face = False
        self.yaw = self.pitch = self.gaze_x = 0.0
        self.ear = 0.0
        # kalibrasyon
        self.calib_start = time.time()
        self.calib_samples = []
        self.baseline = None

    @staticmethod
    def _load_model():
        """train.py'nin ürettiği model.json varsa yükler (özellik sırası uyuşmalı)."""
        try:
            with open(MODEL_PATH, encoding="utf-8") as f:
                m = json.load(f)
            if m["features"] != FEATURES:
                print("model.json özellik listesi eski, kullanılmıyor; train.py'yi yeniden çalıştır")
                return None
            return {"mean": np.array(m["mean"]), "std": np.array(m["std"]),
                    "w": np.array(m["w"]), "b": float(m["b"])}
        except (OSError, KeyError, ValueError):
            return None

    def recalibrate(self):
        self.calib_start = time.time()
        self.calib_samples = []
        self.baseline = None

    # ------------------------------------------------------------------ kare
    def process(self, frame_bgr):
        """Bir kare işler. Yüz noktalarını (piksel) döndürür, yüz yoksa None."""
        t = time.time()
        if self._last_t:
            self.fps = 0.9 * self.fps + 0.1 / max(t - self._last_t, 1e-3)
        self._last_t = t
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        p = self._face(rgb, w, h, t)
        self._hands(rgb, w, h, t)
        return p

    def _face(self, rgb, w, h, t):
        res = self.mesh.process(rgb)
        if not res.multi_face_landmarks:
            self.face = False
            self.closed_frames = 0
            return None
        self.face = True
        lm = res.multi_face_landmarks[0].landmark
        p = np.array([(l.x * w, l.y * h) for l in lm])
        fw = _d(p[234], p[454])         # yüz genişliği (ölçek)

        self._head_gaze(p, fw, t)
        if abs(self.yaw) > 0.3 or abs(self.pitch) > 0.35:
            # Yüz cepheden değil ya da noktalar güvenilmez (el, yan dönüş):
            # sahte olay üretmemek için ölçümü atla.
            self.face = False
            self.closed_frames = 0
            self.prev_center = None
            return p
        self.last = (p, fw, t)          # sadece güvenilir yüz, dokunma tespiti bunu kullanır
        self._blink(p, t)
        self._motion(p, fw)
        self._micro(p, fw, t)
        self._gesture(t)
        return p

    def _hands(self, rgb, w, h, t):
        """Parmak uçları yüzdeki bir bölgeye yaklaştıysa 'yüze dokunma' sayılır."""
        res = self.hands.process(rgb)
        self.hand_pts = []
        self.rejected_hands = []        # filtrenin elediği adaylar (hata ayıklama için)
        touching = None
        ref = self.last if self.last and t - self.last[2] < 3.0 else None
        if res.multi_hand_landmarks:
            best = (1e9, None)
            for hl in res.multi_hand_landmarks:
                hp = np.array([(l.x * w, l.y * h) for l in hl.landmark])
                if ref is None:
                    self.rejected_hands.append(hp)
                    continue         # yüz konumu bilinmiyorsa eli doğrulayamayız
                p, fw, _ = ref
                if self._fake_hand(hp, p, fw):
                    self.rejected_hands.append(hp)
                    continue
                self.hand_pts.append(hp)
                for name, idx in TOUCH_POINTS:
                    for tip in FINGERTIPS:
                        d = _d(hp[tip], p[idx]) / fw
                        if d < best[0]:
                            best = (d, name)
            if ref is not None and best[0] < 0.3:
                touching = best[1]
        # kısa parlamalar el sayılmasın: en az 6 ardışık karede (~0.2 sn) görünmeli
        self.hand_streak = self.hand_streak + 1 if self.hand_pts else 0
        if self.hand_streak < 6:
            self.hand_pts, touching = [], None
        self.touch_now = touching
        if touching:
            if self.touch_since is None:
                self.touch_since, self.touch_counted = t, False
            if not self.touch_counted and t - self.touch_since >= 0.25:
                self.touch_events.append((t, touching))     # kısa değmeleri sayma
                self.touch_counted = True
        else:
            self.touch_since = None

    @staticmethod
    def _fake_hand(hp, p, fw):
        """Çene/sakal gibi yüz bölgelerini el sanan yanlış tespitleri eler.

        Gerçek bir el yüzle aynı mesafede en az yüz genişliği kadar büyük görünür; sahte
        tespit ise yüzün içinde kalan küçük bir noktalar kümesidir.
        """
        size = float(np.hypot(*(hp.max(0) - hp.min(0))))
        if size < 0.5 * fw:
            return True
        # Gerçek el yüze dışarıdan gelir: bilek (nokta 0) yüzün iç bölgesinin dışında kalır
        # (çene altı, yan veya üst). Dişler/gülümseme gibi yüz içi sahte tespitlerde bilek de
        # yüzün içinde çıkar.
        fx0, fx1 = sorted((p[234][0], p[454][0]))
        fy0, fy1 = sorted((p[10][1], p[152][1]))
        mx, my = 0.08 * (fx1 - fx0), 0.05 * (fy1 - fy0)
        wx, wy = hp[0]
        if fx0 + mx < wx < fx1 - mx and fy0 < wy < fy1 - my:
            return True
        cx, cy = hp.mean(axis=0)
        face_c = p[[1, 10, 152, 234, 454]].mean(axis=0)
        if np.hypot(cx - face_c[0], cy - face_c[1]) > 1.5 * fw:
            return True              # yüzden uzak el (kucakta vb.): dokunma için anlamsız
        x0, x1 = sorted((p[234][0], p[454][0]))
        y0, y1 = sorted((p[10][1], p[152][1]))
        return x0 < cx < x1 and y0 < cy < y1 and size < 0.9 * fw

    def _gesture(self, t):
        """Yaw/pitch salınımından baş sallama (hayır) ve baş onaylama (evet)."""
        hh = self.head_hist
        hh.append((t, self.yaw, self.pitch))
        while hh and t - hh[0][0] > 1.5:
            hh.popleft()
        if len(hh) < 12 or t - self.last_gesture_t < 2.0:
            return
        a = np.array([(y, pi) for _, y, pi in hh])
        for ax, name in ((0, "hayir"), (1, "evet")):
            s = a[:, ax] - a[:, ax].mean()
            crossings = int(np.sum(np.diff(np.sign(s)) != 0))
            ptp, other = np.ptp(s), np.ptp(a[:, 1 - ax])
            if ptp > 0.06 and crossings >= 3 and ptp > 1.3 * other:
                self.head_events.append((t, name))
                self.last_gesture_t = t
                return

    def _blink(self, p, t):
        self.ear = (_ear(p, EYE_L) + _ear(p, EYE_R)) / 2
        thr = 0.72 * self.ear_open
        if self.ear > thr:
            self.ear_open += 0.01 * (self.ear - self.ear_open)
            if self.closed_frames >= 2 and t - self.closed_since < 0.6:
                self.blinks.append(t)
                self.blink_durs.append((t, (t - self.closed_since) * 1000))
            self.closed_frames = 0
        else:
            if self.closed_frames == 0:
                self.closed_since = t
            self.closed_frames += 1

    def _head_gaze(self, p, fw, t):
        self.yaw = (p[1][0] - p[234][0]) / (p[454][0] - p[234][0] + 1e-9) - 0.5
        self.pitch = (p[1][1] - p[10][1]) / (p[152][1] - p[10][1] + 1e-9) - 0.5

        def ratio(iris, a, b):
            v = p[b] - p[a]
            return float(np.dot(p[iris] - p[a], v) / (np.dot(v, v) + 1e-9))

        self.gaze_x = (ratio(IRIS_A, 33, 133) + ratio(IRIS_B, 362, 263)) / 2

        def ratio_y(iris, top, bot):
            return float((p[iris][1] - p[top][1]) / (p[bot][1] - p[top][1] + 1e-9))

        self.gaze_y = (ratio_y(IRIS_A, 159, 145) + ratio_y(IRIS_B, 386, 374)) / 2
        eye_open = self.closed_frames == 0 and self.ear > 0.8 * self.ear_open
        if eye_open and abs(self.yaw) < 0.3:     # kişinin "düz bakış" seviyesini öğren
            self.gy_base = self.gaze_y if self.gy_base is None else \
                self.gy_base + 0.01 * (self.gaze_y - self.gy_base)
        dx = self.gaze_x - 0.5
        dy = self.gaze_y - (self.gy_base if self.gy_base is not None else self.gaze_y)
        if abs(dx) > 0.10:
            right = dx > 0 if self.mirrored else dx < 0
            self.gaze_dir = "sag" if right else "sol"
        elif dy < -0.12:
            self.gaze_dir = "yukari"
        elif dy > 0.12:
            self.gaze_dir = "asagi"
        else:
            self.gaze_dir = "merkez"
        away_now = abs(self.gaze_x - 0.5) > 0.14 or abs(self.yaw) > 0.15
        if away_now and not self.away:
            self.away_since = t
        if not away_now and self.away and t - self.away_since > 0.3:
            self.away_events.append(t)
        self.away = away_now

    def _motion(self, p, fw):
        c = p[[1, 10, 152, 234, 454]].mean(axis=0) / fw
        if self.prev_center is not None:
            disp = float(np.hypot(*(c - self.prev_center))) * max(self.fps, 1)
            self.motion += 0.2 * (disp - self.motion)
        self.prev_center = c

    def _micro(self, p, fw, t):
        brow = ((p[159][1] - p[105][1]) + (p[386][1] - p[334][1])) / 2 / fw
        furrow = _d(p[107], p[336]) / fw
        mouth_open = _d(p[13], p[14]) / fw
        mouth_w = _d(p[61], p[291]) / fw
        smile = ((p[13][1] + p[14][1]) / 2 - (p[61][1] + p[291][1]) / 2) / fw
        feats = dict(brow=brow, furrow=furrow, mouth_open=mouth_open,
                     mouth_w=mouth_w, smile=smile)
        for k, v in feats.items():
            ev = self.spikes[k].update(v, t)
            # Sadece üst yüz (kaş) olayı sayılır: ağız/dudak konuşurken sürekli oynar ve
            # kayıtlardaki ~4 olay/10 sn'nin büyük kısmı bu konuşma gürültüsüydü.
            if ev and k in ("brow", "furrow"):
                self.micro_events.append((t, LABELS[(k, ev[1])]))
        # sürekli değerlerin geçmişi: eğitim/skor için 10 sn'lik pencere özellikleri buradan çıkar
        self.feat_hist.append((t, self.ear, abs(self.gaze_x - 0.5), self.gaze_y,
                               self.yaw, self.pitch, brow, mouth_open, smile,
                               furrow, self.motion))

    # ------------------------------------------------------------- saniyelik
    def snapshot(self):
        """Arayüze gidecek görüntü özetini üretir (saniyede bir çağır)."""
        t = time.time()
        for dq in (self.blinks, self.away_events):
            while dq and t - dq[0] > 60:
                dq.popleft()
        for dq in (self.micro_events, self.touch_events, self.head_events,
                   self.blink_durs):
            while dq and t - dq[0][0] > 60:
                dq.popleft()

        # kırpma: 30 sn'lik pencere (15 sn'de sadece ~4 kırpma olur, çok gürültülü).
        # Yalan söylerken kırpma ARTMAK yerine azalabildiği için iki yönlü izlenir.
        span = max(5.0, min(30.0, t - self.t0))
        blink_rate = round(sum(1 for b in self.blinks if t - b <= 30) / span * 60, 1)
        gaze_away = sum(1 for a in self.away_events if t - a <= 10)
        recent = [e for e in self.micro_events if t - e[0] <= 10]
        touches = [e for e in self.touch_events if t - e[0] <= 10]
        heads = [e for e in self.head_events if t - e[0] <= 10]
        vision = {
            "face_detected": self.face,
            "blink_rate": blink_rate,
            "blink_ms": round(float(np.mean([d for _, d in self.blink_durs])))
            if self.blink_durs else None,
            "gaze_away": gaze_away,
            "gaze_dir": self.gaze_dir,
            "au_events": len(recent),
            "last_event": recent[-1][1] if recent else None,
            "face_touch": self.touch_now is not None,
            "touch_count": len(touches),
            "touch_region": self.touch_now or (touches[-1][1] if touches else None),
            "head_events": len(heads),
            "head_gesture": heads[-1][1] if heads else None,
            "motion": round(self.motion, 3),
            "head_yaw": round(self.yaw, 3),
            "head_pitch": round(self.pitch, 3),
        }
        feats, valid = self._features(t, blink_rate, gaze_away, len(recent),
                                      len(touches), len(heads))
        valid = valid and self.face
        left = CALIBRATION_SECONDS - (t - self.calib_start)
        if self.model:                  # eğitilmiş model varsa baz çizgisi modelin içinde
            calibrating = False
        else:
            calibrating = self.baseline is None
        # pencere henüz dolmamışken (ilk ~9 sn) hesaplanan özellikler baz çizgisini bozar
        if calibrating and valid and self.window_span >= CALIB_MIN_WINDOW:
            self.calib_samples.append(feats)
        if calibrating and left <= 0:
            if len(self.calib_samples) >= 5:
                a = np.array(self.calib_samples)
                self.baseline = (a.mean(axis=0), a.var(axis=0))
                calibrating = False
            else:                       # yüz görünmedi, yeniden dene
                self.recalibrate()
        score = None
        if valid and not calibrating:
            score = self._score(feats)
        if score is not None:           # ani sıçramaları yumuşat
            # model modunda saniyelik tahmin gürültülü: ~6 sn'lik yumuşatma
            a = 0.15 if self.model else 0.3
            self.smooth = score if self.smooth is None else \
                (1 - a) * self.smooth + a * score
            score = round(self.smooth, 3)
        return {
            "t": t,
            "vision": vision,
            "vision_score": score,
            "score_mode": "model" if self.model else "expression",
            "features": {k: round(float(v), 4) for k, v in zip(FEATURES, feats)},
            "features_valid": bool(valid),
            "calibrating": calibrating,
            "calibration_left": max(0, round(left)) if calibrating else 0,
            "fps": round(self.fps, 1),
        }

    def _features(self, t, blink_rate, gaze_away, n_events, n_touch, n_head):
        """FEATURES sırasıyla özellik vektörü. İkinci değer: pencere yeterince dolu mu."""
        hh = self.feat_hist
        while hh and t - hh[0][0] > 10:
            hh.popleft()
        valid = len(hh) >= 100          # ~3+ sn'lik güvenilir kare
        self.window_span = (t - hh[0][0]) if hh else 0.0
        a = np.array(hh) if hh else np.zeros((1, 11))
        # Kırpma yokken 0 yazmak kalibrasyon taban çizgisini kirletiyordu (z=3.5-6.9);
        # son bilinen değer taşınır.
        if self.blink_durs:
            self.last_blink_ms = float(np.mean([d for _, d in self.blink_durs]))
        blink_ms = self.last_blink_ms
        vec = [blink_rate, blink_ms, gaze_away, n_events, n_touch, n_head,
               a[:, 10].mean(),                              # motion
               a[:, 4].std() + a[:, 5].std(),                # head_std
               a[:, 2].mean(),                               # gaze_dev
               a[:, 3].std(),                                # gaze_y_std
               a[:, 1].mean(),                               # ear_mean
               a[:, 6].std(), a[:, 7].std(), a[:, 8].std(), a[:, 9].std()]
        return vec, valid

    def _score(self, x):
        """0..1 skor.

        Model varsa: kişiye özel eğitilmiş lojistik regresyonun "yalan olasılığı".
        Yoksa: "ifade hareketliliği": ağız (smile_std) ve kaş arası (furrow_std) oynaklığının
        kişinin kontrol-sorusu baz çizgisine göre artışı. Yalan olasılığı DEĞİLDİR; 3 kişilik
        testte yalan uydururken tutarlı artan, ama satır bazında zayıf bir ipucudur.
        """
        x = np.array(x, dtype=float)
        if self.model:
            m = self.model
            z = (x - m["mean"]) / m["std"]
            return float(1 / (1 + np.exp(-(z @ m["w"] + m["b"]))))
        # İfade hareketliliği: smile_std ve furrow_std, kişinin kontrol-sorusu baz çizgisine göre
        # z-skoru (yalnızca artış; azalma skoru düşürür). Baz çizgisi sabit tutulur: yavaş uyum
        # eklemek, değerlendirilen (statik) yöntemden farklı olurdu ve yalan bölümü boyunca
        # baz çizgisini yukarı çekerdi.
        mean, var = self.baseline
        sd = np.maximum(np.sqrt(var), np.array(FLOORS))
        z = (x - mean) / sd
        zc = sum(w * z[FEATURES.index(n)] for n, w in EXPR_WEIGHTS.items())
        return float(np.clip(zc / EXPR_FULL_Z, 0, 1))
