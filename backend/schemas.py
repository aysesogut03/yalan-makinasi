from pydantic import BaseModel
from typing import Optional, List

# Giriş İsteği
class LoginRequest(BaseModel):
    username: str
    password: str

# Katılımcı Tanımı
class KatilimciCreate(BaseModel):
    ad_soyad: str
    yas: int
    cinsiyet: str

# Oturum Kaydı Tanımı
class OturumCreate(BaseModel):
    katilimci_id: int
    test_adi: Optional[str] = "Poligraf Biyosinyal Oturumu"
    notlar: Optional[str] = None
    ortalama_bpm: Optional[float] = 0.0
    ortalama_gsr: Optional[float] = 0.0
    yalan_skoru: Optional[float] = 0.0