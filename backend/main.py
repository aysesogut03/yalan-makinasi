import asyncio
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from schemas import LoginRequest, KatilimciCreate, OturumCreate
from auth import authenticate_user, create_access_token
from kayit_okuyucu import (
    CanliOkuyucu, canli_mi, en_guncel_oturum,
    oturum_klasorleri, oturum_meta, oturum_ozeti,
)

app = FastAPI(title="Yalan Makinesi REST API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OTURUM_DOSYASI = Path(__file__).resolve().parent / "oturumlar.json"

# Katılımcı veritabanı (Memory)
KATILIMCILAR_DB = [
    {"id": 1, "ad_soyad": "Ahmet Yılmaz", "yas": 25, "cinsiyet": "Erkek", "test_sayisi": 1},
    {"id": 2, "ad_soyad": "Ayşe Kaya", "yas": 30, "cinsiyet": "Kadın", "test_sayisi": 1}
]


class OturumBitis(BaseModel):
    ortalama_bpm: float = 0.0
    ortalama_gsr: float = 0.0
    sure_sn: float = 0.0
    yalan_skoru: float = 0.0


def kayitli_oturumlar():
    try:
        with open(OTURUM_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def oturumlari_yaz(liste):
    with open(OTURUM_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=2)


# 1. Giriş Endpoint'i
@app.post("/api/login")
def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=400, detail="Kullanıcı adı veya şifre hatalı!")

    token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"username": user["username"], "full_name": user["full_name"]}
    }


# 2. Katılımcıları Listeleme
@app.get("/api/katilimcilar")
def get_katilimcilar():
    return KATILIMCILAR_DB


# 3. Yeni Katılımcı Ekleme
@app.post("/api/katilimcilar")
def create_katilimci(katilimci: KatilimciCreate):
    yeni_id = len(KATILIMCILAR_DB) + 1
    yeni_katilimci = {"id": yeni_id, **katilimci.dict(), "test_sayisi": 0}
    KATILIMCILAR_DB.append(yeni_katilimci)
    return yeni_katilimci


# 4. Oturum Geçmişini Listeleme (veri hattı kayıtları + arayüzden kaydedilenler)
@app.get("/api/oturumlar")
def get_oturumlar():
    girdiler = []
    for klasor in oturum_klasorleri():
        meta = oturum_meta(klasor)
        ozet = oturum_ozeti(klasor)
        girdiler.append((klasor.name, {
            "katilimci_id": 1,
            "test_adi": meta.get("test_adi", f"Oturum - {klasor.name}"),
            "notlar": meta.get("notlar", "Veri hattı kaydı"),
            "ortalama_bpm": ozet["ortalama_bpm"],
            "ortalama_gsr": ozet["ortalama_gsr"],
            "yalan_skoru": 45.0,
            "klasor_adi": klasor.name,
            "sure_sn": ozet["sure_sn"],
            "olcum_sayisi": ozet["olcum_sayisi"],
            "atim_sayisi": ozet["atim_sayisi"],
        }))
    for kayit in kayitli_oturumlar():
        girdiler.append((kayit.get("kaydedildi", ""), kayit))
    girdiler.sort(key=lambda g: g[0])
    return [{"id": i, **veri} for i, (_, veri) in enumerate(girdiler, start=1)]


@app.get("/api/oturumlar/{oturum_id}")
def get_oturum(oturum_id: int):
    for oturum in get_oturumlar():
        if oturum["id"] == oturum_id:
            return oturum
    raise HTTPException(status_code=404, detail="Oturum bulunamadı")


# 5. Yeni Oturum Oluşturma (oturumlar.json dosyasına kaydeder)
@app.post("/api/oturumlar")
def create_oturum(oturum: OturumCreate):
    kayit = oturum.dict()
    klasor = en_guncel_oturum()
    kayit["kayit_id"] = uuid4().hex[:12]
    kayit["klasor_adi"] = klasor.name if klasor else None
    kayit["kaydedildi"] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    liste = kayitli_oturumlar()
    liste.append(kayit)
    oturumlari_yaz(liste)
    return {"status": "success", "data": kayit}


# 5b. Ölçüm bitince sonuçları oturuma yazma
@app.put("/api/oturumlar/kayit/{kayit_id}")
def bitir_oturum(kayit_id: str, bitis: OturumBitis):
    liste = kayitli_oturumlar()
    for kayit in liste:
        if kayit.get("kayit_id") == kayit_id:
            kayit.update(bitis.dict())
            kayit["bitti"] = True
            oturumlari_yaz(liste)
            return {"status": "success", "data": kayit}
    raise HTTPException(status_code=404, detail="Oturum bulunamadı")


# 6. Canlı Veri WebSocket Akışı
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Yalnızca şu an yazılan (canlı) kayıt gönderilir; eski kayıt canlıymış gibi oynatılmaz.
    # Okuyucu yeniden başlatılıp yeni bir kayıt klasörü açarsa ona geçilir.
    klasor, okuyucu = None, None
    try:
        while True:
            guncel = en_guncel_oturum()
            if guncel is None or not canli_mi(guncel):
                klasor, okuyucu = None, None
                await websocket.send_json({"durum": "veri_yok"})
            else:
                if guncel != klasor:
                    klasor, okuyucu = guncel, CanliOkuyucu(guncel)
                okuyucu.ilerle()
                nokta = okuyucu.nokta()
                await websocket.send_json(nokta or {"durum": "hesaplaniyor"})
            await asyncio.sleep(1)
    except (WebSocketDisconnect, RuntimeError):
        print("İstemci canlı veri yayınından ayrıldı.")


# 7. Teşhis
@app.get("/api/debug")
def debug():
    klasor = en_guncel_oturum()
    if klasor is None:
        return {"klasor": None}
    return {"klasor": klasor.name, "canli": canli_mi(klasor), **oturum_ozeti(klasor)}