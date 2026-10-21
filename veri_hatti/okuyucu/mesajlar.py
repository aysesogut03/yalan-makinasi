# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU DOSYA (okuyucu/mesajlar.py): ESP32'nin dili: ayrıştırmanın çıktısı, dönüştürmenin
#   girdisi.
#
# AYRINTI: Her satır türünün (I bilgi, S ölçüm, B atım, E hata) Python'daki karşılığı
#   burada tanımlıdır. Değerler ESP32'den geldiği gibidir: ham sayılar ve ESP32'nin
#   kendi saati. Yalnızca okuyucunun içinde kullanılır; diğer katmanlar bunun yerine
#   sozlesme/'yi kullanır.

from dataclasses import dataclass


@dataclass(frozen=True)
class BilgiMesaji:
    seq: int
    ms: int
    surum: int
    hz: int
    acc_g: int
    gyro_dps: int


@dataclass(frozen=True)
class OlcumMesaji:
    seq: int
    ms: int
    gsr: int
    ax: int
    ay: int
    az: int
    gx: int
    gy: int
    gz: int


@dataclass(frozen=True)
class AtimMesaji:
    seq: int
    ms: int


@dataclass(frozen=True)
class HataMesaji:
    seq: int
    ms: int
    kod: str


Mesaj = BilgiMesaji | OlcumMesaji | AtimMesaji | HataMesaji
