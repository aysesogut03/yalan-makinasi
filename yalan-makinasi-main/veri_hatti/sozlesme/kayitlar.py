# SÖZLEŞME: Diğer gruplarla ortak sözlük. Onlara verdiğimiz verinin biçimini tanımlar;
#   diğer katmanlar bizim kodumuzdan yalnızca bu klasörü kullanır.
#
# BU DOSYA (sozlesme/kayitlar.py): Diğer gruplara verdiğimiz kayıt tipleri: Olcum, Atim,
#   Olay... (CSV sütunları bunlar).
#
# AYRINTI: Her kayıt tipinin alanları, kayitlar/ klasöründeki CSV dosyalarının
#   sütunlarıyla birebir aynıdır (README.md, 5. bölüm). Ölçümler birimlidir (mV, g, °/s)
#   ve zamanları bilgisayar saatindedir. Kayıtlar oluşturulduktan sonra değiştirilemez:
#   aynı kayıt birden çok programa gider, biri değiştirirse diğerleri etkilenmesin diye.

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Olcum:
    t: float
    seq: int
    esp_ms: int
    gsr_mv: int
    ax_g: float
    ay_g: float
    az_g: float
    gx_dps: float
    gy_dps: float
    gz_dps: float


@dataclass(frozen=True)
class Atim:
    t: float
    seq: int
    esp_ms: int


class OlayTuru(str, Enum):
    KAYIP = "kayip"
    BOZUK = "bozuk"
    HATA = "hata"
    YENIDEN_BASLAMA = "yeniden_baslama"
    BAGLANTI = "baglanti"


@dataclass(frozen=True)
class Olay:
    t: float
    tur: OlayTuru
    ayrinti: str


@dataclass(frozen=True)
class CihazBilgisi:
    t: float
    surum: int
    hz: int
    acc_g: int
    gyro_dps: int


@dataclass(frozen=True)
class HamSatir:
    t_gelis: float
    metin: str


Kayit = Olcum | Atim | Olay | CihazBilgisi | HamSatir
