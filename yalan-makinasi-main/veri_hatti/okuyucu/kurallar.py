# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU DOSYA (okuyucu/kurallar.py): Alt katmanların uyması gereken kurallar (bir priz
#   standardı gibi).
#
# AYRINTI: "Bağlantı satırları vermeli, ayrıştırıcı satırı mesaja çevirmeli..." gibi
#   kurallar; burada çalışan kod yoktur. Bant (hat.py) alt katmanları yalnızca bu
#   kurallar üzerinden tanır, bu yüzden kurala uyan her parça takılabilir: gerçek seri
#   port da, testteki bir satır listesi de.

from collections.abc import Iterator
from typing import Protocol

from sozlesme import Kayit

from .mesajlar import Mesaj


class Saat(Protocol):
    def simdi(self) -> float:
        ...


class SatirKaynagi(Protocol):
    def satirlar(self) -> Iterator[str]:
        ...

    def kapat(self) -> None:
        ...


class BozukSatir(Exception):
    pass


class Ayristirici(Protocol):
    def ayristir(self, satir: str) -> Mesaj:
        ...


class Donusturucu(Protocol):
    def donustur(self, mesaj: Mesaj, t_gelis: float) -> list[Kayit]:
        ...
