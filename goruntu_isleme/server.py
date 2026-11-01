"""Kamerayı çalıştırır, her saniye JSON yayınlar.

Arayüz için:
  WebSocket  ws://localhost:8000/ws        -> saniyede bir JSON
  GET        http://localhost:8000/latest   -> son JSON
  POST       http://localhost:8000/calibrate -> kalibrasyonu yeniden başlat
ESP32 için:
  POST       http://<pc-ip>:8000/sensors    body: {"bpm":78,"gsr":4.2,"resp_rate":15}

Çalıştır: python server.py            (önizleme penceresi: q ile çık, c ile kalibre et)
          python server.py --no-preview
"""
import argparse
import asyncio
import csv
import json
import math
import os
import threading
import time

import cv2
import mediapipe as mp
import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from guided import Guided
from hud import draw_banner, draw_panel
from features import FEATURES
from vision import FINGERTIPS, VisionAnalyzer

app = FastAPI(title="Yalan Makinesi - Görüntü Modülü")
# Yalnızca yerel sayfalar (arayüz geliştirme sunucusu dahil) HTTP ile okuyabilir.
app.add_middleware(CORSMiddleware, allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
                   allow_methods=["*"], allow_headers=["*"])

analyzer = VisionAnalyzer()
latest = {"status": "starting"}
rec = {"on": False, "label": ""}       # kayıt modu durumu
blind = {"on": False}                   # rehberli kayıtta skor gizlenir (kör test)
recal = {"req": False}                  # /calibrate isteği; kamera döngüsü kendi iş parçacığında uygular
sensors = {"t": 0.0, "bpm": None, "gsr": None, "resp_rate": None}
SENSOR_TIMEOUT = 5.0     # sn; bu kadar süre veri gelmezse null yap


class SensorData(BaseModel):
    bpm: float | None = None
    gsr: float | None = None
    resp_rate: float | None = None


@app.post("/sensors")
def post_sensors(d: SensorData):
    # NaN/inf kabul edilmez: JSON'a "NaN" olarak yazılıp arayüzde JSON.parse'ı bozardı.
    # (Kontrol burada: pydantic'in allow_inf_nan=False hatası, yanıt gövdesine NaN koymaya çalışıp 500 veriyordu.)
    if any(v is not None and not math.isfinite(v) for v in (d.bpm, d.gsr, d.resp_rate)):
        raise HTTPException(status_code=422, detail="bpm, gsr ve resp_rate sonlu sayı olmalı")
    sensors.update(t=time.time(), bpm=d.bpm, gsr=d.gsr, resp_rate=d.resp_rate)
    return {"ok": True}


@app.get("/latest")
def get_latest():
    return latest


@app.post("/label")
def set_label(value: str = ""):
    """Kayıt modunda etiketi arayüzden de değiştirmek için: truth | lie | (boş)."""
    if value not in ("truth", "lie", ""):
        return {"ok": False, "error": "value: truth | lie | boş olmalı"}
    rec["label"] = value
    return {"ok": True, "label": value}


@app.post("/calibrate")
def calibrate():
    # analyzer'a bu (HTTP) iş parçacığından dokunma: kamera döngüsü snapshot()/_score() ortasındayken
    # baseline None olursa TypeError ile döngü ölürdü. Bayrak bırak, döngü uygulasın.
    recal["req"] = True
    return {"ok": True}


@app.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()
    try:
        while True:
            await sock.send_text(json.dumps(latest))
            await asyncio.sleep(1)
    except (WebSocketDisconnect, RuntimeError):
        pass


def build_message(snap):
    fresh = time.time() - sensors["t"] < SENSOR_TIMEOUT
    snap["sensors"] = {k: (sensors[k] if fresh else None)
                       for k in ("bpm", "gsr", "resp_rate")}
    # Füzyon arkadaşlarla birlikte yapılacak; şimdilik sadece görüntü skoru.
    snap["stress_score"] = snap["vision_score"]
    snap["tur"] = "goruntu"      # ekibin canlı akış kuralı: her mesajda "tur" alanı (olcum, atim, ...)
    snap["record"] = rec["label"] if rec["on"] else None   # None: kayıt kapalı
    snap["blind"] = blind["on"]                            # True: rehberli kayıtta skor gizli
    if blind["on"]:
        snap["vision_score"] = snap["stress_score"] = None
        snap["calibrating"] = False
    return snap


FACE = mp.solutions.face_mesh
CONTOURS = list(FACE.FACEMESH_CONTOURS)    # yüz çevresi, kaşlar, gözler, dudaklar
IRISES = list(FACE.FACEMESH_IRISES)
HAND_CONNECTIONS = list(mp.solutions.hands.HAND_CONNECTIONS)
WIN = "Yalan Makinesi - Goruntu"


def render(frame, pts, snap, cw, ch, banner=None):
    """Kareyi pencere boyutuna (cw x ch) büyütür ve çizimleri büyütülmüş görüntüye yapar.

    Çizim analiz çözünürlüğünde (640x480) yapılıp sonra büyütülseydi panel ve yazılar
    bulanıklaşır ve ekranla birlikte devasa olurdu. Burada noktalar ölçeklenir, panel ise
    sınırlı bir ölçekle son çözünürlükte çizilir.
    """
    h, w = frame.shape[:2]
    s = min(cw / w, ch / h)                      # video ölçeği (4:3 oranı korunur)
    dw, dh = int(w * s), int(h * s)
    disp = cv2.resize(frame, (dw, dh),
                      interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    th = 1 if s < 2 else 2                       # çizgi kalınlığı
    if pts is not None:
        xy = (pts * s).astype(int)
        for x, y in xy:                                  # 478 noktanın hepsi
            cv2.circle(disp, (x, y), th, (0, 200, 0), -1)
        for a, b in CONTOURS:
            cv2.line(disp, tuple(xy[a]), tuple(xy[b]), (255, 200, 0), th)
        for a, b in IRISES:
            cv2.line(disp, tuple(xy[a]), tuple(xy[b]), (0, 0, 255), th)
    if analyzer.debug_hands:                     # elenen adaylar: gri kutu + "elendi"
        for hp in analyzer.rejected_hands:
            hxy = (hp * s).astype(int)
            x0, y0 = hxy.min(0)
            x1, y1 = hxy.max(0)
            cv2.rectangle(disp, (x0, y0), (x1, y1), (160, 160, 160), 1)
            cv2.putText(disp, "elendi", (x0, max(12, y0 - 5)), cv2.FONT_HERSHEY_SIMPLEX,
                        0.45, (160, 160, 160), 1)
    color = (80, 80, 255) if snap["vision"]["face_touch"] else (255, 0, 255)  # BGR
    for hp in analyzer.hand_pts:
        hxy = (hp * s).astype(int)
        for a, b in HAND_CONNECTIONS:
            cv2.line(disp, tuple(hxy[a]), tuple(hxy[b]), color, th)
        for tip in FINGERTIPS:
            cv2.circle(disp, tuple(hxy[tip]), 3 + th, color, -1)
    canvas = np.zeros((ch, cw, 3), np.uint8)     # pencereye ortala, 1:1 göster
    ox, oy = (cw - dw) // 2, (ch - dh) // 2
    canvas[oy:oy + dh, ox:ox + dw] = disp
    ui = min(max(dh / 720, 1.0), 1.4)            # panel ölçeği: büyür ama sınırlı
    draw_panel(canvas, snap, scale=ui, x0=ox + 12 * ui, y0=oy + 12 * ui)
    if banner:
        draw_banner(canvas, banner, ui, ox, oy + dh, dw)
    return canvas


def main():
    global latest
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", type=int, default=0)
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1",
                    help="dinlenen adres (varsayılan: yalnızca bu bilgisayar; ağdan erişim için 0.0.0.0)")
    ap.add_argument("--no-preview", action="store_true")
    ap.add_argument("--exposure", type=float, default=None,
                    help="manuel pozlama (örn -5). Kısa pozlama = 30 FPS ama karanlık görüntü")
    ap.add_argument("--gamma", type=float, default=1.0,
                    help="yazılımla aydınlatma (örn 2.2), kısa pozlamayı telafi eder")
    ap.add_argument("--no-mirror", action="store_true",
                    help="görüntüyü aynalama (varsayılan: aynalı, selfie gibi)")
    ap.add_argument("--record", action="store_true",
                    help="özellikleri etiketli CSV'ye kaydet (t=doğru, l=yalan, n=etiketsiz)")
    ap.add_argument("--debug-hands", action="store_true",
                    help="el filtresinin elediği adayları gri kutuyla göster")
    ap.add_argument("--guided", action="store_true",
                    help="rehberli kayıt: ekranda talimat verir, etiketi otomatik koyar")
    ap.add_argument("--pairs", type=int, default=6,
                    help="rehberli kayıtta doğru/yalan bölüm çifti sayısı (en az 3; varsayılan 6)")
    args = ap.parse_args()
    args.record = args.record or args.guided
    guided = Guided(pairs=args.pairs) if args.guided else None
    banner = None
    analyzer.debug_hands = args.debug_hands
    rec["on"] = args.record
    analyzer.mirrored = not args.no_mirror
    lut = None
    if args.gamma != 1.0:
        lut = np.array([255 * (i / 255) ** (1 / args.gamma) for i in range(256)],
                       np.uint8)

    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port,
                                           log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()

    cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise SystemExit("Kamera açılamadı")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    if args.exposure is not None:
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)    # DirectShow: 0.25 = manuel
        cap.set(cv2.CAP_PROP_EXPOSURE, args.exposure)
    print(f"Sunucu: http://localhost:{args.port}  (ws://localhost:{args.port}/ws)")

    writer = csv_file = None
    if args.record:
        os.makedirs("data", exist_ok=True)
        path = os.path.join("data", time.strftime("session_%Y%m%d_%H%M%S.csv"))
        csv_file = open(path, "w", newline="", encoding="utf-8")
        writer = csv.writer(csv_file)
        writer.writerow(["t", "label", "mode"] + FEATURES)
        csv_file.flush()
        print(f"Kayıt: {path}   t=doğru  l=yalan  n=etiketsiz")
    fullscreen = False
    shot_req, flash_until = False, 0.0
    if not args.no_preview:
        # WINDOW_NORMAL: yeniden boyutlandırılabilir; KEEPRATIO: 4:3 oranı bozulmaz
        cv2.namedWindow(WIN, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow(WIN, 960, 720)
    last_snap = 0.0
    snap = None
    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.01)             # kamera kesilirse işlemciyi kilitleme
            continue
        if not args.no_mirror:
            frame = cv2.flip(frame, 1)
        if lut is not None:
            frame = cv2.LUT(frame, lut)
        if recal["req"]:
            recal["req"] = False
            analyzer.recalibrate()
        pts = analyzer.process(frame)
        if guided:                               # etiketi zamanlama belirler
            banner = guided.state(time.time())
            rec["label"] = banner["label"]
            blind["on"] = True
        if time.time() - last_snap >= 1.0:
            snap = build_message(analyzer.snapshot())
            latest = snap
            last_snap = time.time()
            if writer and snap["features_valid"]:
                writer.writerow([f"{snap['t']:.2f}", rec["label"], snap["score_mode"]]
                                + [snap["features"][k] for k in FEATURES])
                csv_file.flush()
        if not args.no_preview:
            if snap:
                _, _, cw, ch = cv2.getWindowImageRect(WIN)
                if cw < 320 or ch < 240:         # pencere henüz hazır değil / küçültülmüş
                    cw, ch = 960, 720
                frame = render(frame, pts, snap, cw, ch, banner)
            if shot_req:                         # 's' ile istenen fotoğraf: görünen hali kaydet
                os.makedirs("screenshots", exist_ok=True)
                shot = os.path.join("screenshots", time.strftime("foto_%Y%m%d_%H%M%S.png"))
                cv2.imwrite(shot, frame)
                print("Fotoğraf kaydedildi:", shot)
                shot_req, flash_until = False, time.time() + 1.5
            if time.time() < flash_until:        # kaydedildi bildirimi (fotoğrafa girmez)
                cv2.putText(frame, "FOTO KAYDEDILDI", (24, frame.shape[0] - 24),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (80, 220, 120), 2)
            cv2.imshow(WIN, frame)
            k = cv2.waitKey(1) & 0xFF
            if k == ord("q"):
                break
            if k == ord("s"):
                shot_req = True
            if k == ord("c"):
                analyzer.recalibrate()
            if args.record and k in (ord("t"), ord("l"), ord("n")):
                rec["label"] = {ord("t"): "truth", ord("l"): "lie", ord("n"): ""}[k]
            if k == ord("f") or (k == 27 and fullscreen):    # f: tam ekran aç/kapa, Esc: kapa
                fullscreen = not fullscreen
                cv2.setWindowProperty(
                    WIN, cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL)
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
