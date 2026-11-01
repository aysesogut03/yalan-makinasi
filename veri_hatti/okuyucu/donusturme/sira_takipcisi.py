# OKUYUCU: Veri hattının asıl işi. ESP32'den gelen satırları, diğer katmanların
#   anlayacağı kayıtlara çevirir ve onlara teslim eder.
#
# BU DOSYA (okuyucu/donusturme/sira_takipcisi.py): Kaybolan satır var mı, ESP32 yeniden
#   mi başladı, ona bakar.
#
# AYRINTI: ESP32 her satıra bir sıra numarası koyar (0, 1, 2, ...). Numara atlarsa arada
#   satır kaybolmuştur: 5'ten sonra 8 gelirse 6 ve 7 kayıptır. Numara geri giderse ESP32
#   yeniden başlamıştır.

class SiraTakipcisi:
    def __init__(self) -> None:
        self._son: int | None = None

    @property
    def basladi(self) -> bool:
        return self._son is not None

    @property
    def son(self) -> int | None:
        return self._son

    def geri_gitti_mi(self, seq: int) -> bool:
        return self._son is not None and seq <= self._son

    def kayip_say(self, seq: int) -> int:
        kayip = 0 if self._son is None else max(0, seq - self._son - 1)
        self._son = seq
        return kayip

    def sifirla(self) -> None:
        self._son = None
