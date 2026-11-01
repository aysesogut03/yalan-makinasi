# SİMÜLATÖR: Sahte ESP32. Kart gelene kadar gerçek ESP32'nin yerine veri üretir.
#
# BU DOSYA (simulator/kurallar.py): Parçaların uyması gereken kurallar (bir priz
#   standardı gibi).
#
# AYRINTI: "Her saatin simdi() ve uyu() metotları olmalı" gibi kurallar; burada çalışan
#   kod yoktur. cihaz.py parçaların kendisini değil bu kuralları tanır. Bu sayede
#   testlerde gerçek saat yerine beklemeyen bir saat, TCP yerine bir liste verilebilir.

from typing import Protocol


class Saat(Protocol):
    def simdi(self) -> float:
        ...

    def uyu(self, saniye: float) -> None:
        ...


class GsrSensoru(Protocol):
    def oku_mv(self, t: float) -> int:
        ...


class IvmeSensoru(Protocol):
    acc_araligi_g: int
    gyro_araligi_dps: int

    def oku(self, t: float) -> tuple[int, int, int, int, int, int]:
        ...


class NabizSensoru(Protocol):
    def sonraki_aralik(self) -> float:
        ...


class SatirCikisi(Protocol):
    def gonder(self, satir: str) -> None:
        ...
