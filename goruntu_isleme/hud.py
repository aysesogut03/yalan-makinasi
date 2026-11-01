"""Önizleme penceresinin sol üstündeki bilgi paneli (yarı saydam, Türkçe karakter destekli)."""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from features import CALIBRATION_SECONDS

FONT = r"C:\Windows\Fonts\segoeui.ttf"
BOLD = r"C:\Windows\Fonts\segoeuib.ttf"

TEXT = (232, 236, 242)
MUTED = (140, 150, 165)
ACCENT = (56, 189, 248)
GOOD = (52, 211, 153)
WARN = (251, 191, 36)
BAD = (248, 113, 113)

EVENT_TR = {
    "kas_kaldirma": "Kaş kaldırma", "kas_indirme": "Kaş indirme",
    "kas_gevseme": "Kaş gevşeme", "kas_catma": "Kaş çatma",
    "agiz_acma": "Ağız açma", "dudak_sikma": "Dudak sıkma",
    "dudak_germe": "Dudak germe", "dudak_buzme": "Dudak büzme",
    "gulumseme": "Gülümseme", "agiz_kosesi_dusme": "Ağız köşesi düşme",
}
GAZE_TR = {"merkez": "Merkez", "sag": "Sağ", "sol": "Sol",
           "yukari": "Yukarı", "asagi": "Aşağı"}
REGION_TR = {"agiz": "Ağız", "burun": "Burun", "goz": "Göz", "cene": "Çene",
             "alin": "Alın", "yanak": "Yanak"}
HEAD_TR = {"evet": "Evet (onay)", "hayir": "Hayır (sallama)"}

X0, Y0, W = 10, 10, 292
PAD = 14
H_HEADER, H_STATUS, H_SECTION, H_ROW = 46, 76, 24, 21

_fonts = {}


def _font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        try:
            _fonts[key] = ImageFont.truetype(BOLD if bold else FONT, size)
        except OSError:
            _fonts[key] = ImageFont.load_default()
    return _fonts[key]


def _level(score, mode="expression"):
    if mode == "model":             # model olasılığı: 0.5 civarı = belirsiz
        if score < 0.4:
            return "Doğruya yakın", GOOD
        if score < 0.6:
            return "Belirsiz", WARN
        return "Yalana yakın", BAD
    # ifade hareketliliği: skor 0.5 = birleşik z 1 (doğru konuşmada ~%10 yanlış alarm, yalanda ~%43 yakalama)
    if score < 0.25:
        return "Sakin", GOOD
    if score < 0.5:
        return "Artmış", WARN
    return "Yüksek", BAD


def _rows(snap):
    """(tür, ...) satırlarını üretir; yükseklik ve çizim bunlardan hesaplanır."""
    v = snap["vision"]
    s = snap.get("sensors") or {}
    dash = "—"
    rows = [("section", "GÖRÜNTÜ")]
    rows.append(("metric", "Göz kırpma", f"{v['blink_rate']} /dk",
                 v["blink_rate"] / 40, None))
    rows.append(("metric", "Kırpma süresi",
                 f"{v['blink_ms']} ms" if v.get("blink_ms") else dash, None, None))
    rows.append(("metric", "Bakış yönü", GAZE_TR.get(v["gaze_dir"], dash), None, None))
    rows.append(("metric", "Bakış kaçırma", str(v["gaze_away"]), v["gaze_away"] / 5, None))
    rows.append(("metric", "Mikro-ifade", str(v["au_events"]), v["au_events"] / 5, None))
    rows.append(("metric", "Son ifade", EVENT_TR.get(v["last_event"], dash), None, None))
    rows.append(("metric", "Hareket", f"{v['motion']:.2f}", min(v["motion"], 1.0), None))
    if v["face_touch"]:
        rows.append(("metric", "Yüze dokunma",
                     f"● {REGION_TR.get(v['touch_region'], '')}", None, BAD))
    else:
        rows.append(("metric", "Yüze dokunma", str(v["touch_count"]),
                     v["touch_count"] / 3, None))
    rows.append(("metric", "Baş hareketi", HEAD_TR.get(v["head_gesture"], dash), None, None))
    rows.append(("section", "SENSÖRLER (ESP32)"))
    fmt = [("Nabız", "bpm", " bpm", "{:.0f}"), ("Terleme (GSR)", "gsr", "", "{:.1f}"),
           ("Nefes", "resp_rate", " /dk", "{:.0f}")]
    for label, key, unit, f in fmt:
        val = s.get(key)
        rows.append(("metric", label, f.format(val) + unit if val is not None else dash,
                     None, None if val is not None else MUTED))
    return rows


def _height(rows):
    return (H_HEADER + H_STATUS
            + sum(H_SECTION if r[0] == "section" else H_ROW for r in rows) + 8)


def draw_banner(frame, st, scale, x0, y1, width):
    """Rehberli kayıt talimat bandı: videonun alt kenarında, yarı saydam."""
    k = scale
    col = {"truth": GOOD, "lie": BAD, "done": ACCENT}.get(st["kind"], ACCENT)
    h = int(86 * k)
    y0 = int(y1 - h)
    x0, x1 = int(x0), int(x0 + width)
    roi = Image.fromarray(cv2.cvtColor(frame[y0:int(y1), x0:x1], cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", roi.size, (12, 15, 21, 215))
    d = ImageDraw.Draw(ov)
    d.rectangle((0, 0, roi.size[0], max(1, int(4 * k))), fill=col + (255,))
    d.text((16 * k, 12 * k), st["title"], font=_font(max(1, round(22 * k)), True),
           fill=col + (255,))
    d.text((16 * k, 46 * k), st["text"], font=_font(max(1, round(15 * k))),
           fill=TEXT + (255,))
    right = f"{int(st['left']) + 1} sn" if st["kind"] != "done" else ""
    if st["total"] and st["kind"] != "done":
        right = f"{st['index']}/{st['total']}   {right}" if st["index"] else right
    f = _font(max(1, round(16 * k)), True)
    d.text((roi.size[0] - 16 * k - d.textlength(right, font=f), 14 * k), right, font=f,
           fill=col + (255,))
    out = Image.alpha_composite(roi, ov).convert("RGB")
    frame[y0:int(y1), x0:x1] = cv2.cvtColor(np.array(out), cv2.COLOR_RGB2BGR)


def draw_panel(frame, snap, scale=1.0, x0=X0, y0=Y0):
    rows = _rows(snap)
    k = scale                      # tüm düzen 1x birimlerle yazılı; çizerken k ile çarpılır
    H = _height(rows)
    X0_, Y0_ = int(x0), int(y0)
    x1 = min(X0_ + int(W * k), frame.shape[1])
    y1 = min(Y0_ + int(H * k), frame.shape[0])
    roi = Image.fromarray(cv2.cvtColor(frame[Y0_:y1, X0_:x1], cv2.COLOR_BGR2RGB)).convert("RGBA")
    ov = Image.new("RGBA", roi.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle((0, 0, W * k - 1, H * k - 1), 14 * k, fill=(12, 15, 21, 205),
                        outline=(255, 255, 255, 30))

    def bar(x, y, w, frac, color, h=5):
        d.rounded_rectangle((x * k, y * k, (x + w) * k, (y + h) * k), 3 * k,
                            fill=(255, 255, 255, 28))
        if frac and frac > 0:
            d.rounded_rectangle((x * k, y * k, (x + max(h, w * min(frac, 1.0))) * k,
                                 (y + h) * k), 3 * k, fill=color + (255,))

    def text(x, y, s, size=13, color=TEXT, bold=False, right=False):
        f = _font(max(1, round(size * k)), bold)
        px = x * k
        if right:
            px -= d.textlength(s, font=f)
        d.text((px, y * k), s, font=f, fill=color + (255,))

    # --- başlık
    text(PAD, 7, "Yalan Makinesi", 16, TEXT, True)
    rec = snap.get("record")
    if rec is None:
        text(PAD, 28, "Görüntü modülü", 11, MUTED)
    else:                           # kayıt modu: etiket her zaman görünür olmalı
        name, col = {"truth": ("DOĞRU", GOOD), "lie": ("YALAN", BAD),
                     "baseline": ("KONTROL", ACCENT)}.get(
            rec, ("etiketsiz", MUTED))
        text(PAD, 28, f"● KAYIT: {name}   (t / l / n)", 11, col, True)
    fps = snap["fps"]
    chip = GOOD if fps >= 25 else WARN
    d.rounded_rectangle(((W - PAD - 62) * k, 12 * k, (W - PAD) * k, 32 * k), 10 * k,
                        fill=chip + (45,))
    d.text(((W - PAD - 31) * k, 22 * k), f"{fps:.0f} FPS",
           font=_font(max(1, round(12 * k)), True), fill=chip + (255,), anchor="mm")

    # --- durum bloğu
    y = H_HEADER
    v = snap["vision"]
    if snap.get("blind") and v["face_detected"]:
        # kör test: denek skora bakıp onu kandırmaya çalışmasın
        text(PAD, y + 6, "Kör test", 17, ACCENT, True)
        text(PAD, y + 32, "Skor kayıt sırasında gizli", 11, MUTED)
        bar(PAD, y + 58, W - 2 * PAD, 0, MUTED)
    elif not v["face_detected"]:
        text(PAD, y + 6, "Yüz algılanmadı", 17, BAD, True)
        text(PAD, y + 32, "Cepheden, kameraya bak; elin yüzü kapatmasın", 11, MUTED)
        bar(PAD, y + 58, W - 2 * PAD, 0, MUTED)
    elif snap["calibrating"]:
        done = 1 - snap["calibration_left"] / CALIBRATION_SECONDS
        text(PAD, y + 4, "KALİBRASYON", 11, MUTED, True)
        text(W - PAD, y + 3, f"{snap['calibration_left']} sn", 13, ACCENT, True, right=True)
        text(PAD, y + 24, "Kontrol soruları: DOĞRU cevapla", 14, TEXT)
        bar(PAD, y + 54, W - 2 * PAD, done, ACCENT, 7)
    elif snap["vision_score"] is None:
        text(PAD, y + 6, "Ölçüm bekleniyor…", 16, MUTED, True)
        text(PAD, y + 32, "Yüzün birkaç saniye sabit görünmeli", 11, MUTED)
        bar(PAD, y + 58, W - 2 * PAD, 0, MUTED)
    else:
        score = snap["vision_score"]
        mode = snap.get("score_mode", "expression")
        word, col = _level(score, mode)
        title = "YALAN OLASILIĞI (MODEL)" if mode == "model" else "İFADE HAREKETLİLİĞİ"
        text(PAD, y + 2, title, 11, MUTED, True)
        text(W - PAD, y + 2, word, 12, col, True, right=True)
        text(PAD, y + 14, f"%{score * 100:.0f}", 34, col, True)
        bar(PAD, y + 56, W - 2 * PAD, score, col, 7)
    y += H_STATUS

    # --- satırlar
    for r in rows:
        if r[0] == "section":
            d.line((PAD * k, (y + 8) * k, (W - PAD) * k, (y + 8) * k),
                   fill=(255, 255, 255, 25), width=max(1, round(k)))
            text(PAD, y + 11, r[1], 10, MUTED, True)
            y += H_SECTION
            continue
        _, label, value, frac, color = r
        text(PAD, y + 1, label, 12, MUTED)
        text(W - PAD, y + 1, value, 12, color or TEXT, True, right=True)
        if frac is not None:
            bar(PAD + 118, y + 9, 62, frac, ACCENT, 4)
        y += H_ROW

    out = Image.alpha_composite(roi, ov).convert("RGB")
    frame[Y0_:y1, X0_:x1] = cv2.cvtColor(np.array(out), cv2.COLOR_RGB2BGR)
