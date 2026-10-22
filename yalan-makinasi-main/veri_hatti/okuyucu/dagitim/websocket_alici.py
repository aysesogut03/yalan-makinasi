# OKUYUCU: Veri hattının asıl işi. ESP32 satırlarını diğer katmanların anlayacağı kayıtlara çevirir.
#
# BU DOSYA (okuyucu/dagitim/websocket_alici.py): Kayıtları canlı olarak arayüze WebSocket ile JSON biçiminde yollar.
#
# AYRINTI: VeriAlici kuralına uyar (al ve kapat). WebSocket sunucusu ayrı bir iş parçacığında çalışır,
# böylece al() beklemez ve kayıt akışı yavaşlamaz. Mesaj biçimi README 5. bölümdeki canlı akış örnekleriyle aynıdır:
# CSV sütun adları ve "tur" alanı. Olay kaydında olayın türü "olay" alanına konur.

import asyncio
import json
import threading
from dataclasses import asdict, is_dataclass

import websockets

TURLER = {"Olcum": "olcum", "Atim": "atim", "Olay": "olay", "CihazBilgisi": "cihaz"}


class WebSocketAlici:
    def __init__(self, host="127.0.0.1", port=8765):
        self._host = host
        self._port = port
        self._istemciler = set()
        self._dongu = asyncio.new_event_loop()
        self._durdur = None
        self._hata = None
        self._hazir = threading.Event()
        self._is_parcacigi = threading.Thread(target=self._calistir, daemon=True)
        self._is_parcacigi.start()
        self._hazir.wait(timeout=5)
        if self._hata:
            raise RuntimeError(f"WebSocket kapısı açılamadı ({host}:{port}): {self._hata}")

    def _calistir(self):
        asyncio.set_event_loop(self._dongu)
        try:
            self._dongu.run_until_complete(self._sunucu())
        except OSError as hata:
            self._hata = hata
            self._hazir.set()

    async def _sunucu(self):
        self._durdur = asyncio.Event()
        async with websockets.serve(self._baglanti, self._host, self._port):
            self._hazir.set()
            await self._durdur.wait()

    async def _baglanti(self, ws):
        self._istemciler.add(ws)
        try:
            await ws.wait_closed()
        finally:
            self._istemciler.discard(ws)

    def al(self, kayit):
        tur = TURLER.get(type(kayit).__name__)
        if tur is None or not self._istemciler:
            return
        veri = asdict(kayit) if is_dataclass(kayit) else dict(vars(kayit))
        alt_tur = veri.pop("tur", None)
        if tur == "olay":
            veri["olay"] = alt_tur
        mesaj = json.dumps({"tur": tur, **veri}, default=str)
        self._dongu.call_soon_threadsafe(websockets.broadcast, self._istemciler, mesaj)

    def kapat(self):
        if self._durdur is not None:
            self._dongu.call_soon_threadsafe(self._durdur.set)
        self._is_parcacigi.join(timeout=2)